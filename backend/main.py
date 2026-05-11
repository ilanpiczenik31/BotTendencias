import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from models.database import init_db, seed_stores, cleanup_stuck_runs
from api.routes import router
from agents.orchestrator import run_pipeline
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
