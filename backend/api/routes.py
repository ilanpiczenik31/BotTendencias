from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from models.database import (
    get_session, WeeklyRun, Product, TrendAnalysis, WeeklyReport, Store, RunStatus
)
from agents.orchestrator import run_pipeline
from scrapers.debug import inspect_page
from scrapers.registry import REGISTRY
from pydantic import BaseModel
import asyncio

router = APIRouter()


class RunConfig(BaseModel):
    stores: list[dict] | None = None  # [{"store": "Zara", "sections": [...]}]


# ── Runs ──────────────────────────────────────────────────────────────────────

@router.post("/runs/trigger")
async def trigger_run(background_tasks: BackgroundTasks, config: RunConfig = RunConfig()):
    """Trigger a manual scraping run with optional custom config."""
    background_tasks.add_task(run_pipeline, "manual", config.stores)
    return {"message": "Run started", "status": "running"}


@router.get("/registry")
async def get_registry():
    """Return all available stores and their scrapeable sections."""
    return [
        {"store": store, "sections": sections}
        for store, sections in REGISTRY.items()
    ]


@router.get("/runs")
async def list_runs(limit: int = 20, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(WeeklyRun).order_by(desc(WeeklyRun.created_at)).limit(limit)
    )
    runs = result.scalars().all()
    return [
        {
            "id": r.id,
            "run_date": r.run_date.isoformat(),
            "status": r.status,
            "triggered_by": r.triggered_by,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "error_message": r.error_message,
        }
        for r in runs
    ]


@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: int, session: AsyncSession = Depends(get_session)):
    from datetime import datetime
    run = await session.get(WeeklyRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.status not in (RunStatus.running, RunStatus.pending):
        raise HTTPException(400, f"Run is {run.status}, cannot cancel")
    run.status = RunStatus.failed
    run.error_message = "Cancelled manually"
    run.completed_at = datetime.utcnow()
    await session.commit()
    return {"message": "Run cancelled"}


@router.get("/runs/{run_id}")
async def get_run(run_id: int, session: AsyncSession = Depends(get_session)):
    run = await session.get(WeeklyRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return {
        "id": run.id,
        "run_date": run.run_date.isoformat(),
        "status": run.status,
        "triggered_by": run.triggered_by,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "error_message": run.error_message,
    }


# ── Products ──────────────────────────────────────────────────────────────────

@router.get("/runs/{run_id}/products")
async def get_run_products(
    run_id: int,
    store_id: int | None = None,
    section: str | None = None,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    query = (
        select(Product, Store)
        .join(Store, Product.store_id == Store.id)
        .where(Product.run_id == run_id)
    )
    if store_id:
        query = query.where(Product.store_id == store_id)
    if section:
        query = query.where(Product.section == section)
    query = query.limit(limit)

    result = await session.execute(query)
    rows = result.all()
    return [
        {
            "id": p.id,
            "store": s.name,
            "store_id": s.id,
            "name": p.name,
            "price": float(p.price) if p.price else None,
            "currency": p.currency,
            "image_url": p.image_url,
            "product_url": p.product_url,
            "section": p.section,
            "category": p.category,
        }
        for p, s in rows
    ]


# ── Analyses ──────────────────────────────────────────────────────────────────

@router.get("/runs/{run_id}/analyses")
async def get_run_analyses(run_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(TrendAnalysis, Store)
        .join(Store, TrendAnalysis.store_id == Store.id)
        .where(TrendAnalysis.run_id == run_id)
    )
    rows = result.all()
    return [
        {
            "store": s.name,
            "store_id": s.id,
            "summary": a.summary,
            "trends": a.trends,
            "created_at": a.created_at.isoformat(),
        }
        for a, s in rows
    ]


# ── Reports ───────────────────────────────────────────────────────────────────

@router.get("/reports")
async def list_reports(limit: int = 10, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(WeeklyReport, WeeklyRun)
        .join(WeeklyRun, WeeklyReport.run_id == WeeklyRun.id)
        .order_by(desc(WeeklyRun.created_at))
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "id": r.id,
            "run_id": r.run_id,
            "run_date": run.run_date.isoformat(),
            "summary": r.summary,
            "top_trends": r.top_trends,
            "comparison_vs_prev": r.comparison_vs_prev,
            "created_at": r.created_at.isoformat(),
        }
        for r, run in rows
    ]


@router.get("/reports/latest")
async def get_latest_report(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(WeeklyReport, WeeklyRun)
        .join(WeeklyRun, WeeklyReport.run_id == WeeklyRun.id)
        .order_by(desc(WeeklyRun.created_at))
        .limit(1)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "No reports yet")
    r, run = row
    return {
        "id": r.id,
        "run_id": r.run_id,
        "run_date": run.run_date.isoformat(),
        "summary": r.summary,
        "top_trends": r.top_trends,
        "comparison_vs_prev": r.comparison_vs_prev,
        "created_at": r.created_at.isoformat(),
    }


@router.get("/reports/{run_id}")
async def get_report_by_run(run_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(WeeklyReport, WeeklyRun)
        .join(WeeklyRun, WeeklyReport.run_id == WeeklyRun.id)
        .where(WeeklyReport.run_id == run_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Report not found")
    r, run = row
    return {
        "id": r.id,
        "run_id": r.run_id,
        "run_date": run.run_date.isoformat(),
        "summary": r.summary,
        "top_trends": r.top_trends,
        "comparison_vs_prev": r.comparison_vs_prev,
        "created_at": r.created_at.isoformat(),
    }


# ── Stores ────────────────────────────────────────────────────────────────────

@router.get("/stores")
async def list_stores(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Store).order_by(Store.name))
    stores = result.scalars().all()
    return [
        {"id": s.id, "name": s.name, "url": s.url, "country": s.country, "active": s.active}
        for s in stores
    ]


# ── Dashboard stats ───────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(session: AsyncSession = Depends(get_session)):
    """Quick stats for the dashboard header."""
    total_runs = await session.scalar(select(func.count(WeeklyRun.id)))
    total_products = await session.scalar(select(func.count(Product.id)))
    total_stores = await session.scalar(select(func.count(Store.id)).where(Store.active == True))

    last_run_result = await session.execute(
        select(WeeklyRun).order_by(desc(WeeklyRun.created_at)).limit(1)
    )
    last_run = last_run_result.scalar_one_or_none()

    return {
        "total_runs": total_runs,
        "total_products": total_products,
        "total_stores": total_stores,
        "last_run_date": last_run.run_date.isoformat() if last_run else None,
        "last_run_status": last_run.status if last_run else None,
    }


# ── Debug ─────────────────────────────────────────────────────────────────────

@router.get("/debug/inspect")
async def debug_inspect(url: str):
    """Inspect a page's HTML structure to find correct CSS selectors."""
    result = await inspect_page(url)
    return result
