import os
import cv2
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import mediapipe as mp
from static_pose_comparision.pose_utils import (
    extract_keypoints_and_angles,
    get_max_angle_difference,
    normalize_skeleton,
    calculate_angles_from_keypoints
)

router = APIRouter()

# --- Constants ---
REFERENCE_POSE_FOLDER = "static_pose_comparision/reference_poses"
POSE_IMAGES = sorted([f for f in os.listdir(REFERENCE_POSE_FOLDER) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
ACCURACY_THRESHOLD_PERCENT = 80 # Threshold to advance to the next pose
MAX_ANGLE_DIFFERENCE_FOR_ACCURACY = 40 # The max possible angle diff that still gives some accuracy score

# --- Load Reference Poses on Startup ---
mp_pose = mp.solutions.pose.Pose(static_image_mode=True, min_detection_confidence=0.5)

REFERENCE_POSES = []
for img_name in POSE_IMAGES:
    img_path = os.path.join(REFERENCE_POSE_FOLDER, img_name)
    img = cv2.imread(img_path)
    if img is not None:
        # Extract and store normalized keypoints (0-1 range) and angles
        _, keypoints, angles = extract_keypoints_and_angles(img, mp_pose, use_pixel_coordinates=False)
        if keypoints and angles:
            REFERENCE_POSES.append({"keypoints": keypoints, "angles": angles, "name": img_name})
    else:
        print(f"Warning: Could not read image {img_path}")

mp_pose.close() # No longer needed after initialization

print(f"Loaded {len(REFERENCE_POSES)} reference poses.")

# --- WebSocket Endpoint ---
@router.websocket("/ws/pose")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    current_pose_index = 0

    try:
        while True:
            if not REFERENCE_POSES:
                await ws.send_json({"error": "No reference poses loaded on the server."})
                break

            ref_pose = REFERENCE_POSES[current_pose_index]
            ref_keypoints = ref_pose["keypoints"]
            ref_angles = ref_pose["angles"]

            data = await ws.receive_json()
            user_landmarks = data.get("landmarks")

            if not user_landmarks:
                await ws.send_json({
                    "accuracy": 0,
                    "feedback": "No person detected.",
                    "current_pose": ref_pose["name"]
                })
                continue

            user_keypoints = {i: (lm['x'], lm['y']) for i, lm in enumerate(user_landmarks)}
            normalized_user_keypoints = normalize_skeleton(user_keypoints, ref_keypoints)
            user_angles = calculate_angles_from_keypoints(normalized_user_keypoints)

            # --- Get max angle difference ---
            max_diff_name, max_diff = get_max_angle_difference(user_angles, ref_angles)

            # --- Calculate overall accuracy ---
            total_diff = sum(abs(user_angles.get(name, 0) - ref_val) for name, ref_val in ref_angles.items())
            count = len(ref_angles)
            avg_diff = total_diff / count if count else MAX_ANGLE_DIFFERENCE_FOR_ACCURACY
            accuracy = max(0, 100 - (avg_diff / MAX_ANGLE_DIFFERENCE_FOR_ACCURACY) * 100)

            # --- Feedback ---
            if accuracy > 90:
                feedback = "Great job! Hold the pose."
            elif max_diff_name:
                feedback = f"Focus on your {max_diff_name.replace('_', ' ')}."
            else:
                feedback = "Align with the pose."

            # --- Check if next pose should be triggered ---
            next_pose_triggered = False
            if accuracy >= ACCURACY_THRESHOLD_PERCENT:
                current_pose_index = (current_pose_index + 1) % len(REFERENCE_POSES)
                next_pose_triggered = True
                feedback = "Excellent! Moving to the next pose."

            await ws.send_json({
                "accuracy": round(accuracy, 2),
                "feedback": feedback,
                "next_pose": next_pose_triggered,
                "current_pose": REFERENCE_POSES[current_pose_index]["name"]
            })

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await ws.close()
