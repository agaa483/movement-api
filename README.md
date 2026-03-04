Movement Efficiency Pipeline — Backend
FastAPI backend for the real-time gait monitoring dashboard. Streams live movement metrics over WebSocket and persists session history to Supabase.

Live API: https://web-production-43f13.up.railway.app/health

What it does
Streams one gait metrics packet per second over WebSocket
Computes a Movement Efficiency Index (MEI) score from four metrics
Detects gait anomalies and fires alerts in real time
Saves and retrieves session history via REST endpoints backed by Supabase
Stack
FastAPI — web framework
uvicorn — ASGI server
asyncio — concurrent WebSocket send/receive
Supabase — PostgreSQL database
Python 3.11
API
WebSocket WS /ws — streams one packet per second

REST Endpoints:

GET /health — server and database health check
POST /api/sessions — save a completed session
GET /api/sessions — list all sessions
GET /api/sessions/{id} — get one session with full detail
DELETE /api/sessions/{id} — delete a session
MEI Formula
MEI = cadence×0.20 + symmetry×0.35 + impact×0.20 + smoothness×0.25

Symmetry is weighted highest — asymmetric gait is the most clinically significant warning sign.

Data layer
generator.py simulates patient gait data using profile-based baselines with ±3% random noise to mimic real sensor fluctuation. In production this file would be replaced by a real IMU sensor integration and an ML inference layer. The WebSocket output schema stays identical so nothing else in the stack changes.
