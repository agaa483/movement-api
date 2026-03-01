"""
Quick WebSocket smoke test.
Run:  python test_ws.py
Connects to ws://localhost:8000/ws, prints 5 metric packets,
then sends a profile-change command and prints 3 more.
"""

import asyncio
import json
import websockets


async def main():
    url = "ws://localhost:8000/ws"
    print(f"Connecting to {url} …\n")

    async with websockets.connect(url) as ws:
        print("=== Initial 5 packets (normal_walk_recovery) ===")
        for i in range(5):
            raw = await ws.recv()
            data = json.loads(raw)
            print(
                f"[{i+1}] cadence={data['cadence']} spm  "
                f"symmetry={data['symmetry']}%  "
                f"impact={data['impact']}g  "
                f"smoothness={data['smoothness']}  "
                f"MEI={data['mei']}  "
                f"alerts={data['alerts']}"
            )

        print("\n=== Sending change_profile → compensating_gait ===\n")
        await ws.send(json.dumps({"action": "change_profile", "profile": "compensating_gait"}))

        print("=== Next 3 packets (compensating_gait) ===")
        for i in range(3):
            raw = await ws.recv()
            data = json.loads(raw)
            print(
                f"[{i+1}] cadence={data['cadence']} spm  "
                f"symmetry={data['symmetry']}%  "
                f"impact={data['impact']}g  "
                f"smoothness={data['smoothness']}  "
                f"MEI={data['mei']}  "
                f"alerts={data['alerts']}"
            )

    print("\nWebSocket test complete.")


if __name__ == "__main__":
    asyncio.run(main())
