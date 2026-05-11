from .base import BaseScraper, ScrapedProduct, fetch_page, parse_price, find_image, find_link
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www.bershka.com/es/mujer/nuevo-l1558051.html", "new_arrivals"),
    ("https://www.bershka.com/es/hombre/nuevo-l1558080.html", "new_arrivals"),
]

PRODUCT_SELECTORS = [
    "li.grid-item",
    "li[class*='product']",
    "article[class*='product']",
    "[class*='grid-card']",
    "[data-productid]",
]

NAME_SELECTORS = [
    "[class*='grid-card-element__title']",
    "[class*='product-title']",
    "[class*='product-name']",
    "h2", "h3",
]

PRICE_SELECTORS = [
    "[class*='price-item--regular']",
    "[class*='current-price']",
    "[class*='price']",
]


class BershkaScraper(BaseScraper):
    store_name = "Bershka"
    store_url = "https://www.bershka.com/es/"

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for url, section in SECTIONS:
            try:
                soup = await fetch_page(url, country="es", wait=5000)

                items = []
                for sel in PRODUCT_SELECTORS:
                    items = soup.select(sel)
                    if items:
                        break

                for item in items[:30]:
                    name = None
                    for sel in NAME_SELECTORS:
                        el = item.select_one(sel)
                        if el and el.get_text(strip=True):
                            name = el.get_text(strip=True)
                            break

                    price_raw = None
                    for sel in PRICE_SELECTORS:
                        el = item.select_one(sel)
                        if el:
                            price_raw = el.get_text(strip=True)
                            break

                    if name:
                        products.append(ScrapedProduct(
                            name=name,
                            section=section,
                            price=parse_price(price_raw),
                            image_url=find_image(item),
                            product_url=find_link(item, "https://www.bershka.com"),
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"Bershka {url}: {e}")

        return products
