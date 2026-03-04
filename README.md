# Movement Efficiency Pipeline — Backend

FastAPI backend for a real-time gait monitoring dashboard. Streams live movement metrics over WebSocket and persists session history to Supabase.

**Live API:** https://web-production-43f13.up.railway.app/health

---

## Stack
- **FastAPI** — web framework
- **uvicorn** — ASGI server
- **asyncio** — concurrent WebSocket send/receive
- **Supabase** — PostgreSQL database
- **Python 3.11**

---

## API

**WebSocket** `WS /ws` — streams one metrics packet per second

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server + database health check |
| `POST` | `/api/sessions` | Save a completed session |
| `GET` | `/api/sessions` | List all sessions |
| `GET` | `/api/sessions/{id}` | Get one session with full detail |
| `DELETE` | `/api/sessions/{id}` | Delete a session |

---

## MEI Formula
cadence×0.20 + symmetry×0.35 + impact×0.20 + smoothness×0.25

## Data Layer

`generator.py` simulates patient gait data using profile-based baselines with ±3% random noise to mimic real IMU sensor fluctuation. In production this would be replaced by a real sensor integration and ML inference layer — the WebSocket output schema stays identical so nothing else in the stack changes.
