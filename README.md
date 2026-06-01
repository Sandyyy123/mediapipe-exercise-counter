# MediaPipe Exercise Rep Counter

Real-time exercise rep counting using **MediaPipe BlazePose** (33-landmark body model). Implements joint angle thresholds, finite-state-machine rep counting, and live form feedback.

## Architecture

```
main.py                        # entry point — webcam/video loop
utils/
  angle_calculator.py          # 3D joint angle from landmark coordinates
  state_machine.py             # two-phase and three-phase rep counters
exercise_definitions/
  bicep_curl.json              # angle thresholds, form rules, edge cases
  squat.json                   # three-phase squat definition
```

## Exercises Implemented (demo)

| Exercise | Landmarks | State Machine | Primary Angle |
|---|---|---|---|
| Bicep Curl | 11-12-13-14-15-16 | Two-phase | Elbow flexion |
| Bodyweight Squat | 23-24-25-26-27-28 | Three-phase | Knee flexion |

**5 exercises ready to implement immediately:**
1. Bicep Curl — elbow flexion, landmarks 11/13/15 (shoulder-elbow-wrist)
2. Bodyweight Squat — knee flexion, landmarks 23/25/27 (hip-knee-ankle)
3. Push-up — elbow flexion + shoulder abduction, landmarks 11/13/15
4. Shoulder Press — shoulder-elbow-wrist angle in overhead plane
5. Lateral Raise — shoulder abduction angle (hip-shoulder-elbow)

## MediaPipe Landmark Model

BlazePose produces **33 keypoints** per frame, each with (x, y, z, visibility) values. Landmark index uniquely identifies a body joint — e.g. index `14` = right elbow, `26` = right knee. Joint angles are computed from three co-indexed landmarks using the law of cosines on the 3D coordinates.

## Setup

```bash
pip install -r requirements.txt
python main.py --exercise bicep_curl           # webcam
python main.py --exercise squat --video demo.mp4
```

## Schema Format

Each exercise definition is stored as JSON per the QuickPose-compatible schema:

```json
{
  "joint_angles": { ... threshold values ... },
  "rep_logic": { "state_machine": "TwoPhase|ThreePhase", ... },
  "form_feedback_rules": [ { "trigger": "...", "message": "..." } ],
  "edge_cases": [ "..." ],
  "met_value": 3.5,
  "met_source": "Ainsworth et al. 2011"
}
```

## Author

Dr. Sandeep Grover — AI/ML Engineer | groverautomationhub.lovable.app/portfolio
