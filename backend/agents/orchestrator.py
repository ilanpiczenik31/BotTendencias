import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from models.database import (
    AsyncSessionLocal, WeeklyRun, Product, TrendAnalysis, WeeklyReport,
    Store, RunStatus
)
from scrapers.zara import ZaraScraper
from scrapers.hm import HMScraper
from scrapers.bershka import BershkaScraper
from scrapers.springfield import SpringfieldScraper
from scrapers.the_sting import TheStingScraper
from scrapers.jcrew import JCrewScraper
from scrapers.north_face import NorthFaceScraper
from scrapers.el_corte_ingles import ElCorteInglesScraper
from agents.analyzer import analyze_store_trends, generate_weekly_report

logger = logging.getLogger(__name__)

SCRAPERS = {
    "Zara": ZaraScraper,
    "H&M": HMScraper,
    "Bershka": BershkaScraper,
    "Springfield": SpringfieldScraper,
    "The Sting": TheStingScraper,
    "J.Crew": JCrewScraper,
    "The North Face": NorthFaceScraper,
    "El Corte Inglés": ElCorteInglesScraper,
}


async def run_pipeline(triggered_by: str = "manual") -> int:
    """Main pipeline: scrape → analyze → report. Returns run_id."""
    async with AsyncSessionLocal() as session:
        run = WeeklyRun(status=RunStatus.running, triggered_by=triggered_by)
        session.add(run)
        await session.commit()
        await session.refresh(run)
        run_id = run.id
        logger.info(f"Started run #{run_id} (triggered_by={triggered_by})")

    try:
        await _scrape_all_stores(run_id)
        await _analyze_all_stores(run_id)
        await _generate_report(run_id)

        async with AsyncSessionLocal() as session:
            run = await session.get(WeeklyRun, run_id)
            run.status = RunStatus.completed
            run.completed_at = datetime.utcnow()
            await session.commit()

        logger.info(f"Run #{run_id} completed successfully")
    except Exception as e:
        logger.error(f"Run #{run_id} failed: {e}")
        async with AsyncSessionLocal() as session:
            run = await session.get(WeeklyRun, run_id)
            run.status = RunStatus.failed
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            await session.commit()

    return run_id


async def _scrape_all_stores(run_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Store).where(Store.active == True))
        stores = result.scalars().all()

    tasks = [_scrape_store(run_id, store) for store in stores]
    await asyncio.gather(*tasks, return_exceptions=True)


async def _scrape_store(run_id: int, store: Store):
    scraper_class = SCRAPERS.get(store.name)
    if not scraper_class:
        logger.warning(f"No scraper for store: {store.name}")
        return

    logger.info(f"Scraping {store.name}...")
    scraper = scraper_class()
    products = await scraper.scrape()

    if not products:
        logger.warning(f"No products scraped for {store.name}")
        return

    # Deduplicate by name (case-insensitive) within the same run+store
    seen_names: set[str] = set()
    unique_products = []
    for p in products:
        key = p.name.strip().lower()
        if key not in seen_names:
            seen_names.add(key)
            unique_products.append(p)

    async with AsyncSessionLocal() as session:
        db_products = [
            Product(
                run_id=run_id,
                store_id=store.id,
                name=p.name,
                price=p.price,
                currency=p.currency,
                image_url=p.image_url,
                product_url=p.product_url,
                category=p.category,
                section=p.section,
            )
            for p in unique_products
        ]
        session.add_all(db_products)
        await session.commit()
        logger.info(f"Saved {len(db_products)} products for {store.name} ({len(products) - len(db_products)} duplicates removed)")


async def _analyze_all_stores(run_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Store).where(Store.active == True))
        stores = result.scalars().all()

    for store in stores:
        await _analyze_store(run_id, store)


async def _analyze_store(run_id: int, store: Store):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Product).where(Product.run_id == run_id, Product.store_id == store.id)
        )
        products = result.scalars().all()

    if not products:
        return

    from scrapers.base import ScrapedProduct
    scraped = [
        ScrapedProduct(
            name=p.name,
            section=p.section,
            price=float(p.price) if p.price else None,
            currency=p.currency,
            image_url=p.image_url,
            product_url=p.product_url,
            category=p.category,
        )
        for p in products
    ]

    trends = await analyze_store_trends(store.name, scraped)

    async with AsyncSessionLocal() as session:
        analysis = TrendAnalysis(
            run_id=run_id,
            store_id=store.id,
            summary=trends.get("summary", ""),
            trends=trends,
        )
        session.add(analysis)
        await session.commit()
        logger.info(f"Analysis saved for {store.name}")


async def _generate_report(run_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TrendAnalysis, Store)
            .join(Store, TrendAnalysis.store_id == Store.id)
            .where(TrendAnalysis.run_id == run_id)
        )
        rows = result.all()

        # Get previous report for comparison
        prev_result = await session.execute(
            select(WeeklyReport)
            .join(WeeklyRun, WeeklyReport.run_id == WeeklyRun.id)
            .where(WeeklyRun.id != run_id, WeeklyRun.status == RunStatus.completed)
            .order_by(desc(WeeklyRun.created_at))
            .limit(1)
        )
        prev_report = prev_result.scalar_one_or_none()

    analyses = [
        {"store_name": store.name, "trends": analysis.trends}
        for analysis, store in rows
    ]

    prev_data = {"top_trends": prev_report.top_trends} if prev_report else None
    report_data = await generate_weekly_report(analyses, prev_data)

    async with AsyncSessionLocal() as session:
        report = WeeklyReport(
            run_id=run_id,
            summary=report_data.get("summary", ""),
            top_trends=report_data.get("top_trends", {}),
            comparison_vs_prev=report_data,
        )
        session.add(report)
        await session.commit()
        logger.info(f"Weekly report saved for run #{run_id}")
