import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import alerts, metrics, nodes, thresholds
from .services import alert_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run offline detection on a timer for the life of the app.
    monitor = asyncio.create_task(alert_service.offline_monitor_loop())
    yield
    monitor.cancel()


app = FastAPI(title="Data Center Monitoring API", lifespan=lifespan)

# The dashboard is served from a different origin during development, so allow
# cross-origin requests. Tighten this list before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics.router)
app.include_router(nodes.router)
app.include_router(alerts.router)
app.include_router(thresholds.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
