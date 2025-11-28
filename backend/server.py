from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Google Gemini API Configuration
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# PRD Generator Models
class AnalyzeRequest(BaseModel):
    idea: str

class QuestionOption(BaseModel):
    label: str
    value: str

class ClarifyingQuestion(BaseModel):
    id: str
    question: str
    options: List[QuestionOption]
    category: str  # auth, data_complexity, edge_cases

class AnalyzeResponse(BaseModel):
    questions: List[ClarifyingQuestion]

class GeneratePRDRequest(BaseModel):
    idea: str
    answers: dict  # question_id -> selected_value

class GeneratePRDResponse(BaseModel):
    prd: str

# System prompts
QUESTION_GENERATOR_PROMPT = """You are a Senior Product Designer & Frontend Architect with deep expertise in design systems, UI/UX patterns, and modern frontend development.

Your task is to analyze the user's app idea and generate clarifying questions that will produce a HIGHLY POLISHED, DESIGN-SYSTEM-HEAVY PRD optimized for AI coding tools like Lovable, Cursor, or Bolt.

Generate 8-10 questions. At least 4-5 questions MUST focus on UI/UX and visual design. The PRD will be used to build production-quality frontends, so design decisions are critical.

Questions MUST cover these categories:

1. **ui_style** - Visual Style & Design Language (REQUIRED - 2 questions minimum)
   - Overall aesthetic (minimal, playful, corporate, brutalist, etc.)
   - Color scheme preferences (dark mode, light mode, specific palette)
   - Typography style (modern sans-serif, elegant serif, monospace)

2. **ui_layout** - Layout & Navigation (REQUIRED - 1-2 questions)
   - Page structure (sidebar, top nav, bottom tabs, etc.)
   - Responsive strategy (mobile-first, desktop-first)
   - Navigation patterns

3. **ui_components** - Component Design & Interactions (REQUIRED - 1-2 questions)
   - Button styles (rounded, sharp, pill, ghost)
   - Card designs and elevation
   - Animation preferences (subtle, expressive, minimal)
   - Micro-interactions

4. **auth** - Authentication (if applicable)
5. **data_complexity** - Data Architecture
6. **features** - Core Feature Scope
7. **edge_cases** - Error States & Empty States

For each question:
- Provide exactly 3 distinct, specific options
- Options should describe actual design implementations
- Be specific enough for an AI to implement without guessing

Respond ONLY with valid JSON:
{
  "questions": [
    {
      "id": "q1",
      "category": "ui_style",
      "question": "What visual style should the app have?",
      "options": [
        {"label": "Clean & Minimal - Lots of whitespace, subtle shadows, neutral colors", "value": "minimal"},
        {"label": "Bold & Vibrant - Strong colors, playful animations, rounded shapes", "value": "vibrant"},
        {"label": "Dark & Premium - Dark backgrounds, high contrast, elegant typography", "value": "dark_premium"}
      ]
    }
  ]
}

IMPORTANT: Generate 8-10 questions. At least 4-5 MUST be about UI/design. Do not include any text outside the JSON."""

