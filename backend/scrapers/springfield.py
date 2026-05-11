from .base import BaseScraper, ScrapedProduct, fetch_page, parse_price, find_image, find_link
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www.springfield.com/es/hombre/novedades/", "new_arrivals"),
    ("https://www.springfield.com/es/mujer/novedades/", "new_arrivals"),
]

PRODUCT_SELECTORS = [
    "[class*='product-grid__item']",
    "[class*='product-item']",
    "[class*='product-card']",
    "li[class*='product']",
    "article[class*='product']",
]

NAME_SELECTORS = [
    "[class*='product-item__name']",
    "[class*='product-name']",
    "[class*='product-title']",
    "h2", "h3",
]

PRICE_SELECTORS = [
    "[class*='product-item__price']",
    "[class*='price-current']",
    "[class*='price']",
]


class SpringfieldScraper(BaseScraper):
    store_name = "Springfield"
    store_url = "https://www.springfield.com/es/"

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
                            product_url=find_link(item, "https://www.springfield.com"),
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"Springfield {url}: {e}")

        return products
