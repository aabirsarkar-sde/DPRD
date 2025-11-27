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

PRD_GENERATOR_PROMPT = """You are a Lead Architect specializing in creating AI-optimized PRDs that save development time and reduce iteration cycles when used with AI coding tools like Cursor, Lovable, Bolt, or Emergent.

Your goal: Generate an EXTREMELY DETAILED, implementation-ready PRD that an AI coding assistant can execute in ONE SHOT without asking clarifying questions.

Using the user's original idea and their answers to 8 clarifying questions, generate a comprehensive PRD.

The PRD MUST follow this EXACT structure in Markdown format:

# [App Name] - Product Requirements Document

## 1. The North Star
- **Vision Statement**: One clear sentence describing what this app does
- **Target User**: Specific user persona with their pain points
- **Core Value Proposition**: Why users will choose this over alternatives
- **Success Metrics**: 3-5 measurable KPIs

## 2. Tech Stack (Be Extremely Specific)
- **Frontend Framework**: [e.g., "Next.js 14 with App Router"]
- **Styling**: [e.g., "Tailwind CSS with shadcn/ui components"]
- **State Management**: [e.g., "Zustand for client state, TanStack Query for server state"]
- **Backend/API**: [e.g., "Next.js API routes with tRPC" or "FastAPI"]
- **Database**: [e.g., "PostgreSQL via Supabase with Row Level Security"]
- **Authentication**: [e.g., "Supabase Auth with Google OAuth + Magic Links"]
- **File Storage**: [if needed, e.g., "Supabase Storage for user uploads"]
- **Deployment**: [e.g., "Vercel for frontend, Supabase for backend"]

## 3. Data Schema (Complete & Detailed)
Define ALL entities with exact field names, types, and relationships:

```typescript
// Example format - provide actual schema
interface User {
  id: string; // UUID, primary key
  email: string; // unique, required
  name: string; // required, max 100 chars
  avatar_url?: string; // optional
  created_at: Date; // auto-generated
  updated_at: Date; // auto-updated
}

// Include ALL entities with relationships noted
```

**Relationships:**
- List all foreign keys and relationship types (1:1, 1:N, N:N)
- Include junction tables for N:N relationships

## 4. UI/UX Specification (CRITICAL - Be Extremely Detailed)

### 4.1 Design System
- **Color Palette**: Primary, secondary, accent, background, text colors (include hex codes)
- **Typography**: Font family, sizes for h1-h6, body, captions
- **Spacing Scale**: Base unit and scale (4px, 8px, 16px, etc.)
- **Border Radius**: Values for buttons, cards, inputs
- **Shadows**: Elevation levels for cards, modals, dropdowns

### 4.2 Page-by-Page Layout Specification
For EACH page, describe:

#### [Page Name] (e.g., "/dashboard")
- **Layout Structure**: Header, sidebar, main content area, footer
- **Component Breakdown**:
  - Header: Logo (left), navigation links (center), user avatar dropdown (right)
  - Sidebar: 240px width, collapsible, contains [list items]
  - Main Content: Grid/flex layout with specific spacing
- **Responsive Behavior**: 
  - Desktop (>1024px): Full sidebar visible
  - Tablet (768-1024px): Sidebar collapsed to icons
  - Mobile (<768px): Bottom navigation, hamburger menu
- **Key Components on Page**: List each component with its purpose

### 4.3 Component Specifications
For EACH major component:

#### [Component Name]
- **Purpose**: What it does
- **Props/Inputs**: List all props with types
- **Visual States**: Default, hover, active, disabled, loading, error
- **Interactions**: Click behavior, animations, transitions
- **Accessibility**: ARIA labels, keyboard navigation

## 5. Core Features (Exhaustively Detailed)

### Feature 1: [Feature Name]
#### Description
[2-3 sentences explaining what this feature does]

#### User Stories
- As a [user type], I want to [action] so that [benefit]
- [Add 2-3 user stories per feature]

#### UI Components Required
- [Component 1]: [Description and behavior]
- [Component 2]: [Description and behavior]

#### User Flow (Step-by-Step)
1. User navigates to [page/component]
2. User sees [initial state]
3. User [action]
4. System [response]
5. User sees [result]

#### API Endpoints
```
POST /api/[resource]
  Request Body: { field1: type, field2: type }
  Response 200: { id: string, ...createdResource }
  Response 400: { error: "Validation error message" }
  Response 401: { error: "Unauthorized" }

GET /api/[resource]?page=1&limit=10
  Response 200: { data: Resource[], total: number, page: number }
```

#### Validation Rules
- [Field 1]: [validation rule, e.g., "required, min 3 chars, max 100 chars"]
- [Field 2]: [validation rule]

#### Edge Cases & Error Handling
| Scenario | System Behavior | User Message |
|----------|-----------------|--------------|
| Empty state | Show illustration + CTA | "No items yet. Create your first!" |
| Network error | Retry 3x, then show error | "Connection failed. Tap to retry." |
| Invalid input | Inline validation | "Email format is invalid" |
| Rate limited | Queue request | "Please wait..." |
| Unauthorized | Redirect to login | "Session expired. Please login." |

#### Loading States
- Initial load: Skeleton with exact dimensions
- Action pending: Button shows spinner, disabled state
- Background refresh: Subtle indicator, no blocking UI

### Feature 2: [Feature Name]
[Repeat the same detailed structure]

### Feature 3: [Feature Name]
[Repeat the same detailed structure]

[Continue for ALL features]

## 6. Authentication & Authorization

### Auth Flow
1. **Sign Up Flow**: Step-by-step with UI screens
2. **Login Flow**: Step-by-step with UI screens  
3. **Password Reset Flow**: Step-by-step with UI screens
4. **Session Management**: Token storage, refresh logic, logout

### Authorization Rules
| Role | Permissions |
|------|-------------|
| Guest | View public content only |
| User | CRUD own resources |
| Admin | Full access |

### Protected Routes
- List all routes requiring authentication
- Redirect behavior for unauthorized access

## 7. Implementation Plan (Phased)

### Phase 1: MVP (Week 1-2)
- [ ] Feature A - Core functionality only
- [ ] Feature B - Basic version
- [ ] Auth - Email/password only
**Deliverable**: Users can [core action]

### Phase 2: Enhanced (Week 3-4)
- [ ] Feature A - Add [enhancement]
- [ ] Feature C - New feature
- [ ] UI Polish - Animations, transitions
**Deliverable**: Production-ready core experience

### Phase 3: Scale (Week 5+)
- [ ] Feature D - Advanced feature
- [ ] Integrations - Third-party services
- [ ] Analytics - Usage tracking
**Deliverable**: Full feature set

## 8. API Reference (Complete)

List ALL endpoints with full request/response schemas:

### Authentication
```
POST /api/auth/signup
POST /api/auth/login
POST /api/auth/logout
POST /api/auth/refresh
POST /api/auth/forgot-password
POST /api/auth/reset-password
```

### [Resource Name]
```
GET    /api/resources          - List all (paginated)
GET    /api/resources/:id      - Get single
POST   /api/resources          - Create new
PATCH  /api/resources/:id      - Update existing
DELETE /api/resources/:id      - Delete
```

## 9. Security Considerations
- Input sanitization requirements
- CORS configuration
- Rate limiting rules
- Data encryption requirements

---

CRITICAL INSTRUCTIONS:
1. Be EXTREMELY specific - name exact libraries, exact colors, exact dimensions
2. Every feature must have complete edge case handling
3. UI specs must be detailed enough to implement without design files
4. API specs must include all request/response shapes
5. The PRD should be 3000-5000 words minimum
6. An AI coding tool should be able to build this app WITHOUT asking any questions"""

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
