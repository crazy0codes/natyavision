import cv2
import mediapipe as mp
import os
import time
import numpy as np
from collections import deque
from pose_utils import extract_keypoints_and_angles, get_max_angle_difference

# ---------------------- Config ----------------------
REFERENCE_POSE_FOLDER = "reference_poses"
ERROR_THRESHOLD_DEGREES = 20
ACCURACY_THRESHOLD_PERCENT = 70
HOLD_TIME_SECONDS = 1.0
ACCURACY_MAX_DIFF = 35
REF_DISPLAY_SIZE = (150, 200)
SMOOTHING_WINDOW = 5

JOINT_WEIGHTS = {
    "left_elbow": 1.5,
    "right_elbow": 1.5,
    "left_knee": 2.0,
    "right_knee": 2.0,
    "left_shoulder": 1.0,
    "right_shoulder": 1.0,
}

angle_history = {}
ref_angles_list = []
ref_images_list = []
ref_keypoints_list = []
current_pose_index = 0
match_start_time = None
pose = mp.solutions.pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# ---------------------- Smoothing ----------------------
def smooth_angle(name, new_val):
    if name not in angle_history:
        angle_history[name] = deque(maxlen=SMOOTHING_WINDOW)
    angle_history[name].append(new_val)
    return np.mean(angle_history[name])

# ---------------------- Accuracy ----------------------
def calculate_overall_accuracy(live_angles, ref_angles):
    total_score = 0.0
    total_weight = 0.0

    for name, ref_val in ref_angles.items():
        live_val = live_angles.get(name)
        if live_val is None: continue
        diff = abs(live_val - ref_val)
        capped_diff = min(diff, ACCURACY_MAX_DIFF)
        score = max(0, ACCURACY_MAX_DIFF - capped_diff)
        weight = JOINT_WEIGHTS.get(name, 1.0)
        total_score += score * weight
        total_weight += ACCURACY_MAX_DIFF * weight

    return max(0.0, min(100.0, (total_score / total_weight) * 100)) if total_weight > 0 else 0.0

# ---------------------- Load references ----------------------
def setup_reference_poses():
    global ref_angles_list, ref_images_list, ref_keypoints_list
    if not os.path.exists(REFERENCE_POSE_FOLDER):
        os.makedirs(REFERENCE_POSE_FOLDER)
        print("Add reference images first.")
        return False

    image_files = sorted([f for f in os.listdir(REFERENCE_POSE_FOLDER) if f.lower().endswith((".png",".jpg",".jpeg"))])
    if not image_files: return False

    ref_angles_list.clear()
    ref_images_list.clear()
    ref_keypoints_list.clear()

    for filename in image_files:
        img = cv2.imread(os.path.join(REFERENCE_POSE_FOLDER, filename))
        if img is None: continue
        ref_images_list.append(cv2.resize(img, REF_DISPLAY_SIZE))
        _, keypoints, angles = extract_keypoints_and_angles(img, pose)
        ref_keypoints_list.append(keypoints)
        ref_angles_list.append(angles)

    print(f"Loaded {len(ref_images_list)} reference poses.")
    return True

# ---------------------- Main ----------------------
def main():
    global current_pose_index, match_start_time

    if not setup_reference_poses(): return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened(): return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: continue
        frame = cv2.flip(frame, 1)

        if current_pose_index >= len(ref_angles_list):
            cv2.putText(frame, "Workout Complete!", (50, frame.shape[0]//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0),2)
            cv2.imshow("Live Pose Comparison", frame)
            cv2.waitKey(2000)
            break

        ref_angles = ref_angles_list[current_pose_index]
        ref_keypoints = ref_keypoints_list[current_pose_index]
        ref_image = ref_images_list[current_pose_index]

        image, keypoints, live_angles_raw = extract_keypoints_and_angles(frame, pose, ref_keypoints)
        live_angles = {name: smooth_angle(name, val) for name, val in live_angles_raw.items() if val is not None}

        current_accuracy = calculate_overall_accuracy(live_angles, ref_angles)
        max_diff_name, max_diff = get_max_angle_difference(live_angles, ref_angles)

        feedback_text = ""
        if current_accuracy >= ACCURACY_THRESHOLD_PERCENT:
            if match_start_time is None: match_start_time = time.time()
            held_time = time.time() - match_start_time
            if held_time >= HOLD_TIME_SECONDS:
                current_pose_index += 1
                match_start_time = None
                continue
            else:
                feedback_text = f"HOLDING: {HOLD_TIME_SECONDS - held_time:.1f}s remaining"
        else:
            match_start_time = None
            if max_diff_name and max_diff > ERROR_THRESHOLD_DEGREES:
                feedback_text = f"ADJUST {max_diff_name} (Error: {max_diff:.1f}°)"
            else:
                feedback_text = "Keep going!"

        # Overlay reference image
        h_ref, w_ref = ref_image.shape[:2]
        h_live, w_live = image.shape[:2]
        image[10:10+h_ref, w_live-10-w_ref:w_live-10] = ref_image
        cv2.putText(image, "Target Pose", (w_live-10-w_ref, 10+h_ref+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255),1)

        # Feedback
        cv2.putText(image, f"POSE {current_pose_index+1}/{len(ref_angles_list)}", (10,30), cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)
        cv2.putText(image, f"ACCURACY: {current_accuracy:.1f}%", (10,70), cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0) if current_accuracy>=ACCURACY_THRESHOLD_PERCENT else (0,255,255),2)
        cv2.putText(image, feedback_text, (10,image.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,255) if "ADJUST" in feedback_text else (0,255,0),2)

        cv2.imshow("Live Pose Comparison", image)
        if cv2.waitKey(5) & 0xFF == ord("q"): break

    cap.release()
    cv2.destroyAllWindows()
    pose.close()

if __name__ == "__main__":
    main()
