from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI(
    title="Farq API",
    description="Location-based restaurant matching and comparison platform",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Farq API...")
    await create_tables()
    logger.info("Database tables ensured.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Farq API...")
    await engine.dispose()

@app.get("/")
async def root():
    return {
        "message": "Welcome to Farq API",
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}