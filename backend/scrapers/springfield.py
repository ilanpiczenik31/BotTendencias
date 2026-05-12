from .base import BaseScraper, ScrapedProduct, fetch_page, extract_json_ld_products, find_image, find_link, parse_price
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www.springfield.com/es/mujer/", "new_arrivals_women"),
    ("https://www.springfield.com/es/hombre/", "new_arrivals_men"),
]

PRODUCT_SELECTORS = [
    "[class*='product-grid__item']", "[class*='product-item']",
    "[class*='product-card']", "li[class*='product']", "article[class*='product']",
]
NAME_SELECTORS = ["[class*='product-name']", "[class*='product-title']", "h2", "h3"]
PRICE_SELECTORS = ["[class*='price-current']", "[class*='price']"]


class SpringfieldScraper(BaseScraper):
    store_name = "Springfield"
    store_url = "https://www.springfield.com/es/"

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for url, section in SECTIONS:
            try:
                soup = await fetch_page(url, country="es", wait=6000, scroll=True)
                items_data = extract_json_ld_products(soup)

                if not items_data:
                    containers = []
                    for sel in PRODUCT_SELECTORS:
                        containers = soup.select(sel)
                        if containers:
                            break
                    for item in containers[:60]:
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
                                "name": name, "image": find_image(item),
                                "price": parse_price(price_raw), "currency": "EUR",
                                "url": find_link(item, "https://www.springfield.com") or url,
                            })

                for p in items_data[:60]:
                    if p["name"]:
                        products.append(ScrapedProduct(
                            name=p["name"], section=section,
                            price=p.get("price"), currency="EUR",
                            image_url=p.get("image") or None,
                            product_url=p.get("url") or None,
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"Springfield {url}: {e}")

        return products
