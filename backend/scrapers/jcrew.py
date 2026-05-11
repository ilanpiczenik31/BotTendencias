from .base import BaseScraper, ScrapedProduct, fetch_page, parse_price, find_image, find_link
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www.jcrew.com/c/womens_clothing/new_arrivals", "new_arrivals"),
    ("https://www.jcrew.com/c/mens_clothing/new_arrivals", "new_arrivals"),
]

PRODUCT_SELECTORS = [
    "[class*='product-tile']",
    "[class*='c-product-tile']",
    "[data-test='product-tile']",
    "li[class*='product']",
    "[class*='product-item']",
]

NAME_SELECTORS = [
    "[class*='product-name']",
    "[data-test='product-name']",
    "[class*='product-title']",
    "[class*='title']",
    "h2", "h3",
]

PRICE_SELECTORS = [
    "[data-test='product-price']",
    "[class*='price']",
]


class JCrewScraper(BaseScraper):
    store_name = "J.Crew"
    store_url = "https://www.jcrew.com/"
    country = "us"

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for url, section in SECTIONS:
            try:
                soup = await fetch_page(url, country="us", wait=5000)

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
                            currency="USD",
                            image_url=find_image(item),
                            product_url=find_link(item, "https://www.jcrew.com"),
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"J.Crew {url}: {e}")

        return products
