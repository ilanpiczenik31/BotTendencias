"""
ASOS scraper — SSR + JSON-LD, no Cloudflare aggressive blocking.
Same static-first approach as H&M.
"""
import json
from .hm import _parse_hm_jld
from .base import BaseScraper, ScrapedProduct, fetch_page, fetch_page_static, parse_price
from .registry import REGISTRY
import logging

logger = logging.getLogger(__name__)

BASE = "https://www.asos.com"


def _parse_asos_next_data(soup, section_key: str) -> list[ScrapedProduct]:
    """Extract from ASOS Next.js __NEXT_DATA__ or window.__STORE__."""
    import re

    # Try __NEXT_DATA__
    script = soup.find("script", id="__NEXT_DATA__")
    if script and script.string:
        try:
            data = json.loads(script.string)
            raw = _walk_for_products(data)
            if raw:
                return _build_products(raw, section_key)
        except Exception:
            pass

    # Try inline window.__STORE__ or similar
    for script in soup.find_all("script"):
        txt = script.string or ""
        if len(txt) < 200 or "products" not in txt.lower():
            continue
        for pattern in [
            r'window\.__[A-Z_]+\s*=\s*({.+?});?\s*(?:</script>|$)',
            r'"products"\s*:\s*(\[.+?\])\s*[,}]',
        ]:
            m = re.search(pattern, txt, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(1))
                    raw = _walk_for_products(data)
                    if raw:
                        return _build_products(raw, section_key)
                except Exception:
                    pass
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
        name = str(obj.get("name", "") or obj.get("title", "")).strip()
        has_fields = (
            ("price" in obj or "imageUrl" in obj or "images" in obj or "image" in obj) and
            ("id" in obj or "productId" in obj or "url" in obj)
        )
        if len(name) > 3 and has_fields:
            results.append(obj)
            return results
        for v in obj.values():
            results.extend(_walk_for_products(v, depth + 1, _seen))
    return results


def _build_products(raw: list[dict], section_key: str) -> list[ScrapedProduct]:
    results = []
    seen: set[str] = set()
    for p in raw:
        if len(results) >= 20:
            break
        name = str(p.get("name", "") or p.get("title", "")).strip()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        image = (p.get("imageUrl") or p.get("image") or
                 p.get("images", [{}])[0] if p.get("images") else "")
        if isinstance(image, dict):
            image = image.get("url", "")
        if isinstance(image, list):
            image = image[0] if image else ""
        price = p.get("price") or p.get("currentPrice")
        if isinstance(price, dict):
            price = price.get("current", {}).get("value") or price.get("value")
        url = p.get("url") or p.get("productUrl") or ""
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
        logger.info(f"ASOS __NEXT_DATA__ [{section_key}]: {len(results)} products")
    return results


def _extract_from_soup(soup, section_key: str) -> list[ScrapedProduct]:
    # 1. JSON-LD (schema.org ItemList)
    parsed = _parse_hm_jld(soup, section_key)
    if parsed:
        logger.info(f"ASOS JSON-LD [{section_key}]: {len(parsed)} products")
        return parsed
    # 2. __NEXT_DATA__ / inline JSON
    return _parse_asos_next_data(soup, section_key)


class ASOSScraper(BaseScraper):
    store_name = "ASOS"
    store_url = "https://www.asos.com/es/"

    def __init__(self, sections: list[dict] | None = None):
        self.sections = sections or REGISTRY.get("ASOS", [])

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
            for wait_ms, use_premium in [(6000, False), (8000, True)]:
                try:
                    soup = await fetch_page(url, country="es", wait=wait_ms, premium=use_premium)
                    parsed = _extract_from_soup(soup, section_key)
                    if parsed:
                        products.extend(parsed)
                        break
                    logger.warning(f"ASOS [{section_key}]: 0 products (render premium={use_premium})")
                    break
                except Exception:
                    logger.warning(f"ASOS [{section_key}] render retry (premium={use_premium})")

        return products
