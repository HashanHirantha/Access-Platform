"""
AccessGuard — FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers.workspace import router as workspace_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables if they don't exist."""
    try:
        await init_db()
        print(" Connected to PostgreSQL database successfully.")
    except Exception as e:
        print(f"\n [Database Connection Error] {e}")
        print("💡 Ensure PostgreSQL is running and credentials in backend/.env are correct.")
        print("💡 To start PostgreSQL with Docker: docker compose up -d db\n")
    yield


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise user access review and governance platform",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(workspace_router)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "database": "postgresql",
    }

