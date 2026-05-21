"""
El Corte Inglés scraper — SSR page, no Cloudflare.
Products are embedded in a JSON data layer in the HTML.
Paginates to fetch ~50 products per section.
"""
import re
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

    # Pattern confirmed working: name then price.f_price in same object
    name_price = re.findall(
        r'"name":"([^"]{3,80})","price":\{"currency":"([^"]+)"[^}]*?"f_price":([\d.]+)',
        html
    )
    if not name_price:
        return []

    # code_a appears before each product (same count, same order)
    code_a_list = re.findall(r'"code_a":"([^"]+)"', html)

    # Product IDs (12-18 digit strings)
    id_list = re.findall(r'"id":"(\d{12,18})"', html)

    # Build product URL map from href links: /moda-mujer/A57120359-slug/
    url_map: dict[str, str] = {}
    for m in re.finditer(r'href="(/[^"]*?/([A-Z][0-9]{7,})[^"?]*)', html):
        code = m.group(2)
        if code not in url_map:
            url_map[code] = BASE + m.group(1)

    for i, (name, currency, f_price) in enumerate(name_price):
        name = name.strip()
        if not name or len(name) < 4 or name.lower() in seen:
            continue
        seen.add(name.lower())

        code_a = code_a_list[i] if i < len(code_a_list) else None
        prod_id = id_list[i] if i < len(id_list) else None

        results.append(ScrapedProduct(
            name=name,
            section=section_key,
            price=float(f_price) if f_price else None,
            currency=currency or "EUR",
            image_url=IMG_BASE.format(id=prod_id) if prod_id else None,
            product_url=url_map.get(code_a) if code_a else None,
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

            # Fetch multiple pages to reach ~50 products (24 per page)
            for page in range(1, 5):
                page_url = url if page == 1 else f"{url}?s[page]={page}"
                soup = await fetch_page_static(page_url, country="es")
                if not soup:
                    logger.warning(f"El Corte Inglés [{section_key}] page {page}: no response")
                    break

                parsed = _parse_eci_html(str(soup), section_key)
                if not parsed:
                    logger.warning(f"El Corte Inglés [{section_key}] page {page}: 0 products parsed")
                    break

                new_count = 0
                for p in parsed:
                    if p.name.lower() not in seen_names:
                        seen_names.add(p.name.lower())
                        section_products.append(p)
                        new_count += 1

                logger.info(f"El Corte Inglés [{section_key}] page {page}: {new_count} new (total: {len(section_products)})")

                if len(section_products) >= 50 or new_count == 0:
                    break

            products.extend(section_products[:50])
            logger.info(f"El Corte Inglés [{section_key}]: {len(section_products[:50])} products total")

        return products
