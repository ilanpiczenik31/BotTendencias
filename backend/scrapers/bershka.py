from .base import BaseScraper, ScrapedProduct, fetch_page, fetch_json, extract_json_ld_products
from .registry import REGISTRY
import re
import logging

logger = logging.getLogger(__name__)

# Inditex API format for Bershka
# URL like "novedades-n3745.html" → section ID 3745
def _section_id(url: str) -> str | None:
    m = re.search(r"-n(\d+)\.html", url)
    return m.group(1) if m else None


async def _fetch_bershka_api(section_id: str) -> list[dict]:
    """Try Bershka's internal catalog API (same Inditex infrastructure as Zara)."""
    candidates = [
        f"https://www.bershka.com/es/es/category/{section_id}/products?ajax=true&page=0&pageSize=40",
        f"https://www.bershka.com/es/category/{section_id}/products?ajax=true&page=0&pageSize=40",
    ]
    for api_url in candidates:
        data = await fetch_json(api_url, country="es")
        if not data:
            continue
        products = []
        items = data if isinstance(data, list) else data.get("products", data.get("productGroups", []))
        for item in (items or []):
            if "elements" in item:
                for elem in item.get("elements", []):
                    for p in elem.get("commercialComponents", [elem]):
                        name = p.get("name", "").strip()
                        if name:
                            products.append({
                                "name": name,
                                "image": None,
                                "price": None,
                                "currency": "EUR",
                                "url": "",
                            })
            else:
                name = item.get("name", "").strip()
                if name:
                    products.append({
                        "name": name,
                        "image": None,
                        "price": None,
                        "currency": "EUR",
                        "url": "",
                    })
        if products:
            logger.info(f"Bershka API returned {len(products)} products for section {section_id}")
            return products
    return []


class BershkaScraper(BaseScraper):
    store_name = "Bershka"
    store_url = "https://www.bershka.com/es/"

    def __init__(self, sections: list[dict] | None = None):
        self.sections = sections or REGISTRY["Bershka"]

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for sec in self.sections:
            url, section_key = sec["url"], sec["key"]
            try:
                # 1. Try internal API first
                sec_id = _section_id(url)
                if sec_id:
                    api_items = await _fetch_bershka_api(sec_id)
                    if api_items:
                        for p in api_items[:60]:
                            if p["name"]:
                                products.append(ScrapedProduct(
                                    name=p["name"], section=section_key,
                                    price=p.get("price"), currency="EUR",
                                    image_url=p.get("image") or None,
                                    product_url=p.get("url") or None,
                                    category="ropa",
                                ))
                        continue

                # 2. Fallback: HTML with shorter wait (saves credits if blocked)
                soup = await fetch_page(url, country="es", wait=8000)
                items = extract_json_ld_products(soup)

                if not items:
                    # Inditex HTML structure (same as Zara)
                    for item in soup.select("li.product-grid-product")[:60]:
                        img = item.select_one("img")
                        src = img.get("src", "") if img else ""
                        alt = img.get("alt", "").strip() if img else ""
                        if "transparent-background" in src and " de Bershka" in alt:
                            name = alt.split(" - ")[0].strip()
                        elif alt and len(alt) > 3:
                            name = alt.split(" - ")[0].strip()
                        else:
                            name = None
                        link = item.select_one("a.product-link[href], a[href]")
                        href = link["href"] if link else ""
                        if href and not href.startswith("http"):
                            href = "https://www.bershka.com" + href
                        image_url = src if src and "transparent-background" not in src and "data:image" not in src else None
                        if name and len(name) > 2:
                            items.append({"name": name, "image": image_url,
                                          "price": None, "currency": "EUR", "url": href})

                for p in items[:60]:
                    if p.get("name") and len(p["name"]) > 2:
                        products.append(ScrapedProduct(
                            name=p["name"], section=section_key,
                            price=p.get("price"), currency=p.get("currency", "EUR"),
                            image_url=p.get("image") or None,
                            product_url=p.get("url") or None,
                            category="ropa",
                        ))
            except Exception as e:
                logger.error(f"Bershka [{section_key}] {url}: {e}")

        return products
