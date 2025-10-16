import cv2
import mediapipe as mp
import numpy as np

# MediaPipe pose solution
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Define the angles to be calculated
# These are tuples of landmarks that form the angle, with the vertex in the middle
ANGLE_DEFINITIONS = {
    "left_elbow": (mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_ELBOW, mp_pose.PoseLandmark.LEFT_WRIST),
    "right_elbow": (mp_pose.PoseLandmark.RIGHT_SHOULDER, mp_pose.PoseLandmark.RIGHT_ELBOW, mp_pose.PoseLandmark.RIGHT_WRIST),
    "left_shoulder": (mp_pose.PoseLandmark.LEFT_ELBOW, mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_HIP),
    "right_shoulder": (mp_pose.PoseLandmark.RIGHT_ELBOW, mp_pose.PoseLandmark.RIGHT_SHOULDER, mp_pose.PoseLandmark.RIGHT_HIP),
    "left_knee": (mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.LEFT_KNEE, mp_pose.PoseLandmark.LEFT_ANKLE),
    "right_knee": (mp_pose.PoseLandmark.RIGHT_HIP, mp_pose.PoseLandmark.RIGHT_KNEE, mp_pose.PoseLandmark.RIGHT_ANKLE),
}

def calculate_angle(a, b, c):
    """Calculates the angle between three 2D points."""
    a = np.array(a)  # First point
    b = np.array(b)  # Mid point (vertex)
    c = np.array(c)  # End point

    # Calculate vectors
    ba = a - b
    bc = c - b

    # Ensure vectors are not zero length
    if np.linalg.norm(ba) == 0 or np.linalg.norm(bc) == 0:
        return None

    # Calculate cosine of the angle
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    
    # Clip value to avoid errors due to floating point inaccuracies
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    
    # Calculate angle in degrees
    angle = np.degrees(np.arccos(cosine_angle))
    return angle

def normalize_skeleton(user_keypoints, ref_keypoints):
    """
    FIX: A more robust normalization using the torso center and size.
    This is crucial for accurate angle comparison, regardless of user's distance from camera.
    """
    # Helper to get a point or return a default
    def get_point(keypoints, landmark, default=(0,0)):
        return keypoints.get(landmark.value, default)

    # Calculate hip and shoulder centers for both skeletons
    user_left_hip = get_point(user_keypoints, mp_pose.PoseLandmark.LEFT_HIP)
    user_right_hip = get_point(user_keypoints, mp_pose.PoseLandmark.RIGHT_HIP)
    user_hip_center = np.array([(user_left_hip[0] + user_right_hip[0]) / 2, (user_left_hip[1] + user_right_hip[1]) / 2])
    
    ref_left_hip = get_point(ref_keypoints, mp_pose.PoseLandmark.LEFT_HIP)
    ref_right_hip = get_point(ref_keypoints, mp_pose.PoseLandmark.RIGHT_HIP)
    ref_hip_center = np.array([(ref_left_hip[0] + ref_right_hip[0]) / 2, (ref_left_hip[1] + ref_right_hip[1]) / 2])
    
    user_left_shoulder = get_point(user_keypoints, mp_pose.PoseLandmark.LEFT_SHOULDER)
    user_right_shoulder = get_point(user_keypoints, mp_pose.PoseLandmark.RIGHT_SHOULDER)
    user_shoulder_center = np.array([(user_left_shoulder[0] + user_right_shoulder[0]) / 2, (user_left_shoulder[1] + user_right_shoulder[1]) / 2])

    ref_left_shoulder = get_point(ref_keypoints, mp_pose.PoseLandmark.LEFT_SHOULDER)
    ref_right_shoulder = get_point(ref_keypoints, mp_pose.PoseLandmark.RIGHT_SHOULDER)
    ref_shoulder_center = np.array([(ref_left_shoulder[0] + ref_right_shoulder[0]) / 2, (ref_left_shoulder[1] + ref_right_shoulder[1]) / 2])

    # Translate user skeleton to origin (based on hip center)
    translated_kps = {idx: np.array(pt) - user_hip_center for idx, pt in user_keypoints.items()}

    # Calculate scaling factor based on torso length (distance between shoulder and hip centers)
    ref_torso_length = np.linalg.norm(ref_shoulder_center - ref_hip_center)
    user_torso_length = np.linalg.norm(user_shoulder_center - user_hip_center)
    
    scale_factor = ref_torso_length / user_torso_length if user_torso_length > 0 else 1.0
    
    # Scale and translate to reference position
    normalized_kps = {idx: pt * scale_factor + ref_hip_center for idx, pt in translated_kps.items()}
    return normalized_kps

def calculate_angles_from_keypoints(keypoints):
    """Calculates all defined angles from a dictionary of keypoints."""
    angles = {}
    for name, landmarks in ANGLE_DEFINITIONS.items():
        p1, p2, p3 = landmarks
        # Ensure all landmarks for the angle are present
        if p1.value in keypoints and p2.value in keypoints and p3.value in keypoints:
            angles[name] = calculate_angle(keypoints[p1.value], keypoints[p2.value], keypoints[p3.value])
    return angles

def get_max_angle_difference(live_angles, ref_angles):
    """Finds the joint with the largest angle difference."""
    max_diff = 0
    max_name = None
    for name, ref_val in ref_angles.items():
        live_val = live_angles.get(name)
        if live_val is not None and ref_val is not None:
            diff = abs(live_val - ref_val)
            if diff > max_diff:
                max_diff = diff
                max_name = name
    return max_name, max_diff

def extract_keypoints_and_angles(image, pose, use_pixel_coordinates=True):
    """
    Processes an image to extract pose keypoints and angles.
    Set `use_pixel_coordinates` to False to get normalized (0-1) coordinates.
    """
    # To improve performance, optionally mark the image as not writeable to
    # pass by reference.
    image.flags.writeable = False
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)
    image.flags.writeable = True

    if not results.pose_landmarks:
        return None, None, None

    landmarks = results.pose_landmarks.landmark
    h, w, _ = image.shape
    
    keypoints = {}
    for idx, lm in enumerate(landmarks):
        if use_pixel_coordinates:
            keypoints[idx] = (int(lm.x * w), int(lm.y * h))
        else:
            keypoints[idx] = (lm.x, lm.y)

    angles = calculate_angles_from_keypoints(keypoints)
    
    return results.pose_landmarks, keypoints, angles

