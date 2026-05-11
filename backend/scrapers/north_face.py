from .base import BaseScraper, ScrapedProduct, fetch_page, parse_price, find_image, find_link
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www.thenorthface.com/en-us/womens/new-arrivals", "new_arrivals"),
    ("https://www.thenorthface.com/en-us/mens/new-arrivals", "new_arrivals"),
    ("https://www.thenorthface.com/en-us/womens/best-sellers", "best_sellers"),
]

PRODUCT_SELECTORS = [
    "[class*='product-tile']",
    "[data-component='ProductTile']",
    "[class*='product-card']",
    "li[class*='product']",
    "[class*='product-item']",
]

NAME_SELECTORS = [
    "[class*='product-name']",
    "[class*='product-tile__name']",
    "[class*='product-title']",
    "h2", "h3",
]

PRICE_SELECTORS = [
    "[class*='product-tile__price']",
    "[class*='price']",
]


class NorthFaceScraper(BaseScraper):
    store_name = "The North Face"
    store_url = "https://www.thenorthface.com/en-us/"
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

                for item in items[:25]:
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
                            product_url=find_link(item, "https://www.thenorthface.com"),
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"North Face {url}: {e}")

        return products
