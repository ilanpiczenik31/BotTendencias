from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScrapedProduct:
    name: str
    section: str  # new_arrivals | best_sellers | trending
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    price: Optional[float] = None
    currency: str = "EUR"
    category: Optional[str] = None


class BaseScraper(ABC):
    store_name: str = ""
    store_url: str = ""

    def __init__(self):
        self._browser: Optional[Browser] = None

    async def _get_page(self, context: BrowserContext) -> Page:
        page = await context.new_page()
        await page.set_extra_http_headers({
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        })
        return page

    async def scrape(self) -> list[ScrapedProduct]:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            try:
                products = await self._scrape(context)
                logger.info(f"[{self.store_name}] scraped {len(products)} products")
                return products
            except Exception as e:
                logger.error(f"[{self.store_name}] scrape failed: {e}")
                return []
            finally:
                await browser.close()

    @abstractmethod
    async def _scrape(self, context: BrowserContext) -> list[ScrapedProduct]:
        """Implement per-store scraping logic."""
        ...

    async def _safe_get_text(self, page: Page, selector: str) -> Optional[str]:
        try:
            el = await page.query_selector(selector)
            return (await el.inner_text()).strip() if el else None
        except Exception:
            return None

    async def _safe_get_attr(self, page: Page, selector: str, attr: str) -> Optional[str]:
        try:
            el = await page.query_selector(selector)
            return await el.get_attribute(attr) if el else None
        except Exception:
            return None

    def _parse_price(self, raw: Optional[str]) -> Optional[float]:
        if not raw:
            return None
        cleaned = raw.replace("€", "").replace("$", "").replace(",", ".").replace("\xa0", "").strip()
        try:
            return float("".join(c for c in cleaned if c.isdigit() or c == "."))
        except ValueError:
            return None
