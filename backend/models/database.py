from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Numeric, DateTime, ForeignKey, JSON, Integer, Enum
from datetime import datetime
from typing import Optional
import enum
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class RunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    url: Mapped[str] = mapped_column(String(500))
    country: Mapped[str] = mapped_column(String(50))
    active: Mapped[bool] = mapped_column(default=True)
    # sections: [{key, label, url}] — managed via dashboard
    sections: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    products: Mapped[list["Product"]] = relationship(back_populates="store")
    analyses: Mapped[list["TrendAnalysis"]] = relationship(back_populates="store")


class WeeklyRun(Base):
    __tablename__ = "weekly_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.pending)
    triggered_by: Mapped[str] = mapped_column(String(50), default="manual")  # manual | cron
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    products: Mapped[list["Product"]] = relationship(back_populates="run")
    analyses: Mapped[list["TrendAnalysis"]] = relationship(back_populates="run")
    report: Mapped[Optional["WeeklyReport"]] = relationship(back_populates="run", uselist=False)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("weekly_runs.id"))
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"))
    name: Mapped[str] = mapped_column(String(500))
    price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="EUR")
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    section: Mapped[str] = mapped_column(String(100))  # new_arrivals | best_sellers | trending
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    run: Mapped["WeeklyRun"] = relationship(back_populates="products")
    store: Mapped["Store"] = relationship(back_populates="products")


class TrendAnalysis(Base):
    __tablename__ = "trend_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("weekly_runs.id"))
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"))
    summary: Mapped[str] = mapped_column(Text)
    trends: Mapped[dict] = mapped_column(JSON)  # {colors, styles, categories, price_range}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    run: Mapped["WeeklyRun"] = relationship(back_populates="analyses")
    store: Mapped["Store"] = relationship(back_populates="analyses")


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("weekly_runs.id"), unique=True)
    summary: Mapped[str] = mapped_column(Text)
    top_trends: Mapped[dict] = mapped_column(JSON)
    comparison_vs_prev: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    run: Mapped["WeeklyRun"] = relationship(back_populates="report")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_stores():
    """Seed active stores with their sections. Only creates stores that don't exist yet."""
    default_stores = [
        Store(
            name="Zara",
            url="https://www.zara.com/es/",
            country="Spain",
            active=True,
            sections=[
                {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.zara.com/es/es/hombre-nuevo-l711.html"},
                {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.zara.com/es/es/mujer-nuevo-l1180.html"},
                {"key": "trending_women",     "label": "Trends · Mujer", "url": "https://www.zara.com/es/es/woman-events-l17929.html"},
            ]
        ),
        Store(
            name="H&M",
            url="https://www2.hm.com/es_es/",
            country="Sweden",
            active=True,
            sections=[
                {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www2.hm.com/es_es/mujer/novedades/ver-todo.html"},
                {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www2.hm.com/es_es/hombre/novedades/ver-todo.html"},
            ]
        ),
        Store(
            name="El Corte Inglés",
            url="https://www.elcorteingles.es/",
            country="Spain",
            active=True,
            sections=[
                {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.elcorteingles.es/lo-mas-nuevo/moda-mujer/"},
                {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.elcorteingles.es/lo-mas-nuevo/moda-hombre/"},
            ]
        ),
        Store(
            name="The North Face",
            url="https://www.thenorthface.com/es-es/",
            country="USA",
            active=True,
            sections=[
                {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.thenorthface.com/es-es/c/hombre/novedades-and-tendencias/novedades-226102"},
                {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.thenorthface.com/es-es/c/mujer/novedades-and-tendencias/novedades-226102"},
            ]
        ),
        # ASOS: marketplace multimarca con versiones por país
        Store(
            name="ASOS",
            url="https://www.asos.com/",
            country="UK",
            active=True,
            sections=[
                {"key": "new_arrivals_women", "label": "Novedades · Mujer",  "category_id": 2623},
                {"key": "new_arrivals_men",   "label": "Novedades · Hombre", "category_id": 2606},
            ]
        ),
        Store(
            name="ASOS España",
            url="https://www.asos.com/es/",
            country="Spain",
            active=True,
            sections=[
                {"key": "new_arrivals_women", "label": "Novedades · Mujer",  "category_id": 2623, "store": "ES", "lang": "es-ES", "currency": "EUR", "country": "ES"},
                {"key": "new_arrivals_men",   "label": "Novedades · Hombre", "category_id": 2606, "store": "ES", "lang": "es-ES", "currency": "EUR", "country": "ES"},
            ]
        ),
        Store(
            name="ASOS Alemania",
            url="https://www.asos.com/de/",
            country="Germany",
            active=True,
            sections=[
                {"key": "new_arrivals_women", "label": "Novedades · Mujer",  "category_id": 2623, "store": "DE", "lang": "de-DE", "currency": "EUR", "country": "DE"},
                {"key": "new_arrivals_men",   "label": "Novedades · Hombre", "category_id": 2606, "store": "DE", "lang": "de-DE", "currency": "EUR", "country": "DE"},
            ]
        ),
        Store(
            name="The Sting",
            url="https://www.thesting.com/nl-nl/",
            country="Netherlands",
            active=True,
            sections=[
                {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.thesting.com/nl-nl/dames/new-in", "category_id": "dames-new-in"},
                {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.thesting.com/nl-nl/heren/new-in", "category_id": "heren-new-in"},
            ]
        ),
    ]
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, text
        # Ensure sections column exists (migration for existing DBs)
        try:
            await session.execute(text("ALTER TABLE stores ADD COLUMN IF NOT EXISTS sections JSON DEFAULT '[]'"))
            await session.commit()
        except Exception:
            pass

        # Deactivate stores that no longer have working scrapers
        RETIRED_STORES = ["& Other Stories", "Pull&Bear"]
        for name in RETIRED_STORES:
            result = await session.execute(select(Store).where(Store.name == name))
            store = result.scalar_one_or_none()
            if store and store.active:
                store.active = False

        for store in default_stores:
            result = await session.execute(select(Store).where(Store.name == store.name))
            existing = result.scalar_one_or_none()
            if not existing:
                session.add(store)
            elif not existing.sections:
                # Backfill sections for existing stores
                existing.sections = store.sections
            elif store.name in ("ASOS", "ASOS España", "ASOS Alemania"):
                # Always refresh ASOS sections to pick up store config params
                existing.sections = store.sections
                existing.url = store.url
        await session.commit()


async def cleanup_stuck_runs():
    """Mark any runs stuck in 'running'/'pending' as failed on startup."""
    from sqlalchemy import update
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            update(WeeklyRun)
            .where(WeeklyRun.status.in_([RunStatus.running, RunStatus.pending]))
            .values(
                status=RunStatus.failed,
                error_message="Interrupted — server restarted",
                completed_at=datetime.utcnow(),
            )
        )
        if result.rowcount:
            import logging
            logging.getLogger(__name__).info(f"Cleaned up {result.rowcount} stuck run(s)")
        await session.commit()


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
