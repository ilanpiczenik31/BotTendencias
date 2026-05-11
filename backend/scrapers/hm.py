from .base import BaseScraper, ScrapedProduct, fetch_page, extract_json_ld_products
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www2.hm.com/es_es/mujer/novedades/ver-todo.html",       "new_arrivals_women"),
    ("https://www2.hm.com/es_es/hombre/novedades/ver-todo.html",      "new_arrivals_men"),
    ("https://www2.hm.com/es_es/mujer/mejores-ventas/ver-todo.html",  "best_sellers_women"),
    ("https://www2.hm.com/es_es/hombre/mejores-ventas/ver-todo.html", "best_sellers_men"),
]


class HMScraper(BaseScraper):
    store_name = "H&M"
    store_url = "https://www2.hm.com/es_es/"

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for url, section in SECTIONS:
            try:
                soup = await fetch_page(url, country="es", wait=5000)
                items = extract_json_ld_products(soup)

                if not items:
                    for img in soup.find_all("img", src=lambda s: s and "image.hm.com" in s):
                        alt = img.get("alt", "").strip()
                        name = alt.split("-")[0].strip() if "-" in alt else alt
                        if name:
                            items.append({"name": name, "image": img["src"],
                                          "price": None, "currency": "EUR", "url": ""})

                for p in items[:30]:
                    if p["name"]:
                        products.append(ScrapedProduct(
                            name=p["name"], section=section,
                            price=p.get("price"), currency=p.get("currency", "EUR"),
                            image_url=p.get("image") or None,
                            product_url=p.get("url") or None,
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"H&M {url}: {e}")

        return products
