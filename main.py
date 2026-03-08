import asyncio
import json
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from generator import MovementGenerator

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabase client — only initialized if env vars are present
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[WARN] Could not connect to Supabase: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_status = "connected" if supabase else "not configured (running without DB)"
    print(f"[INFO] Movement Efficiency API starting — Supabase: {db_status}")
    yield
    print("[INFO] Shutting down.")


app = FastAPI(title="Movement Efficiency API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    generator = MovementGenerator()
    print("[WS] Client connected")

    async def send_metrics():
        """Push one metrics packet per second."""
        while True:
            data = generator.generate()
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(1)

    async def receive_commands():
        """Listen for profile-change commands from the frontend."""
        while True:
            try:
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                if msg.get("action") == "change_profile":
                    profile = msg.get("profile")
                    generator.set_profile(profile)
                    print(f"[WS] Profile changed → {profile}")
                elif msg.get("action") == "ping":
                    await websocket.send_text(json.dumps({"action": "pong"}))
                    print("[WS] Ping → Pong")
            except Exception:
                break

    try:
        await asyncio.gather(send_metrics(), receive_commands())
    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    except Exception as e:
        print(f"[WS] Error: {e}")


# ─── REST: Sessions ───────────────────────────────────────────────────────────

@app.post("/api/sessions")
async def save_session(body: dict):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")

    session_payload = {
        "patient_name": body.get("patient_name"),
        "profile": body.get("profile"),
        "duration": body.get("duration"),
        "mei": body.get("mei"),
        "avg_cadence": body.get("avg_cadence"),
        "avg_symmetry": body.get("avg_symmetry"),
        "avg_impact": body.get("avg_impact"),
        "avg_smoothness": body.get("avg_smoothness"),
        "metrics_history": body.get("metrics_history", []),
    }

    result = supabase.table("sessions").insert(session_payload).execute()
    session = result.data[0]
    session_id = session["id"]

    alerts = body.get("alerts", [])
    if alerts:
        alert_rows = [
            {"session_id": session_id, "time": a["time"], "message": a["message"]}
            for a in alerts
        ]
        supabase.table("alerts").insert(alert_rows).execute()

    return {"id": session_id, "status": "saved"}


@app.get("/api/sessions")
async def list_sessions():
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")

    result = (
        supabase.table("sessions")
        .select("id, patient_name, profile, duration, mei, avg_cadence, avg_symmetry, created_at")
        .order("created_at", desc=True)
        .execute()
    )
    # Attach alert count to each session
    sessions = result.data
    for session in sessions:
        alerts_result = (
            supabase.table("alerts")
            .select("id", count="exact")
            .eq("session_id", session["id"])
            .execute()
        )
        session["alert_count"] = alerts_result.count or 0

    return sessions


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")

    result = supabase.table("sessions").select("*").eq("id", session_id).single().execute()
    session = result.data

    alerts_result = (
        supabase.table("alerts")
        .select("*")
        .eq("session_id", session_id)
        .order("time")
        .execute()
    )
    session["alerts"] = alerts_result.data

    return session


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not configured")

    supabase.table("alerts").delete().eq("session_id", session_id).execute()
    supabase.table("sessions").delete().eq("id", session_id).execute()

    return {"status": "deleted"}


@app.get("/health")
async def health():
    return {"status": "ok", "supabase": supabase is not None}
