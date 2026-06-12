from fastapi import FastAPI

from backend.app.api.v1.auth import router as auth_router


app = FastAPI(
    title="AI Companion Platform",
    version="1.0.0"
)

app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


@app.get("/")
def root():
    return {
        "message": "AI Companion Platform API"
    }