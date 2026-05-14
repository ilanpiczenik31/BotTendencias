"""
Pull&Bear scraper — Inditex brand but different tech stack from Zara.
Tries static JSON-LD first (like H&M), falls back to __NEXT_DATA__ and render.
"""
import json
from .hm import _parse_hm_jld
from .base import BaseScraper, ScrapedProduct, fetch_page, fetch_page_static, parse_price
from .registry import REGISTRY
import logging

logger = logging.getLogger(__name__)

BASE = "https://www.pullandbear.com"


def _parse_pnb_next_data(soup, section_key: str) -> list[ScrapedProduct]:
    """Extract products from Pull&Bear Next.js __NEXT_DATA__."""
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        return []
    try:
        data = json.loads(script.string)
        raw = _walk_for_products(data)
        results = []
        seen: set[str] = set()
        for p in raw:
            if len(results) >= 20:
                break
            name = str(p.get("name", "")).strip()
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            image = p.get("image") or p.get("mainImgUrl") or ""
            if isinstance(image, list):
                image = image[0] if image else ""
            if isinstance(image, dict):
                image = image.get("url", "")
            price = p.get("price")
            if isinstance(price, (int, float)) and price > 100:
                price = price / 100
            elif isinstance(price, dict):
                v = price.get("value") or price.get("amount")
                if v:
                    price = float(v) / 100 if float(v) > 1000 else float(v)
            url = p.get("url") or p.get("href") or ""
            if url and not url.startswith("http"):
                url = BASE + url
            results.append(ScrapedProduct(
                name=name, section=section_key,
                price=float(price) if price else None,
                currency="EUR",
                image_url=image or None,
                product_url=url or None,
                category="ropa",
            ))
        if results:
            logger.info(f"Pull&Bear __NEXT_DATA__ [{section_key}]: {len(results)} products")
        return results
    except Exception as e:
        logger.debug(f"Pull&Bear __NEXT_DATA__ failed: {e}")
    return []


def _walk_for_products(obj, depth: int = 0, _seen: set | None = None) -> list[dict]:
    if _seen is None:
        _seen = set()
    if depth > 12 or not isinstance(obj, (dict, list)):
        return []
    obj_id = id(obj)
    if obj_id in _seen:
        return []
    _seen.add(obj_id)
    results = []
    if isinstance(obj, list):
        for item in obj[:300]:
            results.extend(_walk_for_products(item, depth + 1, _seen))
    elif isinstance(obj, dict):
        name = str(obj.get("name", "")).strip()
        has_fields = (
            ("price" in obj or "xmedia" in obj or "image" in obj or "mainImgUrl" in obj) and
            ("id" in obj or "sku" in obj or "url" in obj)
        )
        if len(name) > 3 and has_fields:
            results.append(obj)
            return results
        for v in obj.values():
            results.extend(_walk_for_products(v, depth + 1, _seen))
    return results


def _extract_from_soup(soup, section_key: str) -> list[ScrapedProduct]:
    # 1. Try H&M-style JSON-LD
    parsed = _parse_hm_jld(soup, section_key)
    if parsed:
        logger.info(f"Pull&Bear JSON-LD [{section_key}]: {len(parsed)} products")
        return parsed
    # 2. Try __NEXT_DATA__
    parsed = _parse_pnb_next_data(soup, section_key)
    if parsed:
        return parsed
    return []


class PullAndBearScraper(BaseScraper):
    store_name = "Pull&Bear"
    store_url = "https://www.pullandbear.com/es/"

    def __init__(self, sections: list[dict] | None = None):
        self.sections = sections or REGISTRY.get("Pull&Bear", [])

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for sec in self.sections:
            url, section_key = sec["url"], sec["key"]

            # 1. Static fetch first
            soup = await fetch_page_static(url, country="es")
            if soup:
                parsed = _extract_from_soup(soup, section_key)
                if parsed:
                    products.extend(parsed)
                    continue

            # 2. Render fallback
            for wait_ms, use_premium in [(5000, False), (8000, True)]:
                try:
                    soup = await fetch_page(url, country="es", wait=wait_ms, premium=use_premium)
                    parsed = _extract_from_soup(soup, section_key)
                    if parsed:
                        products.extend(parsed)
                        break
                    logger.warning(f"Pull&Bear [{section_key}]: 0 products (render premium={use_premium})")
                    break
                except Exception:
                    logger.warning(f"Pull&Bear [{section_key}] render retry (premium={use_premium})")

        return products
