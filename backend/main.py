import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from database import settings
from models import User, DanceStyle, Song, TutorialStep, UserSongStatus
from routes.auth_routes import router as auth_router
from routes.dance_routes import router as dance_router
from routes.user_routes import router as user_router
from routes.pose_routes import router as pose_router 
from fastapi.staticfiles import StaticFiles



# Create FastAPI app instance
app = FastAPI(
    title="Dance Tutorial API",
    description="Backend service for a dance tutorial platform.",
    version="1.0.0"
)

# CORS (Cross-Origin Resource Sharing) Middleware
# This allows your frontend to communicate with this backend.
# Be sure to restrict origins in a production environment.
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
] 
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize the database connection
@app.on_event("startup")
async def app_init():
    """
    Initialize the database connection and Beanie ODM.
    """
    client = AsyncIOMotorClient(settings.DATABASE_URL)
    # The document_models list tells Beanie which models to work with.
    await init_beanie(
        database=client.get_database(),
        document_models=[User, DanceStyle, Song, TutorialStep, UserSongStatus]
    )

# Static resources
app.mount("/static", StaticFiles(directory="static_pose_comparision"), name="static")

# Include API routers
app.include_router(auth_router, tags=["Authentication"], prefix="/api/auth")
app.include_router(dance_router, tags=["Dance Content"], prefix="/api/dance")
app.include_router(user_router, tags=["User Progress"], prefix="/api/user")
app.include_router(pose_router, tags=["Pose Feedback"]) 

# Root endpoint
@app.get("/api", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Dance Tutorial API!"}

# This part is for running the app with `python main.py`
# In a production environment, you would use a process manager like Gunicorn.
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
