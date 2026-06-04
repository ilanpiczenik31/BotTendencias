import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from models.database import init_db, seed_stores, cleanup_stuck_runs
from api.routes import router
from api.auth import router as auth_router, verify_token
from agents.orchestrator import run_pipeline
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


class AuthMiddleware(BaseHTTPMiddleware):
    """Protect write operations (POST/PUT/DELETE) with a bearer token."""
    OPEN_PATHS = {"/health", "/api/auth/login"}

    async def dispatch(self, request: Request, call_next):
        if request.method in ("GET", "OPTIONS") or request.url.path in self.OPEN_PATHS:
            return await call_next(request)

        admin_pw = os.getenv("ADMIN_PASSWORD", "")
        if not admin_pw:
            return await call_next(request)  # dev mode

        auth = request.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip()
        if not verify_token(token):
            return Response(
                content='{"detail":"No autorizado. Iniciá sesión primero."}',
                status_code=401,
                media_type="application/json",
            )
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    await init_db()
    await seed_stores()
    await cleanup_stuck_runs()  # mark any leftover "running" runs as failed

    # Schedule weekly run: every Monday at 08:00 UTC
    scheduler.add_job(
        run_pipeline,
        CronTrigger(day_of_week="mon", hour=8, minute=0),
        id="weekly_scrape",
        replace_existing=True,
        kwargs={"triggered_by": "cron"},
    )
    scheduler.start()
    logger.info("Scheduler started — weekly run every Monday 08:00 UTC")

    yield

    # Shutdown
    scheduler.shutdown()


app = FastAPI(
    title="Fashion Trends API",
    description="Rastreador semanal de tendencias de moda europea",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
