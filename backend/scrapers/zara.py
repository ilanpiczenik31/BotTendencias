import json
import re
from .base import BaseScraper, ScrapedProduct, fetch_page, fetch_json
from .registry import REGISTRY
import logging

logger = logging.getLogger(__name__)

# Zara's internal product API — extracts category ID from URL like "l1180" or "l711"
def _category_id(url: str) -> str | None:
    m = re.search(r"-l(\d+)\.html", url)
    if m:
        return m.group(1)
    # fallback: last number segment before .html
    m = re.search(r"(\d+)\.html", url)
    return m.group(1) if m else None


async def _fetch_via_api(category_id: str, page_size: int = 40) -> list[dict]:
    """Call Zara's internal AJAX API to get products directly."""
    api_url = (
        f"https://www.zara.com/es/es/category/{category_id}/products"
        f"?ajax=true&page=0&pageSize={page_size}&sortBy=newest"
    )
    data = await fetch_json(api_url, country="es")
    if not data:
        return []

    products = []
    # Zara API returns either a list or {"productGroups": [...]} or {"products": [...]}
    items = data if isinstance(data, list) else data.get("products", data.get("productGroups", []))

    for item in items:
        # Handle productGroups nesting
        if "elements" in item:
            for elem in item.get("elements", []):
                for p in elem.get("commercialComponents", [elem]):
                    products.extend(_parse_zara_product(p))
        else:
            products.extend(_parse_zara_product(item))

    return products


def _parse_zara_product(p: dict) -> list[dict]:
    name = p.get("name", "").strip()
    if not name:
        return []

    price = None
    price_data = p.get("price")
    if isinstance(price_data, (int, float)):
        price = price_data / 100  # Zara stores price in cents
    elif isinstance(price_data, dict):
        raw = price_data.get("value") or price_data.get("current", {}).get("value")
        if raw:
            price = float(raw) / 100

    # Image
    image_url = None
    media = p.get("detail", {}).get("colors", [{}])[0].get("xmedia", [{}])[0] if p.get("detail") else {}
    if media:
        path = media.get("path", "")
        name_img = media.get("name", "")
        timestamp = media.get("timestamp", "")
        if path and name_img:
            image_url = f"https://static.zara.net/photos/{path}{name_img}/w/750/{name_img}.jpg?ts={timestamp}"

    # Fallback image from mainImgUrl
    if not image_url:
        image_url = p.get("mainImgUrl") or p.get("imageUrl")

    seo = p.get("seo", {})
    product_url = None
    if seo.get("keyword"):
        product_url = f"https://www.zara.com/es/es/{seo['keyword']}-p{p.get('id', '')}.html"

    return [{"name": name, "image": image_url, "price": price, "currency": "EUR", "url": product_url or ""}]


def _name_from_url(url: str) -> str:
    """Extract readable name from Zara product URL slug."""
    m = re.search(r"/([a-z][a-z0-9-]+)-p\d+\.html", url)
    if m:
        return m.group(1).replace("-", " ").title()
    return ""


def _parse_zara_html(soup, section_key: str) -> list[ScrapedProduct]:
    """
    Parse Zara HTML product grid. Two layouts exist:
    - Hombre "double": transparent-background img has product name in alt ("NAME - Color de Zara")
    - Mujer "zoom": product-link href contains name as slug (/vestido-midi-drapeado-p123.html)
    Image always comes from the first real JPG.
    """
    results = []
    for item in soup.select("li.product-grid-product")[:80]:
        name = None
        image_url = None
        product_url = None

        # Get product URL first
        link = item.select_one("a.product-link[href], a.media-region[href]")
        if link:
            product_url = link.get("href", "")
            if product_url and not product_url.startswith("http"):
                product_url = "https://www.zara.com" + product_url

        for img in item.find_all("img"):
            src = img.get("src", "")
            alt = img.get("alt", "").strip()

            # Strategy 1: transparent-background img has product name ("NAME - Color de Zara")
            if "transparent-background" in src and alt and " de Zara" in alt and "Imagen de producto" not in alt:
                candidate = alt.split(" - ")[0].strip()
                if len(candidate) > 3:
                    name = candidate

            # Real product image
            if ".jpg" in src and "static.zara.net" in src and "stdstatic" not in src and not image_url:
                image_url = src

        # Strategy 2: extract from URL slug if no name found yet
        if not name and product_url:
            name = _name_from_url(product_url)

        if name:
            results.append(ScrapedProduct(
                name=name, section=section_key,
                image_url=image_url, product_url=product_url,
                category="ropa",
            ))

    return results


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

    def __init__(self, sections: list[dict] | None = None):
        self.sections = sections or REGISTRY["Zara"]

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for sec in self.sections:
            url, section_key = sec["url"], sec["key"]
            try:
                # HTML scraping — no scroll (causes 500 on Zara)
                soup = await fetch_page(url, country="es", wait=6000)
                parsed = _parse_zara_html(soup, section_key)
                products.extend(parsed)
                logger.info(f"Zara HTML [{section_key}]: {len(parsed)} products")

            except Exception as e:
                logger.error(f"Zara [{section_key}] {url}: {e}")

        return products
