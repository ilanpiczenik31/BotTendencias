from .base import BaseScraper, ScrapedProduct, fetch_page, extract_json_ld_products, find_image, find_link, parse_price
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www.the-sting.com/en/new", "new_arrivals"),
    ("https://www.the-sting.com/en/women", "new_arrivals"),
    ("https://www.the-sting.com/en/men", "new_arrivals"),
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

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for url, section in SECTIONS:
            try:
                soup = await fetch_page(url, country="nl", wait=5000)
                items_data = extract_json_ld_products(soup)

                if not items_data:
                    containers = []
                    for sel in PRODUCT_SELECTORS:
                        containers = soup.select(sel)
                        if containers:
                            break

                    for item in containers[:30]:
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
                                "currency": "EUR",
                                "url": find_link(item, "https://www.the-sting.com") or url,
                            })

                for p in items_data[:30]:
                    if p["name"]:
                        products.append(ScrapedProduct(
                            name=p["name"],
                            section=section,
                            price=p.get("price"),
                            currency="EUR",
                            image_url=p.get("image") or None,
                            product_url=p.get("url") or None,
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"The Sting {url}: {e}")

        return products
