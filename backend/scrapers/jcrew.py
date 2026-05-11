from .base import BaseScraper, ScrapedProduct, fetch_page, extract_json_ld_products, find_image, find_link, parse_price
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www.jcrew.com/plp/womens/features/new-arrivals",   "new_arrivals_women"),
    ("https://www.jcrew.com/plp/mens/features/new-arrivals",     "new_arrivals_men"),
    ("https://www.jcrew.com/plp/womens/features/best-sellers",   "best_sellers_women"),
    ("https://www.jcrew.com/plp/mens/features/best-sellers",     "best_sellers_men"),
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
    "h2", "h3",
]

PRICE_SELECTORS = [
    "[data-test='product-price']",
    "[class*='price']",
]


class JCrewScraper(BaseScraper):
    store_name = "J.Crew"
    store_url = "https://www.jcrew.com/"

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for url, section in SECTIONS:
            try:
                soup = await fetch_page(url, country="us", wait=5000)
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
                                "currency": "USD",
                                "url": find_link(item, "https://www.jcrew.com") or url,
                            })

                for p in items_data[:30]:
                    if p["name"]:
                        products.append(ScrapedProduct(
                            name=p["name"], section=section,
                            price=p.get("price"), currency="USD",
                            image_url=p.get("image") or None,
                            product_url=p.get("url") or None,
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"J.Crew {url}: {e}")

        return products
