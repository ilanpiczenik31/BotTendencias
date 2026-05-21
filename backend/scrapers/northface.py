"""
North Face scraper — SSR page, no Cloudflare, products in JS data blob.
Static fetch works with free ScraperAPI tier.
Data is in a React serialized format: product_code, name, /es-es/p/url pattern.
"""
import re
import json
from .base import BaseScraper, ScrapedProduct, fetch_page_static, fetch_page, parse_price
from .registry import REGISTRY
import logging

logger = logging.getLogger(__name__)

BASE = "https://www.thenorthface.com"


def _parse_tnf_html(soup, section_key: str) -> list[ScrapedProduct]:
    html = str(soup)
    results = []
    seen: set[str] = set()

    # Products are stored as: "ProductName","/es-es/p/category/url-CODE?color=X"
    product_pattern = re.compile(
        r'"([^"]{10,80})","/es-es/p/([^"?]+(?:\?[^"]{0,50})?)"'
    )

    # Also collect images: product codes like NF0A8GBTBOM appear in image URLs
    # Image pattern: /CODE-HERO/ in assets.thenorthface.eu URLs
    img_map: dict[str, str] = {}
    img_pattern = re.compile(
        r'(https://assets\.thenorthface\.eu/images/[^"]+/([A-Z0-9]{8,12})-HERO/[^"]+\.jpg)'
    )
    for m in img_pattern.finditer(html):
        img_url, code = m.group(1), m.group(2)
        if code not in img_map:
            img_map[code] = img_url

    # Collect prices: EUR formatted prices in the page
    price_pattern = re.compile(r'(\d{2,3})[,.](\d{2})\s*€|€\s*(\d{2,3})[,.](\d{2})')
    all_prices = []
    for m in price_pattern.finditer(html):
        if m.group(1):
            all_prices.append(float(f"{m.group(1)}.{m.group(2)}"))
        else:
            all_prices.append(float(f"{m.group(3)}.{m.group(4)}"))

    # Extract products
    price_idx = 0
    for m in product_pattern.finditer(html):
        if len(results) >= 20:
            break
        name = m.group(1).strip()
        url_path = m.group(2)

        # Skip non-product entries (navigation, categories etc.)
        if len(name) < 8 or any(skip in name.lower() for skip in ["mujer", "hombre", "niños", "equipamiento", "view all", "ver todo"]):
            continue
        if name.lower() in seen:
            continue
        seen.add(name.lower())

        product_url = BASE + "/es-es/p/" + url_path

        # Extract product code from URL (e.g. NF0A8GBT)
        code_match = re.search(r'-(NF[A-Z0-9]{6,10})\?', url_path)
        product_code = code_match.group(1) if code_match else None

        # Find image by product code
        image_url = None
        if product_code:
            for img_code, img_url in img_map.items():
                if img_code.startswith(product_code):
                    image_url = img_url
                    break

        # Assign next available price
        price = all_prices[price_idx] if price_idx < len(all_prices) else None
        price_idx += 1

        results.append(ScrapedProduct(
            name=name,
            section=section_key,
            price=price,
            currency="EUR",
            image_url=image_url,
            product_url=product_url,
            category="ropa",
        ))

    logger.info(f"North Face [{section_key}]: {len(results)} products")
    return results


class NorthFaceScraper(BaseScraper):
    store_name = "The North Face"
    store_url = "https://www.thenorthface.com/es-es/"

    def __init__(self, sections: list[dict] | None = None):
        self.sections = sections or REGISTRY.get("The North Face", [])

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for sec in self.sections:
            url, section_key = sec["url"], sec["key"]

            # Static fetch — no Cloudflare on TNF
            soup = await fetch_page_static(url, country="es")
            if soup:
                parsed = _parse_tnf_html(soup, section_key)
                if parsed:
                    products.extend(parsed)
                    continue

            # Render fallback
            for wait_ms, use_premium in [(5000, False), (8000, True)]:
                try:
                    soup = await fetch_page(url, country="es", wait=wait_ms, premium=use_premium)
                    parsed = _parse_tnf_html(soup, section_key)
                    if parsed:
                        products.extend(parsed)
                    else:
                        logger.warning(f"North Face [{section_key}]: 0 products after render")
                    break
                except Exception:
                    logger.warning(f"North Face [{section_key}] render retry (premium={use_premium})")

        return products
