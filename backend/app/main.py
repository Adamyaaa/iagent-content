from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import ingestion, dashboard, settings as settings_router

app = FastAPI(
    title="iAgent Solutions Content OS",
    description="Core backend for the fully automated AI content intelligence and generation system.",
    version="1.0.0"
)

# CORS setup for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion.router)
app.include_router(dashboard.router)
app.include_router(settings_router.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the iAgent Solutions Content OS API"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment
    }
