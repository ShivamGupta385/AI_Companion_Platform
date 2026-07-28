# AI Companion Platform — 5-Agent MVP

[![Watch Demo Video](https://img.shields.io/badge/▶_Watch_Demo_Video-Vimeo-00ADEF?style=for-the-badge&logo=vimeo&logoColor=white)](https://vimeo.com/1213563606)

---

## 🎬 Project Walkthrough & Demo Video

Experience the platform in action! Watch our full technical walkthrough showcasing real-time video AI companions, interactive Magic Canvas overlays, and multi-agent workflows:

🎥 **[Watch the Working Platform Demo on Vimeo](https://vimeo.com/1213563606)**

---

## About the Project

AI Companion Platform is an enterprise MVP that provides users with a team of AI companions designed to help them grow in different areas of life.

Unlike traditional chatbots, these companions remember past conversations, understand user goals, and work together to provide personalized guidance over time.

The goal is to create a supportive AI ecosystem that feels consistent, intelligent, and helpful in everyday life.

---

## AI Companions

### Meet the Companions

### 📚 Aria — Study Companion

A patient and encouraging tutor who helps users understand concepts, prepare for exams, improve learning habits, and build academic confidence.

#### Focus Areas

- Learning & Education
- Exam Preparation
- Homework Support
- Knowledge Retention

---

### 🌙 Noor — Mindfulness & Sleep Guide

A calm and compassionate companion focused on mental wellness, stress management, mindfulness, and healthy sleep routines.

#### Focus Areas

- Meditation
- Stress Reduction
- Sleep Guidance
- Emotional Wellbeing

---

### 🎯 Rene — Life Coach

The central coaching companion that helps users gain clarity, build habits, set goals, and take meaningful action.

#### Focus Areas

- Goal Setting
- Productivity
- Personal Growth
- Accountability

---

### 💪 Max — Fitness Coach

An energetic fitness mentor that helps users stay active, build healthy habits, and maintain consistency in their wellness journey.

#### Focus Areas

- Workout Guidance
- Fitness Planning
- Habit Building
- Motivation

---

### 📈 Victor — Business Coach

A strategic advisor that helps entrepreneurs, professionals, and creators make better business and career decisions.

#### Focus Areas

- Business Strategy
- Career Growth
- Decision Making
- Entrepreneurship

---

## Target Users

The platform is designed for:

- Students
- Working Professionals
- Entrepreneurs
- Fitness Enthusiasts
- Self-Improvement Seekers
- Individuals focused on mental wellness

---

## MVP Scope

The initial release includes:

- Five AI companions
- Persistent user memory
- Cross-companion collaboration
- Text and voice interactions
- Personalized guidance experiences
- Goal tracking and progress awareness

---

## Project Vision

Our long-term vision is to create a digital “guiding companion” that grows with users over months and years.

The platform should:

- Remember important context
- Understand personal goals
- Provide meaningful support
- Encourage growth without judgment
- Be available whenever users need guidance
---

## Tech Stack Overview

- **Backend Architecture**: FastAPI, Python 3.11+, SQLAlchemy ORM, PostgreSQL database, Alembic migrations.
- **AI & Real-Time Video**: Tavus Conversational Video API (Persona IDs, custom prompts, webhook ingestion), Tavus Magic Canvas.
- **RAG & Vector Storage**: Pinecone Vector Database, Hugging Face `sentence-transformers/all-MiniLM-L6-v2` local embeddings.
- **Frontend Architecture**: Next.js 14+ (App Router), TypeScript, TailwindCSS, Lucide Icons, Custom Activity Calendar.
- **DevOps & Tooling**: Docker Compose (isolated DB container), `uv` (fast Python package manager), Ngrok (webhook tunneling).

---

## Repository Structure

```
ai-companion-platform/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST Endpoints (auth, companions, tavus_tools, documents, etc.)
│   │   ├── core/            # Config, security, database session management
│   │   ├── db/              # SQLAlchemy session initialization
│   │   ├── models/          # PostgreSQL database schemas (11 models)
│   │   ├── schemas/         # Pydantic schemas for API validation
│   │   ├── services/        # Vector store & document ingestion services
│   │   └── main.py          # FastAPI application entrypoint
│   └── scripts/             # Automated setup, seeding, and tool sync scripts
├── frontend/                # Next.js App Router frontend application
│   ├── src/
│   │   ├── app/             # Page routes (dashboard, companions, onboarding, calendar, etc.)
│   │   ├── components/      # React components (TavusAvatar, Heatmap, OnboardingForm, UI)
│   │   └── lib/             # API client and utility helpers
├── alembic/                 # Database migration scripts
├── docker-compose.yml       # Docker database configuration
└── README.md                # Project documentation
```

---

## Developer Setup & Installation Guide (Branch: `optimised_code`)

To get this project running perfectly on your local machine, follow these steps. **You will not need to edit any application code** — everything is automated via setup scripts!

### Prerequisites
1. **Docker**: Ensure Docker Desktop is running.
2. **uv**: We use `uv` for lightning-fast Python dependency management. Install via `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`.
3. **Node.js**: v18+ for running the Next.js frontend.
4. **Ngrok**: For receiving Tavus webhooks locally.
5. **API Keys**: You will need a **Tavus API Key** and a **Pinecone API Key**.

### 1. Clone & Checkout
Clone the repository and switch to the optimized branch:
```bash
git clone https://github.com/ShivamGupta385/AI_Companion_Platform.git
cd ai-companion-platform
git checkout optimised_code
```

### 2. Environment Variables (.env)
We strictly use `.env` files for all secrets. 

**Backend (`.env`)**
Create your `.env` file in the root directory and add the following:
```env
# Database (use Port 5433 (or any other port number) to avoid conflicts with native Windows Postgres)
DATABASE_URL=postgresql+psycopg://postgres:admin@localhost:5433/ai_companion

# Security
SECRET_KEY="your-random-secret-key-here"
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Pinecone (Create a free account and get an API key)
PINECONE_API_KEY="your-pinecone-api-key"
PINECONE_INDEX_NAME="ai-companion-index"

# Tavus
TAVUS_API_KEY="your-tavus-api-key"
TAVUS_BASE_URL=https://tavusapi.com

# We will set BACKEND_URL in step 7!
```

**Frontend (`frontend/.env.local`)**
Navigate to the `frontend/` directory and create `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
```

### 3. Spin up the Database
Start the isolated PostgreSQL database using Docker:
```bash
docker compose up -d
```
*(Note: If you need to use a different port than `5433`, you must change the host port mapping in `docker-compose.yml` AND update the `DATABASE_URL` in your `.env` file to match.)*

### 4. Run Database Migrations
Create all the necessary tables in your empty database:
```bash
uv run alembic upgrade head
```

### 5. Create Pinecone Index
Run the automated script to spin up your Pinecone vector database. It will automatically read your `.env` to create an index with the correct name and dimensions:
```bash
uv run python -m backend.scripts.create_index
```
*(Note: This project uses a local open-source Hugging Face model (`sentence-transformers/all-MiniLM-L6-v2`) for embeddings. This means you do NOT need an OpenAI API key for document search, and the Pinecone index is automatically configured for exactly 384 dimensions to match this model!)*

### 6. Run the Developer Setup Script (CRITICAL)
Tavus requires Personas and Tools to be registered **per account**. We built a robust script that automatically registers all the tools, creates the 5 AI companions on your personal Tavus account, and **dynamically updates the Python codebase** with your newly generated IDs!
```bash
uv run python -m backend.scripts.setup_teammate
```

### 7. Seed the Database
Now that the codebase has been populated with your personal Tavus IDs, insert them into your database:
```bash
uv run python -m backend.scripts.seed_companions
```

### 8. Webhook Setup (Ngrok)
Tavus needs to send webhooks to your local machine. 
1. Open a new terminal and run: `ngrok http 8000`
2. Copy the `Forwarding` URL (e.g., `https://1234-abcd.ngrok-free.app`)
3. Paste it into your `.env` file as `BACKEND_URL="https://1234-abcd.ngrok-free.app"`
4. Run the sync script so Tavus knows where to send webhooks:
```bash
uv run python -m backend.scripts.sync_tool_urls
```
*(Note: You must run this sync script every time you restart ngrok and get a new URL!)*

### 9. Run the App!
**Start the Backend:**
```bash
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
**Start the Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Go to `http://localhost:3000/register`, create an account, and start chatting with your AI companions!