PRD_GENERATOR_PROMPT = """You are a Lead Architect creating AI-optimized PRDs for coding tools like Cursor, Lovable, Bolt, or Emergent.

Your goal: Generate a DETAILED, implementation-ready PRD that an AI coding assistant can execute without asking follow-up questions.

Use the user's idea and their 8 clarifying question answers to generate a comprehensive PRD.

The PRD MUST follow this structure in Markdown:

# [App Name] - Product Requirements Document

## 1. The North Star
- **Vision**: One sentence describing what this app does
- **Target User**: Who uses this and their main pain point
- **Success Metrics**: 3 measurable KPIs

## 2. Tech Stack
Be specific with exact library names and versions:
- **Frontend**: Framework, styling, state management
- **Backend**: API framework, language
- **Database**: Type and provider
- **Auth**: Method and provider
- **Deployment**: Platform

## 3. Data Schema
Define ALL entities with TypeScript interfaces:
```typescript
interface EntityName {
  id: string;          // Primary key
  field: type;         // Description
  created_at: Date;
  updated_at: Date;
}
```
List relationships between entities.

## 4. UI/UX Specification

### Design System
- Color palette with hex codes (primary, secondary, background, text)
- Typography (font family, sizes)
- Spacing (base unit)
- Border radius values

### Page Layouts
For each page describe:
- **[Page Name]** (/route)
  - Layout structure (header, sidebar, main content)
  - Key components with positioning
  - Responsive breakpoints and behavior
  - Navigation elements

### Component Specs
For each major component:
- Visual states (default, hover, active, disabled, loading)
- Props/inputs
- User interactions

## 5. Core Features (Detailed)

### Feature 1: [Name]
**Description**: What this feature does

**User Flow**:
1. Step 1
2. Step 2
3. Step 3

**API Endpoints**:
```
POST /api/resource
GET /api/resource/:id
```

**UI Components**: List components needed

**Edge Cases**:
| Scenario | Behavior | Message |
|----------|----------|---------|
| Empty state | [action] | "[message]" |
| Error | [action] | "[message]" |
| Loading | [action] | [indicator] |

### Feature 2: [Name]
(Repeat same structure)

### Feature 3: [Name]
(Repeat same structure)

## 6. Authentication Flow
- Sign up flow (steps)
- Login flow (steps)
- Session management
- Protected routes list

## 7. Implementation Phases

### Phase 1: MVP
- [ ] Core feature 1
- [ ] Core feature 2
- [ ] Basic auth

### Phase 2: Polish
- [ ] Additional features
- [ ] UI animations
- [ ] Error handling

### Phase 3: Scale
- [ ] Advanced features
- [ ] Integrations

## 8. API Reference
List all endpoints with request/response shapes.

---

IMPORTANT:
- Be specific - name exact libraries, colors (hex), dimensions
- Include ALL edge cases and error states
- UI specs must be implementable without design files
- Target 2000-4000 words
- An AI should build this without asking questions"""

# API Routes
@api_router.get("/")
async def root():
    return {"message": "PRD Generator API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

@api_router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_idea(request: AnalyzeRequest):
    """Analyze user's idea and generate clarifying questions"""
    try:
        if not GOOGLE_API_KEY:
            raise HTTPException(status_code=500, detail="Google API key not configured")
        
        # Call Gemini API directly
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{GEMINI_API_URL}?key={GOOGLE_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": f"{QUESTION_GENERATOR_PROMPT}\n\nAnalyze this app idea and generate clarifying questions:\n\n{request.idea}"}
                            ]
                        }
                    ]
                }
            )
            response.raise_for_status()
            result = response.json()
        
        # Extract text from Gemini response
        llm_response = result["candidates"][0]["content"]["parts"][0]["text"]
        logger.info(f"LLM Response received, length: {len(llm_response)}")
        
        # Parse the JSON response
        import json
        # Clean response - remove markdown code blocks if present
        clean_response = llm_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        if clean_response.startswith("```"):
            clean_response = clean_response[3:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()
        
        data = json.loads(clean_response)
        
        questions = []
        for q in data.get("questions", []):
            questions.append(ClarifyingQuestion(
                id=q["id"],
                question=q["question"],
                options=[QuestionOption(**opt) for opt in q["options"]],
                category=q["category"]
            ))
        
        return AnalyzeResponse(questions=questions)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}, Response: {llm_response}")
        raise HTTPException(status_code=500, detail="Failed to parse LLM response")
    except Exception as e:
        logger.error(f"Error analyzing idea: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/generate-prd", response_model=GeneratePRDResponse)
async def generate_prd(request: GeneratePRDRequest):
    """Generate PRD from idea and answers"""
    try:
        if not GOOGLE_API_KEY:
            raise HTTPException(status_code=500, detail="Google API key not configured")
        
        # Format the answers for context
        answers_text = "\n".join([f"- {k}: {v}" for k, v in request.answers.items()])
        
        prompt = f"""{PRD_GENERATOR_PROMPT}

Generate a comprehensive PRD for this app idea:

## Original Idea:
{request.idea}

## User's Answers to Clarifying Questions:
{answers_text}

Generate the full PRD now."""
        
        # Call Gemini API directly
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{GEMINI_API_URL}?key={GOOGLE_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ]
                }
            )
            response.raise_for_status()
            result = response.json()
        
        # Extract text from Gemini response
        prd_response = result["candidates"][0]["content"]["parts"][0]["text"]
        logger.info(f"PRD Generated successfully, length: {len(prd_response)}")
        
        return GeneratePRDResponse(prd=prd_response)
        
    except Exception as e:
        logger.error(f"Error generating PRD: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
