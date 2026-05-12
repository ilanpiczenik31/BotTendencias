from .base import BaseScraper, ScrapedProduct, fetch_page, extract_json_ld_products
from .registry import REGISTRY
import logging

logger = logging.getLogger(__name__)


def _parse_bershka_html(soup, section_key: str) -> list[ScrapedProduct]:
    """Parse Bershka product grid after React hydration."""
    results = []
    selectors = ["li.grid-item", "[class*='product-card']", "[class*='product-grid-item']"]
    items = []
    for sel in selectors:
        items = soup.select(sel)
        if items:
            break

    for item in items[:60]:
        name = None
        for sel in ["[class*='product-card__title']", "[class*='product-name']", "h2", "h3"]:
            el = item.select_one(sel)
            if el and el.get_text(strip=True):
                name = el.get_text(strip=True)
                break

        img = item.select_one("img[src]")
        src = img.get("src", "") if img else ""
        image_url = src if src and "data:image" not in src else None

        link = item.select_one("a[href]")
        href = link.get("href", "") if link else ""
        product_url = href if href.startswith("http") else ("https://www.bershka.com" + href if href else None)

        if name and len(name) > 2:
            results.append(ScrapedProduct(
                name=name, section=section_key,
                image_url=image_url, product_url=product_url, category="ropa",
            ))
    return results


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
                # Bershka needs 15s for React to fully hydrate products
                soup = await fetch_page(url, country="es", wait=15000, scroll=True)
                items = extract_json_ld_products(soup)

                if not items:
                    html_items = _parse_bershka_html(soup, section_key)
                    if html_items:
                        products.extend(html_items)
                        continue

                    # Fallback: Inditex structure (same as Zara)
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
                        link = item.select_one("a[href]")
                        href = link["href"] if link else ""
                        product_url = href if href.startswith("http") else "https://www.bershka.com" + href
                        image_url = src if src and "transparent-background" not in src and "data:image" not in src else None
                        if name and len(name) > 2:
                            items.append({"name": name, "image": image_url,
                                          "price": None, "currency": "EUR", "url": product_url})

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
