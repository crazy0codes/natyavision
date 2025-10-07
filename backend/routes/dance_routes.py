from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from beanie.odm.operators.find.comparison import In
from bson import ObjectId

from models import DanceStyle, Song, TutorialStep, UserSongStatus, DanceStyleResponse, SongResponse, TutorialStepResponse
from auth import get_current_user_id

router = APIRouter()

@router.get("/styles", response_model=List[DanceStyleResponse])
async def get_all_dance_styles():
    """
    Fetches all available dance styles from the database.
    This is a public endpoint and does not require authentication.
    """
    styles = await DanceStyle.find_all().to_list()
    return styles

@router.get("/{dance_id}", response_model=List[SongResponse])
async def get_songs_in_style(dance_id: str, current_user_id: str = Depends(get_current_user_id)):
    """
    Fetches all songs for a specific dance style.
    It also fetches the user's progress for each song to determine the 'status'.
    """
    if not ObjectId.is_valid(dance_id):
        raise HTTPException(status_code=400, detail="Invalid dance_id format")

    songs = await Song.find(Song.dance_style.id == ObjectId(dance_id)).to_list()
    if not songs:
        return []

    song_ids = [song.id for song in songs]
    
    # Find user's status for these songs
    user_statuses = await UserSongStatus.find(
        UserSongStatus.user.id == ObjectId(current_user_id),
        In(UserSongStatus.song.id, song_ids)
    ).to_list()

    status_map = {str(status.song.id): status.status for status in user_statuses}

    # Prepare response
    response = []
    for song in songs:
        song_data = song.dict()
        song_data["_id"] = str(song.id)
        song_data["status"] = status_map.get(str(song.id), "start")
        response.append(SongResponse(**song_data))
        
    return response


@router.get("/{dance_id}/{song_id}", response_model=List[TutorialStepResponse])
async def get_tutorial_steps(dance_id: str, song_id: str, current_user_id: str = Depends(get_current_user_id)):
    """
    Fetches all tutorial steps for a specific song.
    (Note: The 'status' for each step is simplified to 'pending' or 'completed'
    based on overall song progress. A more complex system could track each step.)
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

    # Determine status for steps based on overall song progress
    song_progress = user_status.progress if user_status else 0
    total_steps = len(steps)
    completed_steps_count = round((song_progress / 100) * total_steps)

    # Prepare response
    response = []
    for i, step in enumerate(steps):
        step_data = step.dict()
        step_data["_id"] = str(step.id)
        step_data["status"] = "completed" if i < completed_steps_count else "pending"
        response.append(TutorialStepResponse(**step_data))

    return response
