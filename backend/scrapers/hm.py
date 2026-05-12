import json
from .base import BaseScraper, ScrapedProduct, fetch_page
import logging

logger = logging.getLogger(__name__)

BASE = "https://www2.hm.com"

SECTIONS = [
    ("https://www2.hm.com/es_es/mujer/novedades/ver-todo.html",  "new_arrivals_women"),
    ("https://www2.hm.com/es_es/hombre/novedades/ver-todo.html", "new_arrivals_men"),
]


def _parse_hm(soup, section_key: str) -> list[ScrapedProduct]:
    """
    H&M uses obfuscated CSS classes — can't use selectors.
    1. JSON-LD ItemList → names, images, prices, urls
    2. a[href*=productpage] → product URLs by position if JSON-LD has no URLs
    3. Fallback: img[alt] from image.hm.com + links
    """
    # 1. JSON-LD
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
                    jld_products.append({
                        "name": item.get("name", "").strip(),
                        "image": image,
                        "price": float(price) if price is not None else None,
                        "currency": offers.get("priceCurrency", "EUR"),
                        "url": url,
                    })
        except Exception:
            pass

    # 2. Product page links from HTML (hrefs are NOT obfuscated)
    seen_links: set[str] = set()
    product_links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "productpage" in href:
            full = href if href.startswith("http") else BASE + href
            if full not in seen_links:
                seen_links.add(full)
                product_links.append(full)

    logger.debug(f"H&M [{section_key}]: {len(jld_products)} JSON-LD products, {len(product_links)} links")

    # 3. Merge
    results = []
    if jld_products:
        for i, p in enumerate(jld_products[:60]):
            if not p["name"]:
                continue
            url = p["url"] or (product_links[i] if i < len(product_links) else None)
            results.append(ScrapedProduct(
                name=p["name"], section=section_key,
                price=p["price"], currency=p["currency"],
                image_url=p["image"] or None,
                product_url=url or None,
                category="ropa",
            ))
        return results

    # Fallback: img alt + links by position
    imgs = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "").strip()
        if "image.hm.com" in src and alt and len(alt) > 3:
            name = alt.split("-")[0].strip()
            if name:
                imgs.append({"name": name, "image": src})

    for i, p in enumerate(imgs[:60]):
        url = product_links[i] if i < len(product_links) else None
        results.append(ScrapedProduct(
            name=p["name"], section=section_key,
            image_url=p["image"], product_url=url,
            category="ropa",
        ))

    return results


class HMScraper(BaseScraper):
    store_name = "H&M"
    store_url = "https://www2.hm.com/es_es/"

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []
        for url, section in SECTIONS:
            try:
                soup = await fetch_page(url, country="es", wait=5000, scroll=True)
                parsed = _parse_hm(soup, section)
                products.extend(parsed)
                logger.info(f"H&M [{section}]: {len(parsed)} products")
            except Exception as e:
                logger.error(f"H&M {url}: {e}")
        return products
