from fastapi import APIRouter, HTTPException, Depends
from typing import List
from beanie.odm.operators.find.comparison import In
from bson import ObjectId

from models import (
    DanceStyle,
    Song,
    TutorialStep,
    UserSongStatus,
    DanceStyleResponse,
    SongResponse,
    TutorialStepResponse,
)
from auth import get_current_user_id

router = APIRouter()

# ---------------------------------------------------------------
# 1️⃣ Get all dance styles
# ---------------------------------------------------------------
@router.get("/styles", response_model=List[DanceStyleResponse])
async def get_all_dance_styles():
    """
    Fetches all available dance styles from the database.
    Public endpoint (no authentication required).
    """
    styles = await DanceStyle.find_all().to_list()

    # Convert ObjectId → str for each item
    return [DanceStyleResponse(id=str(s.id),
                               dance_name=s.dance_name,
                               description=s.description,
                               origin=s.origin,
                               songs=s.songs,
                               img=s.img)
            for s in styles]


# ---------------------------------------------------------------
# 2️⃣ Get all songs under a specific dance style
# ---------------------------------------------------------------
@router.get("/{dance_id}", response_model=List[SongResponse])
async def get_songs_in_style(dance_id: str, current_user_id: str = Depends(get_current_user_id)):
    print("inside the function")
    """
    Fetch all songs for a specific dance style and include the user's progress.
    """
    if not ObjectId.is_valid(dance_id):
        raise HTTPException(status_code=400, detail="Invalid dance_id format")

    # Find songs belonging to this dance style
    songs = await Song.find(Song.dance_style.id == ObjectId(dance_id)).to_list()
    if not songs:
        return []

    song_ids = [song.id for song in songs]

    # Get user's status for these songs
    user_statuses = await UserSongStatus.find(
        UserSongStatus.user.id == ObjectId(current_user_id),
        In(UserSongStatus.song.id, song_ids)
    ).to_list()

    # Create a quick lookup table for statuses
    status_map = {str(status.song.id): status.status for status in user_statuses}

    # Build response list
    response = []
    for song in songs:
        response.append(
            SongResponse(
                id=str(song.id),
                name=song.name,
                description=song.description,
                time=song.time,
                lessons=song.lessons,
                teacher=song.teacher,
                status=status_map.get(str(song.id), "start"),
            )
        )
    return response


# ---------------------------------------------------------------
# 3️⃣ Get all tutorial steps for a specific song
# ---------------------------------------------------------------
@router.get("/{dance_id}/{song_id}", response_model=List[TutorialStepResponse])
async def get_tutorial_steps(dance_id: str, song_id: str, current_user_id: str = Depends(get_current_user_id)):
    """
    Fetch tutorial steps for a specific song and mark them as
    'completed' or 'pending' based on user's song progress.
    """
    if not ObjectId.is_valid(song_id):
        raise HTTPException(status_code=400, detail="Invalid song_id format")

    steps = await TutorialStep.find(TutorialStep.song.id == ObjectId(song_id)).to_list()
    if not steps:
        return []

    user_status = await UserSongStatus.find_one(
        UserSongStatus.user.id == ObjectId(current_user_id),
        UserSongStatus.song.id == ObjectId(song_id)
    )

    # Determine completion percentage
    song_progress = user_status.progress if user_status else 0
    total_steps = len(steps)
    completed_steps = round((song_progress / 100) * total_steps)

    # Build step list
    response = []
    for i, step in enumerate(steps):
        response.append(
            TutorialStepResponse(
                id=str(step.id),
                name=step.name,
                time=step.time,
                description=step.description,
                status="completed" if i < completed_steps else "pending",
            )
        )

    return response
