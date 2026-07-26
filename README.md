# AI Companion App

## About the Project

AI Companion App is a platform that provides users with a team of AI companions designed to help them grow in different areas of life.

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

## Developer Setup Guide ???

To contribute to the AI Companion App, follow these steps to run the full stack locally.

### Prerequisites

1. **Docker**: To run the PostgreSQL database locally without native installation.
2. **uv**: An extremely fast Python package and project manager (replaces pip/poetry). Install it via curl -LsSf https://astral.sh/uv/install.sh | sh or pip install uv.
3. **Node.js**: v18+ for running the Next.js frontend.

### 1. Database Setup
Spin up the local PostgreSQL database using Docker:
```bash
docker compose up -d
```
This will start a Postgres 15 container exposing port 5432.

### 2. Environment Variables & Webhooks (Ngrok)
Tavus requires a publicly accessible URL to send conversation transcripts via webhooks when a call ends. Since it cannot reach `localhost`, you must use ngrok to expose your local backend.

1. Install ngrok and run it in a new terminal:
```bash
ngrok http 8000
```
2. Copy the provided `.env` template:
```bash
cp .env.example .env
```
3. Update `.env` with your specific API keys, and set `BACKEND_URL` to your forwarding ngrok URL (e.g., `https://abcdefg.ngrok-free.app`).

### 3. Backend Setup & Run
We use uv for lightning-fast dependency management. From the root directory:
```bash
# Apply database migrations
uv run alembic upgrade head

# Start the FastAPI development server
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend will run on http://localhost:8000.

### 4. Frontend Setup & Run
In a new terminal window, navigate to the frontend folder:
```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```
The frontend will run on http://localhost:3000.

