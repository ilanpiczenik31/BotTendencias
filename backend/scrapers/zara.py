import json
from .base import BaseScraper, ScrapedProduct, fetch_page
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www.zara.com/es/es/mujer-nuevo-l1180.html", "new_arrivals"),
    ("https://www.zara.com/es/es/hombre-nuevo-l837.html", "new_arrivals"),
]


def _extract_json_ld(soup) -> list[dict]:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if data.get("@type") == "ItemList":
                results = []
                for entry in data.get("itemListElement", []):
                    item = entry.get("item", {})
                    if item.get("@type") == "Product":
                        offers = item.get("offers", {})
                        results.append({
                            "name": item.get("name", ""),
                            "image": item.get("image", ""),
                            "price": offers.get("price"),
                            "currency": offers.get("priceCurrency", "EUR"),
                            "url": offers.get("url", ""),
                        })
                if results:
                    return results
        except Exception:
            pass
    return []


class ZaraScraper(BaseScraper):
    store_name = "Zara"
    store_url = "https://www.zara.com/es/"

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for url, section in SECTIONS:
            try:
                soup = await fetch_page(url, country="es", wait=5000)

                # Primary: JSON-LD structured data
                json_items = _extract_json_ld(soup)
                if json_items:
                    for p in json_items:
                        if p["name"]:
                            products.append(ScrapedProduct(
                                name=p["name"],
                                section=section,
                                price=float(p["price"]) if p["price"] else None,
                                currency=p["currency"],
                                image_url=p["image"] or None,
                                product_url=p["url"] or None,
                                category="ropa",
                            ))
                    continue

                # Fallback: HTML selectors using known structure
                for item in soup.select("li.product-grid-product")[:30]:
                    img = item.select_one("img.media-image__image")
                    name = None
                    if img:
                        alt = img.get("alt", "")
                        # alt format: "PRODUCT NAME - Color de Zara"
                        name = alt.split(" - ")[0].strip() if " - " in alt else alt.strip()

                    link = item.select_one("a.product-link")
                    product_url = link.get("href") if link else None

                    image_url = img.get("src") if img else None
                    if image_url and "transparent-background" in image_url:
                        image_url = None

                    if name:
                        products.append(ScrapedProduct(
                            name=name,
                            section=section,
                            image_url=image_url,
                            product_url=product_url,
                            category="ropa",
                        ))

            except Exception as e:
                logger.error(f"Zara {url}: {e}")

        return products
