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
from datetime import datetime, timezone, timedelta
import httpx
import json
import jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, status

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
# Fix for SSL handshake issues on some platforms
client = AsyncIOMotorClient(mongo_url, tlsAllowInvalidCertificates=True)
db = client[os.environ['DB_NAME']]

# Google Gemini API Configuration
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Auth Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-please-change-in-prod')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

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

# Auth Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

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

class SavedPRD(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Link to User
    idea: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SavedPRDCreate(BaseModel):
    idea: str
class SavedPRDCreate(BaseModel):
    idea: str
    content: str

class SavedPRDUpdateIdea(BaseModel):
    idea: str

class SavedPRDUpdateContent(BaseModel):
    content: str

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

PRD_GENERATOR_PROMPT = """You are a Senior Product Designer & Full-Stack Creative Technologist creating production-ready PRDs for Generative UI tools like Lovable, Emergent, Cursor, or Bolt.

You are an expert in "Prompt-Driven Design" - using descriptive, sensory design language that AI tools understand.

**CRITICAL:** Your superpower is bridging the gap between "Pixel Perfect UI" and "Functional Schema." You don't just describe how things look - you define the data they display and the actions they trigger.

Result: A PRD that creates a STUNNING UI that is *ready* to be wired to a backend.

---

# [App Name] - Product Requirements Document

## 1. The Visual North Star (The Vibe)

### Aesthetic Direction & Inspiration
- **Style Reference**: Describe the overall visual style (e.g., "Modern SaaS dashboard meets Notion's minimalism", "Stripe's polished corporate with Vercel's dark mode elegance", "Playful Duolingo energy with Linear's precision")
- **Inspiration Sources**: Reference 2-3 real products that capture the intended feel
- **Visual Keywords**: 5-7 adjectives (e.g., "clean, airy, confident, subtle, purposeful")

### Feeling & Atmosphere
- **First Impression**: What should users *feel* in the first 3 seconds?
- **Mood**: The emotional tone (calm & focused, energetic & motivating, premium & exclusive)
- **Personality**: If this app were a person, who would they be?

## 2. The Design Language (Visuals)

### Color Story
*Don't just list hex codes - describe WHEN and WHY to use each color.*

| Color Role | Value | Usage |
|------------|-------|-------|
| **Primary Action** | #[hex] | CTAs, key buttons, links - the "do this" color |
| **Primary Subtle** | #[hex] | Hover backgrounds, selected states, badges |
| **Surface** | #[hex] | Card backgrounds, elevated containers |
| **Background** | #[hex] | Page background, the "canvas" |
| **Border** | #[hex] | Subtle dividers, input borders (at rest) |
| **Text Primary** | #[hex] | Headlines, important labels, high contrast |
| **Text Secondary** | #[hex] | Body text, descriptions |
| **Text Muted** | #[hex] | Placeholders, timestamps, helper text |
| **Success** | #[hex] | Confirmations, completed states, positive metrics |
| **Warning** | #[hex] | Caution states, pending items |
| **Error** | #[hex] | Validation errors, destructive actions |

### Typography & Physics

**Font Pairing:**
- **Headlines**: [Font Name] - [weight] (e.g., "Inter Bold - confident, geometric")
- **Body**: [Font Name] - [weight] (e.g., "Inter Regular - readable, professional")
- **Mono/Code**: [Font Name] (e.g., "JetBrains Mono - technical contexts")

**Border Radius Philosophy:**
- **Sharp (4px)**: Tags, small badges - feels precise
- **Rounded (8px)**: Buttons, inputs - approachable but professional  
- **Soft (12-16px)**: Cards, modals - friendly containers
- **Pill (9999px)**: Avatars, status indicators - organic, modern

**Shadow & Depth:**
- **Resting State**: Barely there (0 1px 2px) - grounded, humble
- **Hover/Interactive**: Gentle lift (0 4px 12px) - "I'm clickable"
- **Elevated/Modal**: Prominent (0 12px 24px) - commands attention

**Motion Personality:**
- **Speed**: Fast (150ms) for micro-interactions, Medium (250ms) for transitions
- **Easing**: Ease-out for entrances (things arriving), ease-in-out for transforms
- **Character**: Subtle and purposeful, never distracting

## 3. Component Visual Narratives & Data Binding

*For each component, describe the LOOK, the DATA it displays, and the ACTIONS it triggers.*

### [Component Name] Component

**Visual Description:**
> "[Describe how it looks using sensory language - the container, colors, shadows, spacing, what catches the eye first]"

**Data Props (What it displays):**
| Prop Name | Type | Format/Notes |
|-----------|------|--------------|
| `title` | String | Max 50 chars, truncate with ellipsis |
| `status` | Enum | 'active', 'pending', 'completed' → maps to color badges |
| `createdAt` | Date | Display as "MMM DD" (e.g., "Dec 05") |
| `progress` | Integer | 0-100, drives progress bar width |
| `assignees` | Array<User> | Show max 3 avatars, +N for overflow |

**Interactive States:**
- **Default**: [describe resting appearance]
- **Hover**: [describe what changes - shadow, border, scale]
- **Active/Pressed**: [describe pressed state]
- **Selected**: [describe selected state if applicable]
- **Disabled**: [describe disabled appearance]
- **Loading**: [describe skeleton/loading state]

**Actions:**
- **Click**: Routes to `/[route]/[id]` OR opens modal
- **Secondary Action**: [e.g., "Three-dot menu reveals Edit, Delete options"]

---

## 4. The Data Wiring (Schema-by-Screen)

*Define the database schema BY LOOKING AT THE UI. Each screen tells you what data you need.*

### Core Entities

**Based on the UI components above, we need these database tables:**

#### [Entity Name] Table
```
Purpose: [What UI elements does this support?]

Fields:
- id: UUID (primary key)
- [field_name]: [Type] — "[Why needed: which component displays this?]"
- [field_name]: [Type] — "[Why needed: which component displays this?]"
- created_at: Timestamp
- updated_at: Timestamp

Relationships:
- belongs_to: [Other Entity] via [foreign_key]
- has_many: [Other Entity]
```

### State & Computed Values

*Some UI elements need real-time or computed data:*

| UI Element | State Needed | Source |
|------------|--------------|--------|
| Notification Bell | `unread_count` (Integer) | Count where `read = false` |
| Progress Ring | `completion_percentage` | Computed from tasks completed/total |
| "Online" Indicator | `is_online` (Boolean) | Presence system / last_seen < 5min |

### State Rules & Visual Reactions
- **If** `unread_count > 0` → Show red badge with pulse animation on bell icon
- **If** `status = 'overdue'` → Card border becomes `var(--color-error)`, show warning icon
- **If** `assignees.length > 3` → Show first 3 avatars + "+N" overflow badge

## 5. Page Layouts & Flow

### [Page Name] (`/route`)

**The Feel:**
> "[Describe the overall feeling of this page - what's the user's goal, what should feel easy?]"

**Visual Structure:**
```
┌─────────────────────────────────────────────────┐
│ [Header/Nav Description]                         │
├──────────────┬──────────────────────────────────┤
│              │                                   │
│  [Sidebar]   │  [Main Content Area]             │
│              │                                   │
│              │                                   │
└──────────────┴──────────────────────────────────┘
```

**Layout Strategy:**
- **Grid/Flex**: [Describe the CSS strategy]
- **Spacing Rhythm**: [e.g., "24px gaps between cards, 16px internal padding"]
- **Max Width**: [e.g., "Content maxes at 1200px, centered on larger screens"]

**Responsive Behavior:**
| Breakpoint | Changes |
|------------|---------|
| Desktop (≥1024px) | [Full layout description] |
| Tablet (768-1023px) | [What collapses, reflows] |
| Mobile (<768px) | [Stack order, hidden elements, bottom nav] |

**Components on This Page:**
1. **[Component]** - [Position, purpose, what data it shows]
2. **[Component]** - [Position, purpose, what data it shows]

**Empty State:**
- **Illustration**: [Describe the illustration style and subject]
- **Headline**: "[Friendly, action-oriented headline]"
- **Subtext**: "[Helpful explanation, 1-2 sentences]"
- **CTA**: "[Button text]" → [What it does]

**Loading State:**
- Skeleton placeholders that match the content shape
- Subtle shimmer animation (1.5s loop)
- [Specific elements that show skeletons]

## 6. User Flows with UI States

### [Flow Name] (e.g., "Creating a New Project")

**Step-by-Step with Visual States:**

1. **Trigger**: User clicks "[Button Name]"
   - Button shows loading spinner, text fades slightly

2. **Modal Opens**: 
   - Backdrop fades in (150ms)
   - Modal scales from 0.95 → 1.0 with fade (200ms)
   - First input auto-focused

3. **Form Completion**:
   - Real-time validation on blur
   - Error state: Red border, error message slides down (150ms)
   - Valid state: Subtle green checkmark appears

4. **Submission**:
   - Submit button shows spinner, disabled state
   - Optimistic UI: New item appears immediately (with subtle loading indicator)

5. **Success**:
   - Modal closes with reverse animation
   - Toast slides in from top-right: "✓ Project created"
   - New item in list has brief highlight animation (500ms)

6. **Error Handling**:
   - If API fails: Modal stays open
   - Error toast: Red accent, "Something went wrong. Try again."
   - Submit button re-enabled

## 7. Mock Data Strategy

**CRITICAL: Use realistic, contextual mock data. Never use "Test 1", "Lorem ipsum", or obvious placeholders.**

| Data Type | Mock Examples |
|-----------|---------------|
| **Project Names** | "Nebula Dashboard", "Horizon Mobile", "Atlas CRM" |
| **User Names** | "Sarah Chen", "Marcus Johnson", "Aisha Patel" |
| **Company Names** | "Nexus Labs", "Orbit Systems", "Quantum Design Co." |
| **Emails** | "sarah@nexuslabs.io", "marcus@orbit.dev" |
| **Dates** | Use dates relative to "today" (e.g., "2 days ago", "Due Dec 15") |
| **Status Mix** | Include variety: some completed, some in-progress, some overdue |
| **Avatar Images** | Use diverse placeholder avatars (randomuser.me or similar) |

## 8. Tech Stack

- **Frontend**: Next.js 14 + TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: Zustand (client), TanStack Query (server)
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Backend**: [Based on requirements - Supabase, Firebase, custom API]
- **Database**: [Based on requirements]
- **Auth**: [Based on requirements]

## 9. Implementation Phases

### Phase 1: Visual Foundation
- [ ] Set up design tokens (colors, typography, spacing)
- [ ] Create base components with all states
- [ ] Build page layouts with responsive behavior
- [ ] Implement with realistic mock data

### Phase 2: Data Integration
- [ ] Set up database schema based on Section 4
- [ ] Connect components to real data
- [ ] Implement loading and error states
- [ ] Add optimistic updates where appropriate

### Phase 3: Polish & Delight
- [ ] Add micro-interactions and hover effects
- [ ] Implement page transitions
- [ ] Add keyboard shortcuts
- [ ] Performance optimization

---

## CRITICAL INSTRUCTIONS:

1. **70% Visual / 30% Logic** - The PRD should paint a vivid picture while ensuring the schema is airtight
2. **Schema-by-Screen** - Every data table should trace back to a UI element that needs it
3. **Sensory Language** - Describe how things *feel*, not just how they look ("confident button", "subtle hover lift")
4. **Realistic Mock Data** - Use believable names, dates, and states. Never "Test 1", "User 1"
5. **State Completeness** - Every component needs: default, hover, active, loading, error, empty, disabled states
6. **Action Clarity** - Every interactive element must specify what happens on click/interaction
7. **Minimum 2500 words** - Be thorough, especially in component narratives and data binding"""

# API Routes
@api_router.get("/")
async def root():
    return {"message": "PRD Generator API"}

# Auth Utils
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = await db.users.find_one({"email": token_data.email})
    if user is None:
        raise credentials_exception
    return User(**user)

# Auth Endpoints
@api_router.post("/auth/signup", response_model=Token)
async def signup(user: UserCreate):
    try:
        existing_user = await db.users.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        hashed_password = get_password_hash(user.password)
        new_user = User(
            email=user.email,
            password_hash=hashed_password
        )
        
        await db.users.insert_one(new_user.model_dump())
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": new_user.email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "created_at": user.created_at.isoformat()}

@api_router.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = await db.users.find_one({"email": form_data.username})
        if not user or not verify_password(form_data.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user['email']}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

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
    """Analyze user's idea and generate clarifying questions (MOCK MODE)"""
    try:
        # Mock response - no API call
        mock_questions = [
            ClarifyingQuestion(
                id="q1",
                question="What authentication method do you prefer?",
                options=[
                    QuestionOption(id="q1_a", label="Email/Password", description="Traditional login"),
                    QuestionOption(id="q1_b", label="OAuth (Google/GitHub)", description="Social login"),
                    QuestionOption(id="q1_c", label="Magic Link", description="Passwordless email"),
                ],
                category="auth"
            ),
            ClarifyingQuestion(
                id="q2",
                question="What's your target user base size?",
                options=[
                    QuestionOption(id="q2_a", label="Small (under 100 users)", description="MVP/Testing"),
                    QuestionOption(id="q2_b", label="Medium (100-10K users)", description="Growing startup"),
                    QuestionOption(id="q2_c", label="Large (10K+ users)", description="Scale-ready"),
                ],
                category="data_complexity"
            ),
            ClarifyingQuestion(
                id="q3",
                question="What's your preferred UI style?",
                options=[
                    QuestionOption(id="q3_a", label="Minimal/Clean", description="Apple-like simplicity"),
                    QuestionOption(id="q3_b", label="Feature-rich Dashboard", description="Power-user focused"),
                    QuestionOption(id="q3_c", label="Playful/Colorful", description="Consumer app vibe"),
                ],
                category="ui_style"
            ),
            ClarifyingQuestion(
                id="q4",
                question="What's your timeline?",
                options=[
                    QuestionOption(id="q4_a", label="MVP in 1 week", description="Fast prototype"),
                    QuestionOption(id="q4_b", label="Production in 1 month", description="Full features"),
                    QuestionOption(id="q4_c", label="Enterprise in 3 months", description="Complete solution"),
                ],
                category="features"
            ),
        ]
        
        idea_preview = request.idea[:50] if request.idea else "empty"
        logger.info(f"Mock analyze: Returning {len(mock_questions)} questions for: {idea_preview}...")
        return AnalyzeResponse(questions=mock_questions)
    except Exception as e:
        logger.error(f"Mock analyze error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/generate-prd", response_model=GeneratePRDResponse)
async def generate_prd(request: GeneratePRDRequest):
    """Generate PRD from idea and answers (MOCK MODE)"""
    # Format answers for display
    answers_text = "\n".join([f"- {k}: {v}" for k, v in request.answers.items()])
    
    mock_prd = f"""# Product Requirements Document

## 1. Executive Summary

**Product Name:** {request.idea.split()[0].title()}App

**Vision:** {request.idea}

## 2. User Requirements

Based on your specifications:
{answers_text}

## 3. Technical Architecture

### 3.1 Frontend
- React/Next.js with TypeScript
- Tailwind CSS for styling
- Zustand for state management

### 3.2 Backend
- FastAPI (Python)
- PostgreSQL database
- Redis for caching

### 3.3 Infrastructure
- Vercel for frontend hosting
- Railway/Render for backend
- AWS S3 for file storage

## 4. Core Features

### 4.1 User Management
- Sign up / Login
- Profile management
- Settings

### 4.2 Main Features
- Feature 1: Core functionality based on your idea
- Feature 2: Secondary features
- Feature 3: Nice-to-have additions

### 4.3 Admin Panel
- User management
- Analytics dashboard
- Content moderation

## 5. UI/UX Specifications

### 5.1 Design System
- Color palette: Dark theme with accent colors
- Typography: Inter font family
- Spacing: 4px grid system

### 5.2 Key Screens
1. Landing page
2. Dashboard
3. Profile
4. Settings

## 6. Timeline

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| Phase 1 | Week 1-2 | MVP Core |
| Phase 2 | Week 3-4 | Full Features |
| Phase 3 | Week 5-6 | Polish & Launch |

## 7. Success Metrics

- User signups: 1000 in first month
- Daily active users: 30% retention
- User satisfaction: 4.5+ rating

---

*Generated by Deep PRD (Mock Mode)*
"""
    
    logger.info(f"Mock generate-prd: Generated PRD for: {request.idea[:50]}...")
    return GeneratePRDResponse(prd=mock_prd)

@api_router.post("/prds", response_model=SavedPRD)
async def save_prd(input: SavedPRDCreate, user: User = Depends(get_current_user)):
    prd_dict = input.model_dump()
    prd_obj = SavedPRD(**prd_dict, user_id=user.id)
    doc = prd_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    _ = await db.saved_prds.insert_one(doc)
    return prd_obj

@api_router.get("/prds", response_model=List[SavedPRD])
async def get_saved_prds(user: User = Depends(get_current_user)):
    saved_prds = await db.saved_prds.find({"user_id": user.id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    for prd in saved_prds:
        if isinstance(prd['created_at'], str):
            prd['created_at'] = datetime.fromisoformat(prd['created_at'])
    return saved_prds

@api_router.get("/prds/{prd_id}", response_model=SavedPRD)
async def get_saved_prd(prd_id: str, user: User = Depends(get_current_user)):
    prd = await db.saved_prds.find_one({"id": prd_id, "user_id": user.id}, {"_id": 0})
    if not prd:
        raise HTTPException(status_code=404, detail="PRD not found")
    if isinstance(prd['created_at'], str):
        prd['created_at'] = datetime.fromisoformat(prd['created_at'])
    return prd

@api_router.patch("/prds/{prd_id}/idea", response_model=SavedPRD)
async def update_prd_idea(prd_id: str, input: SavedPRDUpdateIdea, user: User = Depends(get_current_user)):
    result = await db.saved_prds.find_one_and_update(
        {"id": prd_id, "user_id": user.id},
        {"$set": {"idea": input.idea}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="PRD not found")
    if isinstance(result['created_at'], str):
        result['created_at'] = datetime.fromisoformat(result['created_at'])
    return result

@api_router.put("/prds/{prd_id}/content", response_model=SavedPRD)
async def update_prd_content(prd_id: str, input: SavedPRDUpdateContent, user: User = Depends(get_current_user)):
    result = await db.saved_prds.find_one_and_update(
        {"id": prd_id, "user_id": user.id},
        {"$set": {"content": input.content}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="PRD not found")
    if isinstance(result['created_at'], str):
        result['created_at'] = datetime.fromisoformat(result['created_at'])
    return result

@api_router.delete("/prds/{prd_id}/content", response_model=SavedPRD)
async def delete_prd_content(prd_id: str, user: User = Depends(get_current_user)):
    result = await db.saved_prds.find_one_and_update(
        {"id": prd_id, "user_id": user.id},
        {"$set": {"content": ""}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="PRD not found")
    if isinstance(result['created_at'], str):
        result['created_at'] = datetime.fromisoformat(result['created_at'])
    return result

@api_router.delete("/prds/{prd_id}")
async def delete_saved_prd(prd_id: str, user: User = Depends(get_current_user)):
    result = await db.saved_prds.delete_one({"id": prd_id, "user_id": user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="PRD not found")
    return {"message": "PRD deleted successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,  # Bearer token doesn't require credentials/cookies
    allow_origins=["*"],      # Allow all origins
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
