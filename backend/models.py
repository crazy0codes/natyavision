from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from beanie import Document, Link
from uuid import UUID, uuid4
from datetime import datetime

# =====================================================================
# Beanie ODM Models (for MongoDB)
# These models define the structure of the data in the database.
# =====================================================================

class User(Document):
    user_id: UUID = Field(default_factory=uuid4, unique=True)
    email: EmailStr = Field(..., unique=True)
    hashed_password: str
    
    class Settings:
        name = "users" # MongoDB collection name

class DanceStyle(Document):
    dance_name: str
    description: str
    origin: str
    songs: int
    img: str

    class Settings:
        name = "dance_styles"

class Song(Document):
    dance_style: Link[DanceStyle] # Reference to the DanceStyle document
    name: str
    description: str
    time: int # in minutes
    lessons: int
    teacher: str

    class Settings:
        name = "songs"

class TutorialStep(Document):
    song: Link[Song] # Reference to the Song document
    name: str # e.g., "Step 1"
    time: int # in minutes
    description: str

    class Settings:
        name = "tutorial_steps"

class UserSongStatus(Document):
    user: Link[User] # Reference to the User document
    song: Link[Song] # Reference to the Song document
    status: str = "start"  # "start", "resume", "completed"
    progress: int = 0  # 0-100
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "user_song_status"


# =====================================================================
# Pydantic Models (for API requests and responses)
# These models define the shape of the data sent to and from the API.
# =====================================================================

# ----- Authentication -----
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AuthResponse(BaseModel):
    jwt_token: str
    email: EmailStr
    status: str
    message: Optional[str] = None

# ----- Dance Content -----
class DanceStyleResponse(BaseModel):
    id: str = Field(..., alias="_id") # Map MongoDB's _id to id
    dance_name: str
    description: str
    origin: str
    songs: int
    img: str
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class SongResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    description: str
    time: int
    lessons: int
    status: str # This will be dynamically set based on user progress
    teacher: str
    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        
class TutorialStepResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    status: str # Dynamically set
    time: int
    description: str
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

# ----- User Progress -----
class UserStatusResponse(BaseModel):
    song_name: str
    dance_name: str
    status: str
    progress: int

class UserStatusUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None

class UpdateSuccessResponse(BaseModel):
    message: str
    status: str
