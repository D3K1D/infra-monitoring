import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routers import alerts, auth, metrics, nodes, summary, thresholds
from .services import alert_service

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run offline detection on a timer for the life of the app.
    monitor = asyncio.create_task(alert_service.offline_monitor_loop())
    yield
    monitor.cancel()


app = FastAPI(title="Data Center Monitoring API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(metrics.router)
app.include_router(nodes.router)
app.include_router(alerts.router)
app.include_router(thresholds.router)
app.include_router(summary.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


# Serve the dashboard from the same origin as the API. Mounted last so /api/*
# keeps routing to the routers above; everything else falls through to files.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
