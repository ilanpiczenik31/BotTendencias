from .base import BaseScraper, ScrapedProduct, fetch_page, parse_price, find_image, find_link
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www.the-sting.com/en/new", "new_arrivals"),
    ("https://www.the-sting.com/en/women/new", "new_arrivals"),
    ("https://www.the-sting.com/en/men/new", "new_arrivals"),
]

PRODUCT_SELECTORS = [
    "[class*='product-tile']",
    "[class*='product-item']",
    "article[class*='product']",
    "li[class*='product']",
    "[class*='product-card']",
]

NAME_SELECTORS = [
    "[class*='product-name']",
    "[class*='product-title']",
    "h2", "h3",
]

PRICE_SELECTORS = [
    "[class*='price']",
    "[class*='product-price']",
]


class TheStingScraper(BaseScraper):
    store_name = "The Sting"
    store_url = "https://www.the-sting.com/"
    country = "nl"

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for url, section in SECTIONS:
            try:
                soup = await fetch_page(url, country="nl", wait=5000)

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
                            currency="EUR",
                            image_url=find_image(item),
                            product_url=find_link(item, "https://www.the-sting.com"),
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"The Sting {url}: {e}")

        return products
