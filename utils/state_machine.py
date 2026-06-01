"""Generic two-phase and three-phase rep-counting state machines."""
from enum import Enum, auto


class RepState(Enum):
    START = auto()
    PHASE_1 = auto()   # e.g. eccentric / down
    PHASE_2 = auto()   # e.g. concentric / up
    PHASE_3 = auto()   # optional third phase (e.g. isometric hold)


class RepCounter:
    """
    Two-phase rep counter.

    A rep is counted when the machine transitions:
        START -> PHASE_1 -> PHASE_2 -> START
    """

    def __init__(self, phase1_threshold, phase2_threshold, hysteresis=5.0):
        self.p1_thresh = phase1_threshold   # angle to enter phase 1
        self.p2_thresh = phase2_threshold   # angle to enter phase 2 (complete rep)
        self.hysteresis = hysteresis
        self.state = RepState.START
        self.reps = 0
        self.history = []

    def update(self, angle):
        self.history.append(round(angle, 2))
        if len(self.history) > 30:
            self.history.pop(0)

        if self.state == RepState.START:
            if angle < self.p1_thresh:
                self.state = RepState.PHASE_1

        elif self.state == RepState.PHASE_1:
            if angle > self.p2_thresh - self.hysteresis:
                self.state = RepState.PHASE_2

        elif self.state == RepState.PHASE_2:
            if angle < self.p1_thresh + self.hysteresis:
                self.reps += 1
                self.state = RepState.START

        return self.reps, self.state


class ThreePhaseRepCounter:
    """
    Three-phase rep counter (e.g. squat: standing -> parallel -> bottom -> parallel -> standing).
    Phases: START -> DESCENT -> BOTTOM -> ASCENT -> START (counts on return to START)
    """

    def __init__(self, descent_thresh, bottom_thresh, ascent_thresh, hysteresis=5.0):
        self.descent_thresh = descent_thresh
        self.bottom_thresh = bottom_thresh
        self.ascent_thresh = ascent_thresh
        self.hysteresis = hysteresis
        self.state = RepState.START
        self.reps = 0

    def update(self, angle):
        if self.state == RepState.START:
            if angle < self.descent_thresh:
                self.state = RepState.PHASE_1   # descending

        elif self.state == RepState.PHASE_1:    # descending
            if angle < self.bottom_thresh:
                self.state = RepState.PHASE_2   # at bottom

        elif self.state == RepState.PHASE_2:    # at bottom
            if angle > self.bottom_thresh + self.hysteresis:
                self.state = RepState.PHASE_3   # ascending

        elif self.state == RepState.PHASE_3:    # ascending
            if angle > self.ascent_thresh:
                self.reps += 1
                self.state = RepState.START

        return self.reps, self.state
