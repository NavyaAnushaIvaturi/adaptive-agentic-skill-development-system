from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.auth_routes import (
    router as auth_router,
)
from backend.api.routes import (
    router as learning_router,
)
from backend.database import models
from backend.database.database import (
    Base,
    engine,
)


# Create all database tables when the application starts.
Base.metadata.create_all(
    bind=engine
)


# Create the FastAPI application.
app = FastAPI(

    title=(
        "Adaptive Agentic "
        "Skill Development System"
    ),

    version="1.0.0",

    description=(
        "Adaptive learning platform "
        "with personalized roadmaps, "
        "detailed lessons, assessments, "
        "adaptive learning, progress "
        "tracking, and learner accounts."
    ),
)


# Configure CORS to allow requests from the frontend.
app.add_middleware(

    CORSMiddleware,

    allow_origins=[

        "http://localhost:3000",

        "http://localhost:5173",

        "http://127.0.0.1:3000",

        "http://127.0.0.1:5173",
        
        "https://adaptive-agentic-skill-development-0dvv.onrender.com",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# Add authentication and learning API routes.
app.include_router(
    auth_router
)

app.include_router(
    learning_router
)


# Return basic application information.
@app.get("/")
def root():

    return {

        "message": (
            "Adaptive Agentic "
            "Skill Development System"
        ),

        "status":
            "running",

        "version":
            "1.0.0",
    }


# Check whether the application is healthy.
@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# Return the configuration status of system components.
@app.get("/system/status")
def system_status():

    return {

        "application":
            "running",

        "database":
            "configured",

        "llm":
            "configured",

        "langgraph":
            "configured",

        "langsmith":
            "configured",

        "resource_search":
            "optional",
    }