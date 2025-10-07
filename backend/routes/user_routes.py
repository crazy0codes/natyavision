from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from bson import ObjectId
from datetime import datetime

from models import User, Song, UserSongStatus, UserStatusUpdate, UserStatusResponse, UpdateSuccessResponse
from auth import get_current_user_id

router = APIRouter()

@router.get("/status", response_model=List[UserStatusResponse])
async def get_user_song_statuses(current_user_id: str = Depends(get_current_user_id)):
    """
    Fetches all song progress records for the currently logged-in user.
    """
    statuses = await UserSongStatus.find(
        UserSongStatus.user.id == ObjectId(current_user_id)
    ).project(UserStatusResponse).to_list()

    # We need to fetch song and dance style names
    response = []
    for status_doc in statuses:
        # Fetch related song and then its dance style
        song_with_style = await Song.get(status_doc.song.id, fetch_links=True)
        if song_with_style:
            response.append(
                UserStatusResponse(
                    song_name=song_with_style.name,
                    dance_name=song_with_style.dance_style.dance_name,
                    status=status_doc.status,
                    progress=status_doc.progress,
                )
            )
    return response

@router.patch("/status/{song_id}", response_model=UpdateSuccessResponse)
async def update_user_song_status(
    song_id: str, 
    update_data: UserStatusUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Updates the progress or status for a specific song for the logged-in user.
    If no status record exists for this user and song, it creates one.
    """
    if not ObjectId.is_valid(song_id):
        raise HTTPException(status_code=400, detail="Invalid song_id format")

    # Find the existing status record or create a new one
    user_status = await UserSongStatus.find_one(
        UserSongStatus.user.id == ObjectId(current_user_id),
        UserSongStatus.song.id == ObjectId(song_id)
    )

    if not user_status:
        # Ensure user and song exist before creating a new status
        user = await User.get(current_user_id)
        song = await Song.get(song_id)
        if not user or not song:
            raise HTTPException(status_code=404, detail="User or Song not found")
        
        user_status = UserSongStatus(user=user, song=song)

    # Update fields if they are provided in the request
    if update_data.status is not None:
        user_status.status = update_data.status
    if update_data.progress is not None:
        user_status.progress = update_data.progress
    
    user_status.last_accessed = datetime.utcnow()
    
    await user_status.save()

    return UpdateSuccessResponse(message="Progress updated successfully", status="success")
