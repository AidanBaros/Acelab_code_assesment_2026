"""Web server for the Material Recommendation Agent."""

import argparse
import asyncio
import json
import threading
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, StreamingResponse

load_dotenv()

from agent import run_agent  # noqa: E402

# ---------------------------------------------------------------------------
# CLI args — parsed at startup, used by all requests
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser(description="Acelab Material Recommendation Agent")
parser.add_argument(
    "--dev",
    action="store_true",
    help="Dev mode: hide confidence scores and technical stats from recommendations",
)
args = parser.parse_args()
DEV_MODE: bool = args.dev

app = FastAPI(title="Acelab Material Agent")


def _stream_agent(query: str) -> StreamingResponse:
    """Shared SSE streaming logic used by both endpoints."""
    loop = asyncio.get_event_loop()
    q: asyncio.Queue = asyncio.Queue()

    def on_progress(event_type: str, message: str) -> None:
        asyncio.run_coroutine_threadsafe(
            q.put({"type": event_type, "data": message}), loop
        )

    def run() -> None:
        try:
            result = run_agent(query, on_progress=on_progress, dev_mode=DEV_MODE)
            asyncio.run_coroutine_threadsafe(
                q.put({"type": "result", "data": result}), loop
            )
        except Exception as exc:
            asyncio.run_coroutine_threadsafe(
                q.put({"type": "error", "data": str(exc)}), loop
            )
        finally:
            asyncio.run_coroutine_threadsafe(q.put(None), loop)

    threading.Thread(target=run, daemon=True).start()

    async def event_stream():
        while True:
            item = await q.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/")
async def index() -> HTMLResponse:
    html = Path("templates/index.html").read_text()
    return HTMLResponse(html)


# GET endpoint — used by EventSource in the browser (SSE requires GET)
@app.get("/search-stream")
async def search_stream(q: str = Query(..., description="Project description")) -> StreamingResponse:
    return _stream_agent(q)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
