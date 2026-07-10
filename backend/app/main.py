from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.users import (
    router as users_router
)
from backend.app.api.v1.companions import (
    router as companion_router
)
from backend.app.api.v1.conversations import (
    router as conversation_router
)
from backend.app.api.v1.chat import (
    router as chat_router
)
from backend.app.api.v1.user_onboarding import (
    router as user_onboarding_router
)

from backend.app.api.v1 import tts
from backend.app.api.v1 import documents

from backend.app.api.v1.liveavatar import (
    router as liveavatar_router
)
from backend.app.api.v1.heygenavatar import (
    router as heygen_router
)

from backend.app.api.v1.tavus import (
    router as tavus_router
)
from backend.app.api.v1.tavus_tools import (
    router as tavus_tools_router
)

app = FastAPI(
    title="AI Companion Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    users_router,
    prefix="/api/v1/users",
    tags=["Users"]
)

app.include_router(
    user_onboarding_router,
    prefix="/api/v1/user-onboarding",
    tags=["User Onboarding"]
)

app.include_router(
    companion_router,
    prefix="/api/v1/companions",
    tags=["Companions"]
)

app.include_router(
    conversation_router,
    prefix="/api/v1/conversations",
    tags=["Conversations"]
)

app.include_router(
    chat_router,
    prefix="/api/v1/chat",
    tags=["Chat"]
)

app.include_router(
    tts.router,
    prefix="/api/v1/tts",
    tags=["Text To Speech"]
)

app.include_router(
    documents.router,
    prefix="/api/v1/documents",
    tags=["Documents"]
)

app.include_router(
    liveavatar_router,
    prefix="/api/v1/liveavatar",
    tags=["LiveAvatar"]
)

app.include_router(
    heygen_router,
    prefix="/api/v1/heygenavatar",
    tags=["HeyGen Avatar"]
)

app.include_router(
    tavus_router,
    prefix="/api/v1/tavus",
    tags=["Tavus Avatar"]
)

app.include_router(
    tavus_tools_router,
    prefix="/api/v1/tavus_tools",
    tags=["Tavus Tools"]
)

@app.get("/")
def root():
    return {
        "message": "AI Companion Platform API"
    }