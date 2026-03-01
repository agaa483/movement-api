"""
Seed script — populates Supabase with demo session data.

Usage:
    python seed.py

Requires SUPABASE_URL and SUPABASE_KEY in .env (or environment).
"""

import os
import random
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env")
    sys.exit(1)

from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def jitter(v: float, pct: float = 0.03) -> float:
    return v + random.uniform(-v * pct, v * pct)


def cadence_score(c): return max(0, min(100, 100 - abs(c - 110) * 1.2))
def symmetry_score(s): return max(0, min(100, 100 - abs(s - 50) * 4))
def impact_score(i): return max(0, min(100, 100 - (i - 1) * 25))


def mei(cadence, symmetry, impact, smoothness):
    return round(
        cadence_score(cadence) * 0.20
        + symmetry_score(symmetry) * 0.35
        + impact_score(impact) * 0.20
        + smoothness * 0.25,
        1
    )


def detect_alerts(symmetry, impact, smoothness, mei_val):
    out = []
    if symmetry < 45 or symmetry > 55:
        out.append("Gait asymmetry detected")
    if impact > 3.0:
        out.append("Impact spike detected")
    if smoothness < 65:
        out.append("Movement irregularity detected")
    if mei_val < 70:
        out.append("MEI below threshold")
    return out


def build_session(
    patient_name: str,
    profile: str,
    base_cadence: float,
    base_symmetry: float,
    base_impact: float,
    base_smoothness: float,
    duration: int = 60,
    created_offset_days: int = 0,
):
    history = []
    all_alerts = []

    for t in range(duration):
        c = jitter(base_cadence)
        s = jitter(base_symmetry)
        i = jitter(base_impact, pct=0.05)
        sm = jitter(base_smoothness)
        m = mei(c, s, i, sm)

        history.append({
            "time": t,
            "cadence": round(c, 1),
            "symmetry": round(s, 1),
            "impact": round(i, 2),
            "smoothness": round(sm, 1),
            "mei": m,
        })

        for msg in detect_alerts(s, i, sm, m):
            if not all_alerts or all_alerts[-1]["message"] != msg:
                all_alerts.append({"time": t, "message": msg})

    avg = lambda key: round(sum(h[key] for h in history) / len(history), 2)

    created_at = (
        datetime.now(timezone.utc) - timedelta(days=created_offset_days)
    ).isoformat()

    return {
        "session": {
            "patient_name": patient_name,
            "profile": profile,
            "duration": duration,
            "mei": avg("mei"),
            "avg_cadence": avg("cadence"),
            "avg_symmetry": avg("symmetry"),
            "avg_impact": avg("impact"),
            "avg_smoothness": avg("smoothness"),
            "metrics_history": history,
            "created_at": created_at,
        },
        "alerts": all_alerts,
    }


# ─── Demo Sessions ─────────────────────────────────────────────────────────────

DEMO_SESSIONS = [
    dict(
        patient_name="PT-0042 (Sarah M.)",
        profile="normal_walk_recovery",
        base_cadence=110,
        base_symmetry=50,
        base_impact=1.2,
        base_smoothness=92,
        duration=60,
        created_offset_days=3,
    ),
    dict(
        patient_name="PT-0017 (James R.)",
        profile="normal_run_recovery",
        base_cadence=170,
        base_symmetry=50,
        base_impact=2.0,
        base_smoothness=88,
        duration=60,
        created_offset_days=2,
    ),
    dict(
        patient_name="PT-0031 (Maria L.)",
        profile="compensating_gait",
        base_cadence=145,
        base_symmetry=62,
        base_impact=3.5,
        base_smoothness=58,
        duration=60,
        created_offset_days=1,
    ),
    dict(
        patient_name="PT-0055 (David K.)",
        profile="post_exercise_fatigue",
        base_cadence=145,
        base_symmetry=55,
        base_impact=2.8,
        base_smoothness=70,
        duration=60,
        created_offset_days=0,
    ),
]


def main():
    print("Seeding Supabase with demo sessions…\n")

    for params in DEMO_SESSIONS:
        data = build_session(**params)
        session = data["session"]
        alerts = data["alerts"]

        print(f"  → Inserting session for {session['patient_name']} ({session['profile']}) …")
        result = supabase.table("sessions").insert(session).execute()
        session_id = result.data[0]["id"]

        if alerts:
            alert_rows = [
                {"session_id": session_id, "time": a["time"], "message": a["message"]}
                for a in alerts
            ]
            supabase.table("alerts").insert(alert_rows).execute()

        mei_val = session["mei"]
        print(f"     Saved (id={session_id[:8]}…, MEI={mei_val}, alerts={len(alerts)})")

    print("\nSeed complete.")


if __name__ == "__main__":
    main()
