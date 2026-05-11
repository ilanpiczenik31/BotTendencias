from .base import BaseScraper, ScrapedProduct, fetch_page, parse_price, find_image, find_link
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www2.hm.com/es_es/mujer/novedades/ver-todo.html", "new_arrivals"),
    ("https://www2.hm.com/es_es/hombre/novedades/ver-todo.html", "new_arrivals"),
]

PRODUCT_SELECTORS = [
    "li.product-item",
    "article.product-item",
    "li[class*='product']",
    "[data-articlecode]",
    "[class*='product-tile']",
]

NAME_SELECTORS = [
    "h2.item-heading a",
    "[class*='item-heading']",
    "[class*='product-title']",
    "[class*='product-name']",
    "h2", "h3",
]

PRICE_SELECTORS = [
    "span.price.regular",
    "[class*='price-value']",
    "[class*='product-price']",
    "[class*='price']",
]


class HMScraper(BaseScraper):
    store_name = "H&M"
    store_url = "https://www2.hm.com/es_es/"

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

                    img = find_image(item)
                    if img and img.startswith("//"):
                        img = "https:" + img

                    if name:
                        products.append(ScrapedProduct(
                            name=name,
                            section=section,
                            price=parse_price(price_raw),
                            image_url=img,
                            product_url=find_link(item, "https://www2.hm.com"),
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"H&M {url}: {e}")

        return products
