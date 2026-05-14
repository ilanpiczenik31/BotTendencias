"""
& Other Stories scraper — H&M Group brand, same SSR + JSON-LD stack as H&M.
URL pattern /es_es/ matches H&M exactly — reuses _parse_hm_jld directly.
"""
from .hm import _parse_hm_jld
from .base import BaseScraper, ScrapedProduct, fetch_page, fetch_page_static
from .registry import REGISTRY
import logging

logger = logging.getLogger(__name__)

BASE = "https://www.stories.com"


class StoriesScraper(BaseScraper):
    store_name = "& Other Stories"
    store_url = "https://www.stories.com/es_es/"

    def __init__(self, sections: list[dict] | None = None):
        self.sections = sections or REGISTRY.get("& Other Stories", [])

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for sec in self.sections:
            url, section_key = sec["url"], sec["key"]
            soup = None

            # 1. Static fetch — H&M Group SSR, JSON-LD in raw HTML
            soup = await fetch_page_static(url, country="es")
            if soup:
                parsed = _parse_hm_jld(soup, section_key)
                if parsed:
                    logger.info(f"& Other Stories [{section_key}]: {len(parsed)} products (JSON-LD static)")
                    products.extend(parsed)
                    continue
                soup = None

            # 2. Render fallback
            if not soup:
                for wait_ms, use_premium in [(5000, False), (8000, True)]:
                    try:
                        soup = await fetch_page(url, country="es", wait=wait_ms, premium=use_premium)
                        break
                    except Exception:
                        logger.warning(f"& Other Stories [{section_key}] render retry (premium={use_premium})")

            if not soup:
                logger.error(f"& Other Stories [{section_key}] failed: {url}")
                continue

            parsed = _parse_hm_jld(soup, section_key)
            if parsed:
                logger.info(f"& Other Stories [{section_key}]: {len(parsed)} products (JSON-LD render)")
                products.extend(parsed)
            else:
                logger.warning(f"& Other Stories [{section_key}]: 0 products — JSON-LD empty")

        return products
