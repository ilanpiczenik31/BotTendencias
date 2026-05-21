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

    # Build image map: full SKU (e.g. NF0A8GBTBOM) → image URL
    # Pattern: /NF0A8GBTBOM-HERO/ in assets.thenorthface.eu image paths
    img_map: dict[str, str] = {}
    for m in re.finditer(
        r'(https://assets\.thenorthface\.eu/images/[^"]+/([A-Z0-9]{10,12})-HERO/[^"]+\.jpg)',
        html
    ):
        sku = m.group(2)
        if sku not in img_map:
            img_map[sku] = m.group(1)

    # Collect EUR prices in order of appearance
    all_prices = []
    for m in re.finditer(r'(\d{2,3})[,.](\d{2})\s*€|€\s*(\d{2,3})[,.](\d{2})', html):
        val = float(f"{m.group(1)}.{m.group(2)}") if m.group(1) else float(f"{m.group(3)}.{m.group(4)}")
        all_prices.append(val)

    # Products: full SKU (10-12 chars) then name then /es-es/p/ URL
    # Pattern: "NF0A8GBTBOM","Product Name","/es-es/p/..."
    product_pattern = re.compile(
        r'"([A-Z0-9]{10,12})","([^"]{8,80})","(/es-es/p/[^"]+)"'
    )

    skip_words = ["mujer", "hombre", "niños", "equipment", "view all", "ver todo",
                  "este artículo", "available", "disponible"]
    price_idx = 0

    for m in product_pattern.finditer(html):
        if len(results) >= 20:
            break
        sku, name, url_path = m.group(1), m.group(2).strip(), m.group(3)

        if len(name) < 6:
            continue
        if any(w in name.lower() for w in skip_words):
            continue
        if name.lower() in seen:
            continue
        seen.add(name.lower())

        product_url = BASE + url_path
        image_url = img_map.get(sku)  # exact SKU match → correct image per product

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
