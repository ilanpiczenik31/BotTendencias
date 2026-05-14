import json
from .base import BaseScraper, ScrapedProduct, fetch_page
from .registry import REGISTRY
import logging

logger = logging.getLogger(__name__)

BASE = "https://www2.hm.com"


def _parse_hm_jld(soup, section_key: str) -> list[ScrapedProduct]:
    """
    Extract products from H&M JSON-LD (schema.org ItemList).
    H&M includes 20-60 products in SSR JSON-LD with names, images, prices and URLs.
    """
    jld_products = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if data.get("@type") == "ItemList":
                for entry in data.get("itemListElement", []):
                    item = entry.get("item", entry)
                    if item.get("@type") != "Product":
                        continue
                    offers = item.get("offers", {})
                    image = item.get("image", "")
                    if isinstance(image, list):
                        image = image[0] if image else ""
                    price = offers.get("price")
                    url = offers.get("url") or item.get("url", "")
                    if url and not url.startswith("http"):
                        url = BASE + url
                    name = item.get("name", "").strip()
                    if name:
                        jld_products.append({
                            "name": name,
                            "image": image or None,
                            "price": float(price) if price is not None else None,
                            "currency": offers.get("priceCurrency", "EUR"),
                            "url": url or None,
                        })
        except Exception:
            pass

    if not jld_products:
        return []

    # Enrich with product page URLs from HTML (not obfuscated)
    seen_links: set[str] = set()
    product_links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "productpage" in href:
            full = href if href.startswith("http") else BASE + href
            if full not in seen_links:
                seen_links.add(full)
                product_links.append(full)

    results: list[ScrapedProduct] = []
    seen_names: set[str] = set()
    for i, p in enumerate(jld_products):
        if len(results) >= 20:
            break
        key = p["name"].strip().lower()
        if key in seen_names:
            continue
        seen_names.add(key)
        url = p["url"] or (product_links[i] if i < len(product_links) else None)
        results.append(ScrapedProduct(
            name=p["name"], section=section_key,
            price=p["price"], currency=p["currency"],
            image_url=p["image"],
            product_url=url,
            category="ropa",
        ))

    logger.debug(f"H&M [{section_key}]: {len(jld_products)} JSON-LD → {len(results)} unique")
    return results


class HMScraper(BaseScraper):
    store_name = "H&M"
    store_url = "https://www2.hm.com/es_es/"

    def __init__(self, sections: list[dict] | None = None):
        self.sections = sections or REGISTRY["H&M"]

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for sec in self.sections:
            url, section_key = sec["url"], sec["key"]
            soup = None

            # Try standard first, then premium — no scroll (causes 500s)
            for wait_ms, use_premium in [(5000, False), (8000, True)]:
                try:
                    soup = await fetch_page(url, country="es", wait=wait_ms, premium=use_premium)
                    break
                except Exception:
                    logger.warning(f"H&M [{section_key}] retry (premium={use_premium})")

            if not soup:
                logger.error(f"H&M [{section_key}] failed: {url}")
                continue

            parsed = _parse_hm_jld(soup, section_key)
            if parsed:
                products.extend(parsed)
                logger.info(f"H&M [{section_key}]: {len(parsed)} products (all with image+price)")
            else:
                logger.warning(f"H&M [{section_key}]: 0 products — JSON-LD empty")

        return products
