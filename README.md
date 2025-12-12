# DPRD (Deep PRD)

## 1. Project Title
**DPRD: AI-Powered Product Requirements Document Generator**

Give your product requirements a jumpstart. DPRD leverages AI to interview you about your app idea, identifying gaps and generating professional, design-system-ready specifications instantly.

---

## 2. Problem Statement
Bridging the gap between a raw app idea and a technical specification ready for development is time-consuming and prone to ambiguity. Modern coding agents (like Lovable or Cursor) require highly specific prompts to function well. **DPRD** solves this by acting as an intelligent product manager—analyzing your concept, asking clarifying questions, and auto-generating rigorous PRDs optimized for generative UI development.

---

## 3. System Architecture
The project follows a modern client-server architecture separating the React frontend from the FastAPI backend.

**Frontend** → **Backend (API)** → **Database** & **AI Service**

*   **Frontend**: React 19 SPA running on Vercel.
*   **Backend**: FastAPI (Python) REST API running on Render.
*   **Database**: MongoDB Atlas for persistent storage of users and PRDs.
*   **Authentication**: JWT-based stateless authentication.
*   **AI**: Google Gemini Pro for intelligent reasoning and content generation.

---

## 4. Key Features

| Category | Features |
| :--- | :--- |
| **Authentication** | User registration and secure login using JWT tokens; Password hashing with Bcrypt. |
| **AI Analysis** | intelligent breakdown of vague ideas; Automatic generation of context-aware clarifying questions. |
| **PRD Generation** | Creates extensive documentation including Design Systems, Schema-by-screen, and User Flows. |
| **History & Management** | Save, search, and filter previously generated PRDs; Persisted in MongoDB. |
| **UI/UX** | Modern dark-mode interface; Responsive layout; Glassmorphism effects using Tailwind CSS & Shadcn/UI. |
| **Export/Usage** | content formatted specifically to be copy-pasted into AI coding tools (Cursor, Bolt, etc). |

---

## 5. Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 19, React Router v7, Tailwind CSS, Shadcn/UI (Radix), Lucide React |
| **Backend** | Python 3.10+, FastAPI, Pydantic, Motor (Async Mongo Driver) |
| **Database** | MongoDB Atlas |
| **Authentication** | JSON Web Tokens (JWT), Passlib |
| **AI** | Google Gemini API (Generative Language) |
| **Hosting** | Vercel (Frontend), Render (Backend) |

---

## 6. API Overview

| Endpoint | Method | Description | Access |
| :--- | :--- | :--- | :--- |
| `/api/auth/signup` | POST | Register a new user account | Public |
| `/api/auth/login` | POST | Authenticate and receive access token | Public |
| `/api/auth/me` | GET | Retrieve current user profile | Authenticated |
| `/api/analyze` | POST | Analyze idea & generate clarifying questions | Public |
| `/api/generate-prd` | POST | Generate full PRD from answers | Public |
| `/api/prds` | POST | Save a generated PRD to history | Authenticated |
| `/api/prds` | GET | List saved PRDs (supports filtering) | Authenticated |
| `/api/status` | GET | Check system health | Public |
