from datetime import datetime, timezone

from fastapi import FastAPI

app = FastAPI(
    title="Task Tracker API",
    description="Module 1 Task Tracker learning project (no auth, no database — in-memory + JSON file persistence per ADR-001)",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
