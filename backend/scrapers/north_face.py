from .base import BaseScraper, ScrapedProduct, fetch_page, extract_json_ld_products, find_image, find_link, parse_price
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www.thenorthface.com/en-gb/mens", "new_arrivals"),
    ("https://www.thenorthface.com/en-gb/womens", "new_arrivals"),
]

PRODUCT_SELECTORS = [
    "[class*='product-tile']",
    "[class*='product-card']",
    "li[class*='product']",
    "[class*='product-item']",
    "[data-component='ProductTile']",
]

NAME_SELECTORS = [
    "[class*='product-name']",
    "[class*='product-title']",
    "[class*='title-']",
    "h2", "h3",
]

PRICE_SELECTORS = [
    "[class*='price']",
    "[class*='cost']",
]


class NorthFaceScraper(BaseScraper):
    store_name = "The North Face"
    store_url = "https://www.thenorthface.com/en-gb/"
    country = "gb"

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for url, section in SECTIONS:
            try:
                soup = await fetch_page(url, country="gb", wait=5000)
                items_data = extract_json_ld_products(soup)

                if not items_data:
                    # Try HTML selectors
                    containers = []
                    for sel in PRODUCT_SELECTORS:
                        containers = soup.select(sel)
                        if containers:
                            break

                    for item in containers[:25]:
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
                            items_data.append({
                                "name": name,
                                "image": find_image(item),
                                "price": parse_price(price_raw),
                                "currency": "GBP",
                                "url": find_link(item, "https://www.thenorthface.com") or url,
                            })

                for p in items_data[:25]:
                    if p["name"]:
                        products.append(ScrapedProduct(
                            name=p["name"],
                            section=section,
                            price=p.get("price"),
                            currency=p.get("currency", "GBP"),
                            image_url=p.get("image") or None,
                            product_url=p.get("url") or None,
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"North Face {url}: {e}")

        return products
