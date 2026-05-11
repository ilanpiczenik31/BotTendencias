from .base import BaseScraper, ScrapedProduct, fetch_page, parse_price, find_image, find_link
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www.elcorteingles.es/moda/mujer/novedades/", "new_arrivals"),
    ("https://www.elcorteingles.es/moda/hombre/novedades/", "new_arrivals"),
    ("https://www.elcorteingles.es/moda/mujer/tendencias/", "trending"),
]

PRODUCT_SELECTORS = [
    "[class*='c-product-card']",
    "[class*='product-card']",
    "[data-product]",
    "li[class*='product']",
    "[class*='product-item']",
]

NAME_SELECTORS = [
    "[class*='c-product-card__description-title']",
    "[class*='product-title']",
    "[class*='product-name']",
    "h2", "h3",
]

PRICE_SELECTORS = [
    "[class*='c-product-card__price']",
    "[class*='price-current']",
    "[class*='price']",
]


class ElCorteInglesScraper(BaseScraper):
    store_name = "El Corte Inglés"
    store_url = "https://www.elcorteingles.es/moda/"

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
                            product_url=find_link(item, "https://www.elcorteingles.es"),
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"El Corte Inglés {url}: {e}")

        return products
