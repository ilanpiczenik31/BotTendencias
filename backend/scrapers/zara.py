from .base import BaseScraper, ScrapedProduct, fetch_page, parse_price, find_image, find_link
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www.zara.com/es/es/mujer-nuevo-l1180.html", "new_arrivals"),
    ("https://www.zara.com/es/es/hombre-nuevo-l837.html", "new_arrivals"),
]

# Candidate selectors tried in order
PRODUCT_SELECTORS = [
    "li.product-grid-product",
    "li[class*='product']",
    "article[class*='product']",
    "div[class*='product-grid'] li",
    "[data-productid]",
]

NAME_SELECTORS = [
    "[class*='product-grid-product-info__name']",
    "[class*='product-name']",
    "h2", "h3",
]

PRICE_SELECTORS = [
    "[class*='money-amount__main']",
    "[class*='price-current']",
    "[class*='price']",
    "span[class*='amount']",
]


class ZaraScraper(BaseScraper):
    store_name = "Zara"
    store_url = "https://www.zara.com/es/"

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
                            product_url=find_link(item, "https://www.zara.com"),
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"Zara {url}: {e}")

        return products
