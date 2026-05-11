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
    stores = [
        Store(name="Zara", url="https://www.zara.com/es/", country="Spain"),
        Store(name="H&M", url="https://www2.hm.com/es_es/", country="Sweden"),
        Store(name="Bershka", url="https://www.bershka.com/es/", country="Spain"),
        Store(name="Springfield", url="https://www.springfield.com/es/", country="Spain"),
        Store(name="The Sting", url="https://www.the-sting.com/", country="Netherlands"),
        Store(name="J.Crew", url="https://www.jcrew.com/", country="USA"),
        Store(name="The North Face", url="https://www.thenorthface.com/en-us/", country="USA"),
        Store(name="El Corte Inglés", url="https://www.elcorteingles.es/moda/", country="Spain"),
    ]
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        for store in stores:
            result = await session.execute(select(Store).where(Store.name == store.name))
            if not result.scalar_one_or_none():
                session.add(store)
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
