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

PRD_GENERATOR_PROMPT = """You are a Senior Frontend Architect & Design Systems Lead creating production-ready PRDs for AI coding tools like Cursor, Lovable, Bolt, or Emergent.

Your PRDs are known for their EXCEPTIONAL FRONTEND DETAIL - design-system-heavy, pixel-perfect specifications that result in polished, production-quality UIs on the first build.

Generate a comprehensive PRD with HEAVY EMPHASIS on UI/UX specifications. The frontend section should be the most detailed part of the document.

# [App Name] - Product Requirements Document

## 1. The North Star
- **Vision**: One sentence describing what this app does
- **Target User**: Who uses this and their main pain point
- **Design Philosophy**: The visual and interaction principles guiding the UI

## 2. Tech Stack
- **Frontend**: Next.js 14 / React 18 + TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **State**: Zustand for client state, TanStack Query for server state
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Backend**: [Based on requirements]
- **Database**: [Based on requirements]
- **Auth**: [Based on requirements]

## 3. Design System (CRITICAL SECTION)

### 3.1 Color Tokens
```css
/* Primary Palette */
--color-primary: #[hex];           /* Main brand color */
--color-primary-hover: #[hex];     /* Hover state */
--color-primary-active: #[hex];    /* Active/pressed state */
--color-primary-subtle: #[hex];    /* Backgrounds, badges */

/* Neutral Palette */
--color-background: #[hex];        /* Page background */
--color-surface: #[hex];           /* Card/panel backgrounds */
--color-surface-elevated: #[hex];  /* Modals, dropdowns */
--color-border: #[hex];            /* Default borders */
--color-border-subtle: #[hex];     /* Subtle dividers */

/* Text Colors */
--color-text-primary: #[hex];      /* Headings, important text */
--color-text-secondary: #[hex];    /* Body text */
--color-text-muted: #[hex];        /* Captions, placeholders */
--color-text-inverse: #[hex];      /* Text on dark backgrounds */

/* Semantic Colors */
--color-success: #[hex];
--color-warning: #[hex];
--color-error: #[hex];
--color-info: #[hex];
```

### 3.2 Typography Scale
```css
/* Font Family */
--font-sans: 'Inter', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', monospace;

/* Font Sizes */
--text-xs: 0.75rem;      /* 12px - Captions */
--text-sm: 0.875rem;     /* 14px - Small text */
--text-base: 1rem;       /* 16px - Body */
--text-lg: 1.125rem;     /* 18px - Large body */
--text-xl: 1.25rem;      /* 20px - Small headings */
--text-2xl: 1.5rem;      /* 24px - Section headings */
--text-3xl: 1.875rem;    /* 30px - Page headings */
--text-4xl: 2.25rem;     /* 36px - Hero headings */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;

/* Line Heights */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.625;
```

### 3.3 Spacing System
```css
/* Base unit: 4px */
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

### 3.4 Border Radius
```css
--radius-sm: 4px;      /* Small elements, tags */
--radius-md: 8px;      /* Buttons, inputs */
--radius-lg: 12px;     /* Cards, panels */
--radius-xl: 16px;     /* Modals, large cards */
--radius-full: 9999px; /* Pills, avatars */
```

### 3.5 Shadows & Elevation
```css
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
--shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1);
--shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1);
--shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.1);
```

### 3.6 Animation Tokens
```css
/* Durations */
--duration-fast: 150ms;
--duration-normal: 200ms;
--duration-slow: 300ms;

/* Easings */
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
```

## 4. Component Specifications

### 4.1 Button Component
```
Variants: primary, secondary, outline, ghost, destructive
Sizes: sm (h-8 px-3 text-sm), md (h-10 px-4 text-sm), lg (h-12 px-6 text-base)

States:
- Default: [base styles]
- Hover: brightness +5%, scale(1.02), transition 150ms
- Active: scale(0.98), brightness -5%
- Disabled: opacity 50%, cursor not-allowed
- Loading: spinner icon, text opacity 0

Focus: ring-2 ring-primary ring-offset-2
```

### 4.2 Input Component
```
Height: h-10 (40px)
Padding: px-3
Border: 1px solid var(--color-border)
Border Radius: var(--radius-md)

States:
- Default: border-gray-300, bg-white
- Focus: border-primary, ring-2 ring-primary/20
- Error: border-error, ring-2 ring-error/20
- Disabled: bg-gray-100, cursor not-allowed

Placeholder: text-muted, font-normal
```

### 4.3 Card Component
```
Background: var(--color-surface)
Border: 1px solid var(--color-border)
Border Radius: var(--radius-lg)
Padding: var(--space-6)
Shadow: var(--shadow-sm)

Hover (if interactive): 
- shadow-md
- border-color: var(--color-border-hover)
- transform: translateY(-2px)
- transition: all 200ms ease-out
```

### 4.4 Modal/Dialog
```
Overlay: bg-black/50, backdrop-blur-sm
Container: bg-surface, rounded-xl, shadow-xl
Animation: 
- Enter: fade in 200ms, scale from 0.95
- Exit: fade out 150ms, scale to 0.95
Padding: p-6
Max Width: max-w-md (default), max-w-lg, max-w-xl
```

## 5. Page Layouts

### 5.1 [Page Name] (/route)

**Layout Structure:**
```
┌─────────────────────────────────────────┐
│ Header (h-16, sticky top-0)             │
├─────────────────────────────────────────┤
│ Sidebar (w-64)  │  Main Content         │
│                 │  (flex-1, p-6)        │
│                 │                       │
│                 │                       │
└─────────────────────────────────────────┘
```

**Responsive Behavior:**
- Desktop (≥1024px): Full sidebar visible
- Tablet (768-1023px): Sidebar collapsed to icons (w-16)
- Mobile (<768px): Sidebar hidden, hamburger menu, bottom nav

**Components on Page:**
1. [Component] - Position, purpose, interactions
2. [Component] - Position, purpose, interactions

**Empty State:**
- Illustration: [describe]
- Heading: "[text]"
- Subtext: "[text]"
- CTA Button: "[text]"

**Loading State:**
- Skeleton placeholders matching content layout
- Pulse animation on skeletons

## 6. Micro-Interactions & Animations

### Page Transitions
- Route change: Fade + slide (200ms)
- Content load: Stagger children (50ms delay each)

### Hover Effects
- Buttons: Scale 1.02, brightness +5%
- Cards: Lift (translateY -2px), shadow increase
- Links: Underline slide in from left

### Feedback Animations
- Success: Checkmark draw animation (400ms)
- Error: Shake animation (300ms, 3 shakes)
- Loading: Spinner rotation (continuous)
- Toast: Slide in from top-right, auto-dismiss 4s

### Skeleton Loading
```css
.skeleton {
  background: linear-gradient(90deg, var(--color-surface) 25%, var(--color-surface-elevated) 50%, var(--color-surface) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

## 7. Core Features

### Feature 1: [Name]

**UI Components Required:**
- [List specific components with their variants]

**User Flow with UI States:**
1. User lands on [page] → sees [initial state]
2. User clicks [element] → [button shows loading state]
3. System processes → [loading indicator/skeleton]
4. Success → [success state, toast notification]
5. Error → [error state, inline error message]

**API Integration:**
```
POST /api/[endpoint]
Request: { field: type }
Response: { data: type }
```

**Edge Cases UI:**
| State | Visual Treatment |
|-------|------------------|
| Empty | Illustration + CTA centered |
| Loading | Skeleton matching content shape |
| Error | Red border, error icon, message below |
| Success | Green checkmark, success toast |

## 8. Data Schema
[TypeScript interfaces for all entities]

## 9. API Reference
[All endpoints with request/response shapes]

## 10. Implementation Phases

### Phase 1: MVP
- [ ] Design system setup (colors, typography, spacing)
- [ ] Core layout components
- [ ] Main feature UI
- [ ] Basic states (loading, error, empty)

### Phase 2: Polish
- [ ] Micro-interactions
- [ ] Animations
- [ ] Responsive refinements
- [ ] Accessibility (focus states, ARIA)

### Phase 3: Delight
- [ ] Advanced animations
- [ ] Skeleton loaders
- [ ] Optimistic updates
- [ ] Keyboard shortcuts

---

CRITICAL INSTRUCTIONS:
1. The Design System section must have EXACT values (hex colors, pixel values, timing)
2. Every component needs all states specified (default, hover, active, disabled, loading, error)
3. Include ASCII layout diagrams for page structures
4. Animations must have duration and easing specified
5. The PRD should enable an AI to build a POLISHED, PRODUCTION-READY frontend
6. Minimum 3000 words, with 60% focused on UI/UX specifications"""

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
