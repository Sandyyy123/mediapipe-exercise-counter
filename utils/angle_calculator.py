"""Joint angle calculation from MediaPipe landmark coordinates."""
import numpy as np


def get_landmark_coords(landmarks, index):
    """Return (x, y, z) from a landmark list by index."""
    lm = landmarks[index]
    return np.array([lm.x, lm.y, lm.z])


def calculate_angle(a, b, c):
    """
    Calculate angle at joint B formed by points A-B-C.
    All points are numpy arrays (x, y, z). Returns degrees.
    """
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
    cosine = np.clip(cosine, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def joint_angle(landmarks, idx_a, idx_b, idx_c):
    """Convenience wrapper: compute angle at landmark idx_b."""
    a = get_landmark_coords(landmarks, idx_a)
    b = get_landmark_coords(landmarks, idx_b)
    c = get_landmark_coords(landmarks, idx_c)
    return calculate_angle(a, b, c)
