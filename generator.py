import random
import time


PROFILES = {
    "normal_walk_recovery": {
        "cadence": 110,
        "symmetry": 50,
        "impact": 1.2,
        "smoothness": 92,
    },
    "normal_run_recovery": {
        "cadence": 170,
        "symmetry": 50,
        "impact": 2.0,
        "smoothness": 88,
    },
    "compensating_gait": {
        "cadence": 145,
        "symmetry": 62,
        "impact": 3.5,
        "smoothness": 58,
    },
    "post_exercise_fatigue": {
        # Starts normal-ish, degrades toward these values over time
        "cadence": 155,
        "symmetry": 58,
        "impact": 3.5,
        "smoothness": 63,
    },
}

# Ideal cadence for scoring purposes (walking)
IDEAL_CADENCE = 110


def _jitter(value: float, pct: float = 0.03) -> float:
    """Add small random noise (±pct of value) to simulate sensor variation."""
    return value + random.uniform(-value * pct, value * pct)


def _cadence_score(cadence: float) -> float:
    """Score cadence 0-100 based on closeness to ideal."""
    deviation = abs(cadence - IDEAL_CADENCE)
    score = max(0.0, 100.0 - deviation * 1.2)
    return min(100.0, score)


def _symmetry_score(symmetry: float) -> float:
    """Score symmetry 0-100 where 50% = perfect (100)."""
    deviation = abs(symmetry - 50.0)
    score = max(0.0, 100.0 - deviation * 4.0)
    return min(100.0, score)


def _impact_score(impact: float) -> float:
    """Score impact 0-100 where lower impact = higher score."""
    score = max(0.0, 100.0 - (impact - 1.0) * 25.0)
    return min(100.0, score)


def _compute_mei(cadence: float, symmetry: float, impact: float, smoothness: float) -> float:
    cs = _cadence_score(cadence)
    ss = _symmetry_score(symmetry)
    is_ = _impact_score(impact)
    mei = cs * 0.20 + ss * 0.35 + is_ * 0.20 + smoothness * 0.25
    return round(min(100.0, max(0.0, mei)), 1)


def _detect_alerts(symmetry: float, impact: float, smoothness: float, mei: float) -> list[str]:
    alerts = []
    if symmetry < 45 or symmetry > 55:
        alerts.append("Gait asymmetry detected")
    if impact > 3.0:
        alerts.append("Impact spike detected")
    if smoothness < 65:
        alerts.append("Movement irregularity detected")
    if mei < 70:
        alerts.append("MEI below threshold")
    return alerts


class MovementGenerator:
    def __init__(self):
        self._profile = "normal_walk_recovery"
        self._start_time = time.time()
        self._elapsed = 0

    def set_profile(self, profile: str) -> None:
        if profile not in PROFILES:
            raise ValueError(f"Unknown profile: {profile}")
        self._profile = profile
        self._start_time = time.time()
        self._elapsed = 0

    def generate(self) -> dict:
        self._elapsed = time.time() - self._start_time
        base = PROFILES[self._profile]

        if self._profile == "post_exercise_fatigue":
            metrics = self._generate_fatigue(base)
        else:
            metrics = {
                "cadence": _jitter(base["cadence"]),
                "symmetry": _jitter(base["symmetry"]),
                "impact": _jitter(base["impact"], pct=0.05),
                "smoothness": _jitter(base["smoothness"]),
            }

        cadence = round(metrics["cadence"], 1)
        symmetry = round(metrics["symmetry"], 1)
        impact = round(metrics["impact"], 2)
        smoothness = round(metrics["smoothness"], 1)
        mei = _compute_mei(cadence, symmetry, impact, smoothness)
        alerts = _detect_alerts(symmetry, impact, smoothness, mei)

        return {
            "cadence": cadence,
            "symmetry": symmetry,
            "impact": impact,
            "smoothness": smoothness,
            "mei": mei,
            "alerts": alerts,
            "profile": self._profile,
            "elapsed": round(self._elapsed, 1),
        }

    def _generate_fatigue(self, base: dict) -> dict:
        """Degrade metrics linearly over 120 seconds toward fatigued values."""
        # Start values (normal walk)
        start = PROFILES["normal_walk_recovery"]
        progress = min(1.0, self._elapsed / 120.0)

        cadence = start["cadence"] + (base["cadence"] - start["cadence"]) * progress
        symmetry = start["symmetry"] + (base["symmetry"] - start["symmetry"]) * progress
        impact = start["impact"] + (base["impact"] - start["impact"]) * progress
        smoothness = start["smoothness"] + (base["smoothness"] - start["smoothness"]) * progress

        return {
            "cadence": _jitter(cadence),
            "symmetry": _jitter(symmetry),
            "impact": _jitter(impact, pct=0.05),
            "smoothness": _jitter(smoothness),
        }
