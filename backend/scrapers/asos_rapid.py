"""
ASOS scraper via RapidAPI (asos2.p.rapidapi.com).
Server-side call — no CORS issues, no ScraperAPI needed.
Fetches new arrivals sorted by freshness for women and men.
"""
import os
import httpx
import logging
from .base import BaseScraper, ScrapedProduct
from .registry import REGISTRY

logger = logging.getLogger(__name__)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "asos2.p.rapidapi.com"
BASE_URL = "https://asos2.p.rapidapi.com/products/v2/list"
PRODUCT_BASE = "https://www.asos.com"

HEADERS = {
    "x-rapidapi-host": RAPIDAPI_HOST,
    "x-rapidapi-key": RAPIDAPI_KEY,
}

# categoryId → section key
CATEGORIES = {
    2623: "new_arrivals_women",
    2606: "new_arrivals_men",
}


def _build_params(category_id: int, offset: int = 0, limit: int = 48) -> dict:
    return {
        "store": "COM",
        "lang": "en-GB",
        "currency": "GBP",
        "categoryId": str(category_id),
        "sort": "freshness",
        "limit": str(limit),
        "offset": str(offset),
        "country": "GB",
    }


def _parse_product(item: dict, section_key: str) -> ScrapedProduct | None:
    name = (item.get("name") or "").strip()
    if not name or len(name) < 3:
        return None

    brand = (item.get("brandName") or "").strip()
    full_name = f"{brand} — {name}" if brand and brand.lower() not in name.lower() else name

    raw_image = item.get("imageUrl") or ""
    image_url = ("https:" + raw_image) if raw_image.startswith("//") else (raw_image or None)

    raw_url = item.get("url") or ""
    product_url = (PRODUCT_BASE + raw_url) if raw_url.startswith("/") else (raw_url or None)

    price = None
    price_obj = item.get("price") or {}
    if isinstance(price_obj, dict):
        current = price_obj.get("current") or {}
        price = current.get("value")
    elif isinstance(price_obj, (int, float)):
        price = float(price_obj)

    return ScrapedProduct(
        name=full_name,
        section=section_key,
        price=float(price) if price is not None else None,
        currency="GBP",
        image_url=image_url,
        product_url=product_url,
        category="ropa",
    )


class ASOSRapidScraper(BaseScraper):
    store_name = "ASOS"
    store_url = "https://www.asos.com/"

    def __init__(self, sections: list[dict] | None = None):
        self.sections = sections or REGISTRY.get("ASOS", [])

    async def _scrape(self) -> list[ScrapedProduct]:
        if not RAPIDAPI_KEY:
            logger.error("ASOS: RAPIDAPI_KEY not set — skipping")
            return []

        products: list[ScrapedProduct] = []

        for sec in self.sections:
            section_key = sec["key"]

            # Map section key back to category ID
            cat_id = next(
                (cid for cid, key in CATEGORIES.items() if key == section_key),
                None
            )
            if cat_id is None:
                # Try to get from the section dict directly
                cat_id = sec.get("category_id")
            if cat_id is None:
                logger.warning(f"ASOS [{section_key}]: no category_id found, skipping")
                continue

            section_products: list[ScrapedProduct] = []
            seen_names: set[str] = set()

            # Paginate up to 48 products (1 page is usually enough)
            for page in range(3):
                offset = page * 48
                params = _build_params(int(cat_id), offset=offset, limit=48)

                try:
                    async with httpx.AsyncClient(timeout=20, headers=HEADERS) as client:
                        resp = await client.get(BASE_URL, params=params)
                        resp.raise_for_status()
                        data = resp.json()
                except Exception as e:
                    logger.error(f"ASOS [{section_key}] fetch failed (offset={offset}): {e}")
                    break

                items = data.get("products") or []
                if not items:
                    logger.info(f"ASOS [{section_key}] page {page + 1}: no products returned")
                    break

                new_count = 0
                for item in items:
                    p = _parse_product(item, section_key)
                    if p and p.name.lower() not in seen_names:
                        seen_names.add(p.name.lower())
                        section_products.append(p)
                        new_count += 1

                logger.info(f"ASOS [{section_key}] page {page + 1}: {new_count} new (total: {len(section_products)})")

                if len(section_products) >= 48 or new_count == 0:
                    break

            products.extend(section_products[:50])
            logger.info(f"ASOS [{section_key}]: {len(section_products[:50])} products total")

        return products
