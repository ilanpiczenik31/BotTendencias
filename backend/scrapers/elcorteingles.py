"""
El Corte Inglés scraper — SSR page, no Cloudflare.
Products are embedded in a JSON data layer in the HTML.
Paginates to fetch ~50 products per section.
"""
import re
import json
from .base import BaseScraper, ScrapedProduct, fetch_page_static
from .registry import REGISTRY
import logging

logger = logging.getLogger(__name__)

BASE = "https://www.elcorteingles.es"
IMG_BASE = "https://dam.elcorteingles.es/producto/www-{id}-00.jpg"


def _parse_eci_html(html: str, section_key: str) -> list[ScrapedProduct]:
    """Extract products from ECI JSON data layer embedded in HTML."""
    results = []
    seen: set[str] = set()

    # Find the products JSON array in the data layer
    # Pattern: "products":[{"brand":...,"code_a":...,"id":...,"name":...,"price":{...}}]
    products_match = re.search(r'"products":\[(\{.+?\})\s*[,\]]', html, re.DOTALL)
    if not products_match:
        return []

    # Find ALL product objects in the full products array
    # Each product has: code_a, id, name, price.f_price
    product_pattern = re.compile(
        r'"code_a":"([^"]+)"[^}]*?"id":"(\d+)"[^}]*?"(?:media|name)"[^}]*?"name":"([^"]{3,80})"'
        r'[^}]*?"price":\{"currency":"([^"]+)"[^}]*?"f_price":([\d.]+)',
        re.DOTALL
    )

    # Build product URL map from href links
    url_map: dict[str, str] = {}
    for m in re.finditer(r'href="(/[^"]*?/([A-Z][0-9]{7,})[^"]*?)"', html):
        href, code = m.group(1), m.group(2)
        clean_url = href.split("?")[0]  # Remove query params
        if code not in url_map:
            url_map[code] = BASE + clean_url

    for m in product_pattern.finditer(html):
        code_a, prod_id, name, currency, f_price = (
            m.group(1), m.group(2), m.group(3).strip(),
            m.group(4), m.group(5)
        )

        if not name or name.lower() in seen:
            continue
        # Skip category navigation items
        if len(name) < 4:
            continue
        seen.add(name.lower())

        image_url = IMG_BASE.format(id=prod_id)
        product_url = url_map.get(code_a)

        try:
            price = float(f_price)
        except Exception:
            price = None

        results.append(ScrapedProduct(
            name=name,
            section=section_key,
            price=price,
            currency=currency or "EUR",
            image_url=image_url,
            product_url=product_url,
            category="ropa",
        ))

    return results


class ElCorteInglesScraper(BaseScraper):
    store_name = "El Corte Inglés"
    store_url = "https://www.elcorteingles.es/"

    def __init__(self, sections: list[dict] | None = None):
        self.sections = sections or REGISTRY.get("El Corte Inglés", [])

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for sec in self.sections:
            url, section_key = sec["url"], sec["key"]
            section_products: list[ScrapedProduct] = []
            seen_names: set[str] = set()

            # Fetch multiple pages to reach ~50 products
            for page in range(1, 5):  # pages 1-4 → up to ~96 products
                page_url = url if page == 1 else f"{url}?s[page]={page}"
                soup = await fetch_page_static(page_url, country="es")
                if not soup:
                    logger.warning(f"El Corte Inglés [{section_key}] page {page}: no response")
                    break

                parsed = _parse_eci_html(str(soup), section_key)
                if not parsed:
                    break  # No more products

                new_count = 0
                for p in parsed:
                    if p.name.lower() not in seen_names:
                        seen_names.add(p.name.lower())
                        section_products.append(p)
                        new_count += 1

                logger.info(f"El Corte Inglés [{section_key}] page {page}: {new_count} new products (total: {len(section_products)})")

                if len(section_products) >= 50:
                    break
                if new_count == 0:
                    break  # All products already seen, stop paginating

            products.extend(section_products[:50])
            logger.info(f"El Corte Inglés [{section_key}]: {len(section_products[:50])} products total")

        return products
