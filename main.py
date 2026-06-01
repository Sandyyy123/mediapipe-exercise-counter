"""
MediaPipe BlazePose exercise rep counter — demo runner.
Reads from webcam (or a video file), overlays landmark skeleton,
counts reps for the selected exercise, and shows live form feedback.

Usage:
    python main.py --exercise bicep_curl   # webcam
    python main.py --exercise squat --video squat_demo.mp4
"""
import argparse
import json
import os
import sys

import cv2
import mediapipe as mp
import numpy as np

from utils.angle_calculator import joint_angle
from utils.state_machine import RepCounter, ThreePhaseRepCounter

# ── MediaPipe setup ───────────────────────────────────────────────────
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

LANDMARK = mp_pose.PoseLandmark


def load_exercise(name: str) -> dict:
    path = os.path.join("exercise_definitions", f"{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"No definition found for exercise: {name}")
    with open(path) as f:
        return json.load(f)


def build_counter(exercise: dict):
    """Instantiate the correct state machine from the exercise definition."""
    rep_logic = exercise["rep_logic"]
    angles = exercise["joint_angles"]
    primary = list(angles.values())[0]

    if rep_logic["state_machine"] == "TwoPhase":
        return RepCounter(
            phase1_threshold=primary["phase_2_start"],     # contracted
            phase2_threshold=primary["phase_1_start"],     # extended
        )
    else:
        return ThreePhaseRepCounter(
            descent_thresh=primary["standing_threshold"],
            bottom_thresh=primary["bottom_threshold"],
            ascent_thresh=primary["standing_threshold"],
        )


def draw_overlay(frame, landmarks, angle, reps, state, feedback):
    """Draw skeleton, angle, rep count and form feedback on frame."""
    mp_drawing.draw_landmarks(
        frame,
        landmarks,
        mp_pose.POSE_CONNECTIONS,
        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
    )
    h, w, _ = frame.shape

    # Rep counter box
    cv2.rectangle(frame, (0, 0), (220, 70), (0, 0, 0), -1)
    cv2.putText(frame, f"REPS: {reps}", (10, 45),
                cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 255, 100), 3)

    # Angle display
    cv2.putText(frame, f"Angle: {angle:.1f}deg", (10, 95),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

    # State label
    cv2.putText(frame, f"State: {state.name}", (10, 125),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (100, 200, 255), 2)

    # Form feedback
    for i, msg in enumerate(feedback[:3]):
        cv2.putText(frame, f"! {msg}", (10, h - 80 + i * 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 80, 255), 2)

    return frame


def check_form(landmarks_list, exercise: dict) -> list:
    """Evaluate form feedback rules — returns list of active warning messages."""
    warnings = []
    for rule in exercise.get("form_feedback_rules", []):
        # Elbow drift rule (bicep curl)
        if rule["rule_id"] == "elbow_drift":
            try:
                elbow = landmarks_list[LANDMARK.RIGHT_ELBOW.value]
                hip = landmarks_list[LANDMARK.RIGHT_HIP.value]
                if abs(elbow.x - hip.x) > 0.12:
                    warnings.append(rule["message"])
            except Exception:
                pass
        # Knee cave rule (squat)
        elif rule["rule_id"] == "knee_cave":
            try:
                lk = landmarks_list[LANDMARK.LEFT_KNEE.value]
                rk = landmarks_list[LANDMARK.RIGHT_KNEE.value]
                lh = landmarks_list[LANDMARK.LEFT_HIP.value]
                rh = landmarks_list[LANDMARK.RIGHT_HIP.value]
                hip_w = abs(lh.x - rh.x)
                knee_w = abs(lk.x - rk.x)
                if hip_w > 0 and knee_w / hip_w < 0.85:
                    warnings.append(rule["message"])
            except Exception:
                pass
    return warnings


def get_primary_angle(landmarks_list, exercise: dict) -> float:
    """Calculate the primary joint angle for the exercise."""
    angles = exercise["joint_angles"]
    name = list(angles.keys())[0]
    lm_used = exercise["landmarks_used"]

    if name == "elbow_flexion":
        # Use right arm landmarks
        return joint_angle(landmarks_list,
                           LANDMARK.RIGHT_SHOULDER.value,
                           LANDMARK.RIGHT_ELBOW.value,
                           LANDMARK.RIGHT_WRIST.value)
    elif name == "knee_flexion":
        return joint_angle(landmarks_list,
                           LANDMARK.RIGHT_HIP.value,
                           LANDMARK.RIGHT_KNEE.value,
                           LANDMARK.RIGHT_ANKLE.value)
    return 0.0


def run(exercise_name: str, video_source):
    exercise = load_exercise(exercise_name)
    counter = build_counter(exercise)
    cap = cv2.VideoCapture(video_source)

    print(f"Running: {exercise['display_name']} | Press Q to quit")

    with mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            angle = 0.0
            feedback = []

            if results.pose_landmarks:
                lm_list = results.pose_landmarks.landmark
                angle = get_primary_angle(lm_list, exercise)
                reps, state = counter.update(angle)
                feedback = check_form(lm_list, exercise)
                frame = draw_overlay(frame, results.pose_landmarks, angle, reps, state, feedback)

            cv2.imshow(f"MediaPipe — {exercise['display_name']}", frame)
            if cv2.waitKey(10) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Final rep count: {counter.reps}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--exercise", default="bicep_curl", help="Exercise name (matches JSON filename)")
    parser.add_argument("--video", default=0, help="Video path or 0 for webcam")
    args = parser.parse_args()
    video_src = args.video if args.video == 0 else args.video
    run(args.exercise, video_src)
