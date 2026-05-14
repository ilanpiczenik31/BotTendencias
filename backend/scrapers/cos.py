"""
COS scraper — H&M Group brand.
COS doesn't use H&M's JSON-LD format, so we try multiple extraction methods:
JSON-LD → __NEXT_DATA__ → HTML grid.
Static fetch works (no Cloudflare), render needed as fallback.
"""
import json
import re
from .hm import _parse_hm_jld
from .base import BaseScraper, ScrapedProduct, fetch_page, fetch_page_static, parse_price
from .registry import REGISTRY
import logging

logger = logging.getLogger(__name__)

BASE = "https://www.cos.com"


def _parse_cos_next_data(soup, section_key: str) -> list[ScrapedProduct]:
    """Extract products from COS Next.js __NEXT_DATA__ SSR state."""
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
            image = p.get("image", "") or p.get("images", "")
            if isinstance(image, list):
                image = image[0] if image else ""
            if isinstance(image, dict):
                image = image.get("url", "")
            price = p.get("price")
            if isinstance(price, dict):
                price = price.get("value") or price.get("amount") or price.get("current")
            if isinstance(price, dict):
                price = price.get("value") or price.get("amount")
            url = p.get("url") or p.get("href") or p.get("pdpUrl") or ""
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
            logger.info(f"COS __NEXT_DATA__ [{section_key}]: {len(results)} products")
        return results
    except Exception as e:
        logger.debug(f"COS __NEXT_DATA__ failed: {e}")
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
        has_product_fields = (
            ("price" in obj or "images" in obj or "image" in obj) and
            ("id" in obj or "sku" in obj or "articleCode" in obj or "url" in obj or "href" in obj)
        )
        if len(name) > 3 and has_product_fields:
            results.append(obj)
            return results
        for v in obj.values():
            results.extend(_walk_for_products(v, depth + 1, _seen))
    return results


def _parse_cos_html(soup, section_key: str) -> list[ScrapedProduct]:
    """Parse COS product grid HTML."""
    results = []
    items = (
        soup.select("article[class*='product']") or
        soup.select("[class*='product-tile']") or
        soup.select("[class*='product-item']") or
        soup.select("li[class*='product']")
    )[:30]

    for item in items:
        name = None
        image_url = None
        product_url = None
        price = None

        for sel in ["[class*='name']", "[class*='title']", "h2", "h3", "h4"]:
            el = item.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text and len(text) > 3:
                    name = text
                    break

        for img in item.find_all("img"):
            src = (img.get("src") or img.get("data-src") or
                   img.get("data-srcset", "").split(",")[0].strip().split(" ")[0] or "")
            if src and "cos.com" in src and (".jpg" in src or ".webp" in src):
                image_url = src
                break

        link = item.select_one("a[href]")
        if link:
            href = link.get("href", "")
            product_url = href if href.startswith("http") else BASE + href

        for sel in ["[class*='price']", "[class*='amount']"]:
            el = item.select_one(sel)
            if el:
                price = parse_price(el.get_text(strip=True))
                if price:
                    break

        if name:
            results.append(ScrapedProduct(
                name=name, section=section_key,
                price=price, currency="EUR",
                image_url=image_url,
                product_url=product_url,
                category="ropa",
            ))
    return results


def _extract_from_soup(soup, section_key: str) -> list[ScrapedProduct]:
    """Try all extraction methods in order."""
    parsed = _parse_hm_jld(soup, section_key)
    if parsed:
        logger.info(f"COS [{section_key}]: {len(parsed)} products (JSON-LD)")
        return parsed
    parsed = _parse_cos_next_data(soup, section_key)
    if parsed:
        return parsed
    parsed = _parse_cos_html(soup, section_key)
    if parsed:
        logger.info(f"COS HTML [{section_key}]: {len(parsed)} products")
        return parsed
    return []


class COSScraper(BaseScraper):
    store_name = "COS"
    store_url = "https://www.cos.com/es_es/"

    def __init__(self, sections: list[dict] | None = None):
        self.sections = sections or REGISTRY.get("COS", [])

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for sec in self.sections:
            url, section_key = sec["url"], sec["key"]

            # 1. Static fetch first (COS has no Cloudflare)
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
                    else:
                        logger.warning(f"COS [{section_key}]: 0 products after render (premium={use_premium})")
                    break
                except Exception:
                    logger.warning(f"COS [{section_key}] render retry (premium={use_premium})")

        return products
