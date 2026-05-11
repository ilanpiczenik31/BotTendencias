from .base import BaseScraper, ScrapedProduct, fetch_page, extract_json_ld_products, find_image, find_link
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www.bershka.com/es/mujer/nuevo-l1558051.html", "new_arrivals"),
    ("https://www.bershka.com/es/hombre/nuevo-l1558080.html", "new_arrivals"),
]


class BershkaScraper(BaseScraper):
    store_name = "Bershka"
    store_url = "https://www.bershka.com/es/"

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for url, section in SECTIONS:
            try:
                soup = await fetch_page(url, country="es", wait=5000)
                items = extract_json_ld_products(soup)

                # Fallback: Bershka is Inditex, same structure as Zara
                if not items:
                    for item in soup.select("li.product-grid-product, li[class*='product']")[:30]:
                        img = item.select_one("img")
                        alt = img.get("alt", "") if img else ""
                        name = alt.split(" - ")[0].strip() if " - " in alt else alt.strip()
                        link = item.select_one("a[href]")
                        product_url = link["href"] if link else None
                        if product_url and not product_url.startswith("http"):
                            product_url = "https://www.bershka.com" + product_url
                        image_url = img.get("src") if img else None
                        if image_url and "transparent-background" in (image_url or ""):
                            image_url = None
                        if name:
                            items.append({"name": name, "image": image_url,
                                          "price": None, "currency": "EUR", "url": product_url or ""})

                for p in items[:30]:
                    if p["name"]:
                        products.append(ScrapedProduct(
                            name=p["name"],
                            section=section,
                            price=p.get("price"),
                            currency=p.get("currency", "EUR"),
                            image_url=p.get("image") or None,
                            product_url=p.get("url") or None,
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"Bershka {url}: {e}")

        return products
