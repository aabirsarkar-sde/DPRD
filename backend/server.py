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
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# LLM Configuration
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

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
QUESTION_GENERATOR_PROMPT = """You are a Senior Product Manager with deep expertise in software architecture, UI/UX design, and product development.

Your task is to analyze the user's app idea and identify 8-10 critical ambiguities that would block development or lead to wasted AI coding credits.

Generate exactly 8 multiple-choice questions to resolve these ambiguities. Questions MUST cover ALL of these categories:

1. **auth** - Authentication & User Management (1-2 questions)
   - Login methods, session handling, user roles

2. **data_complexity** - Data Architecture & Storage (1-2 questions)
   - Schema design, relationships, data types

3. **ui_layout** - UI Layout & Navigation (1-2 questions)
   - Page structure, navigation patterns, responsive design

4. **ui_components** - UI Components & Interactions (1-2 questions)
   - Specific component choices, interaction patterns, animations

5. **features** - Core Feature Scope (1-2 questions)
   - Feature priorities, MVP vs future, specific behaviors

6. **edge_cases** - Edge Cases & Error Handling (1 question)
   - Error states, empty states, loading states

7. **integrations** - External Integrations (1 question)
   - Third-party services, APIs, notifications

For each question, provide exactly 3-4 clear, distinct options that represent different implementation approaches. Options should be specific enough that an AI coding tool can implement them directly.

Respond ONLY with valid JSON in this exact format:
{
  "questions": [
    {
      "id": "q1",
      "category": "auth",
      "question": "Your specific question here?",
      "options": [
        {"label": "Detailed option A description", "value": "option_a"},
        {"label": "Detailed option B description", "value": "option_b"},
        {"label": "Detailed option C description", "value": "option_c"}
      ]
    },
    {
      "id": "q2",
      "category": "ui_layout",
      "question": "Your question here?",
      "options": [...]
    }
    // ... continue for all 8 questions
  ]
}

IMPORTANT: Generate exactly 8 questions covering different categories. Do not include any text outside the JSON object."""

PRD_GENERATOR_PROMPT = """You are a Lead Architect with expertise in building production-ready software systems.

Using the user's original idea and their answers to clarifying questions, generate a comprehensive, developer-ready PRD (Product Requirements Document).

The PRD MUST follow this exact structure in Markdown format:

# [App Name] - Product Requirements Document

## 1. The North Star
- Clear vision statement
- Primary user problem being solved
- Success metrics

## 2. Tech Stack
- Frontend framework and libraries (be specific: e.g., "TanStack Query for server state")
- Backend/API approach
- Database choice and schema considerations
- Authentication solution (e.g., "Supabase Auth with OAuth providers")
- Deployment platform

## 3. Data Schema
- List all core entities/models
- Define key fields and relationships
- Include data types and constraints
```
[Include actual schema definitions]
```

## 4. Core Features
For EACH feature, include:
### Feature Name
- **Description**: What it does
- **User Flow**: Step-by-step interaction
- **API Endpoints**: Required backend routes
- **Edge Cases**: 
  - What happens when X fails?
  - How to handle empty states?
  - Rate limiting considerations
- **Error States**: Specific error messages and recovery flows

## 5. Implementation Plan
- Phase 1: MVP (list specific features)
- Phase 2: Enhanced (list features)
- Phase 3: Scale (list features)
- Estimated complexity for each phase

## 6. Security Considerations
- Authentication requirements
- Data privacy
- Input validation rules

---

Be extremely specific. Name actual libraries, define actual API routes, and provide implementation-ready details.
The PRD should be detailed enough that an AI coding assistant (like Cursor or Lovable) could build the app from this spec alone."""

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
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="LLM API key not configured")
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"analyze-{uuid.uuid4()}",
            system_message=QUESTION_GENERATOR_PROMPT
        ).with_model("gemini", "gemini-2.5-flash")
        
        user_message = UserMessage(
            text=f"Analyze this app idea and generate 3 clarifying questions:\n\n{request.idea}"
        )
        
        response = await chat.send_message(user_message)
        logger.info(f"LLM Response: {response}")
        
        # Parse the JSON response
        import json
        # Clean response - remove markdown code blocks if present
        clean_response = response.strip()
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
        logger.error(f"JSON parse error: {e}, Response: {response}")
        raise HTTPException(status_code=500, detail="Failed to parse LLM response")
    except Exception as e:
        logger.error(f"Error analyzing idea: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/generate-prd", response_model=GeneratePRDResponse)
async def generate_prd(request: GeneratePRDRequest):
    """Generate PRD from idea and answers"""
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="LLM API key not configured")
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"prd-{uuid.uuid4()}",
            system_message=PRD_GENERATOR_PROMPT
        ).with_model("gemini", "gemini-2.5-flash")
        
        # Format the answers for context
        answers_text = "\n".join([f"- {k}: {v}" for k, v in request.answers.items()])
        
        user_message = UserMessage(
            text=f"""Generate a comprehensive PRD for this app idea:

## Original Idea:
{request.idea}

## User's Answers to Clarifying Questions:
{answers_text}

Generate the full PRD now."""
        )
        
        response = await chat.send_message(user_message)
        logger.info(f"PRD Generated successfully")
        
        return GeneratePRDResponse(prd=response)
        
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
