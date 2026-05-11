from .base import BaseScraper, ScrapedProduct, fetch_page, extract_json_ld_products, parse_price
import logging

logger = logging.getLogger(__name__)

SECTIONS = [
    ("https://www.elcorteingles.es/moda-mujer/", "new_arrivals"),
    ("https://www.elcorteingles.es/moda-hombre/", "new_arrivals"),
]


class ElCorteInglesScraper(BaseScraper):
    store_name = "El Corte Inglés"
    store_url = "https://www.elcorteingles.es/"

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for url, section in SECTIONS:
            try:
                soup = await fetch_page(url, country="es", wait=5000)

                # Try JSON-LD first
                items = extract_json_ld_products(soup)

                # Fallback: pair h2/h3 product names with their nearest image
                if not items:
                    cdn = "cdn.grupoelcorteingles.es"
                    imgs = {
                        img.get("alt", "").strip(): img.get("src", "")
                        for img in soup.find_all("img")
                        if cdn in (img.get("src") or "")
                    }
                    for h in soup.find_all(["h2", "h3"]):
                        name = h.get_text(strip=True)
                        if len(name) > 10:
                            # Try to find price nearby
                            parent = h.parent
                            price_el = parent.find(class_=lambda c: c and "price" in c.lower()) if parent else None
                            price = parse_price(price_el.get_text(strip=True)) if price_el else None
                            # Match image by alt text similarity
                            image_url = None
                            for alt, src in imgs.items():
                                if any(word in alt.lower() for word in name.lower().split()[:3]):
                                    image_url = "https:" + src if src.startswith("//") else src
                                    break
                            items.append({
                                "name": name,
                                "image": image_url,
                                "price": price,
                                "currency": "EUR",
                                "url": url,
                            })

                for p in items[:30]:
                    if p["name"]:
                        img = p.get("image")
                        if img and img.startswith("//"):
                            img = "https:" + img
                        products.append(ScrapedProduct(
                            name=p["name"],
                            section=section,
                            price=p.get("price"),
                            currency="EUR",
                            image_url=img or None,
                            product_url=p.get("url") or url,
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"El Corte Inglés {url}: {e}")

        return products
