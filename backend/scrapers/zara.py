import json
import re
from .base import BaseScraper, ScrapedProduct, fetch_page, fetch_json, fetch_json_direct
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
    """Call Zara's internal AJAX API to get products directly (no proxy needed for JSON)."""
    api_url = (
        f"https://www.zara.com/es/es/category/{category_id}/products"
        f"?ajax=true&page=0&pageSize={page_size}&sortBy=newest"
    )
    # Try direct call first (no ScraperAPI — Zara's JSON API works with browser headers)
    data = await fetch_json_direct(api_url, extra_headers={"Referer": "https://www.zara.com/es/es/"})
    if not data:
        # Fallback through ScraperAPI proxy
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

    # Image — try media first, then direct fields
    image_url = p.get("mainImgUrl") or p.get("imageUrl")
    try:
        media = p.get("detail", {}).get("colors", [{}])[0].get("xmedia", [{}])[0]
        if media:
            path = media.get("path", "").strip("/")
            name_img = media.get("name", "")
            timestamp = media.get("timestamp", "")
            if path and name_img:
                image_url = f"https://static.zara.net/photos/{path}/{name_img}/1/w/750/{name_img}.jpg?ts={timestamp}"
    except Exception:
        pass

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
            # src may be empty due to lazy loading — also check data-src and srcset
            src = img.get("src", "") or img.get("data-src", "")
            srcset = img.get("srcset", "") or img.get("data-srcset", "")
            alt = img.get("alt", "").strip()

            # Pick best URL: prefer src, then first entry in srcset
            best_src = src
            if not best_src and srcset:
                best_src = srcset.split(",")[0].strip().split(" ")[0]

            # Strategy 1: transparent-background img has product name ("NAME - Color de Zara")
            if "transparent-background" in best_src and alt and " de Zara" in alt and "Imagen de producto" not in alt:
                candidate = alt.split(" - ")[0].strip()
                if len(candidate) > 3:
                    name = candidate

            # Real product image (static.zara.net JPG)
            if not image_url and best_src and ".jpg" in best_src and "static.zara.net" in best_src and "stdstatic" not in best_src:
                image_url = best_src

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


def _extract_next_data(soup) -> list[dict]:
    """Extract products from Next.js __NEXT_DATA__ embedded JSON."""
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        return []
    try:
        data = json.loads(script.string)
        products = []
        # Walk the props tree looking for product arrays
        def find_products(obj, depth=0):
            if depth > 10 or not isinstance(obj, (dict, list)):
                return
            if isinstance(obj, list):
                for item in obj:
                    find_products(item, depth + 1)
            elif isinstance(obj, dict):
                name = obj.get("name", "").strip()
                # Looks like a product if it has a name + price or image
                if name and len(name) > 3 and ("price" in obj or "xmedia" in obj or "seo" in obj):
                    products.extend(_parse_zara_product(obj))
                for v in obj.values():
                    find_products(v, depth + 1)
        find_products(data)
        # Deduplicate by name
        seen = set()
        unique = []
        for p in products:
            if p["name"] not in seen:
                seen.add(p["name"])
                unique.append(p)
        return unique
    except Exception as e:
        logger.debug(f"__NEXT_DATA__ parse failed: {e}")
    return []


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

            # 1. Try internal Zara API first — returns prices + images reliably
            cat_id = _category_id(url)
            if cat_id:
                try:
                    api_items = await _fetch_via_api(cat_id, page_size=40)
                    if api_items:
                        for p in api_items[:40]:
                            if p.get("name"):
                                products.append(ScrapedProduct(
                                    name=p["name"], section=section_key,
                                    price=p.get("price"), currency="EUR",
                                    image_url=p.get("image") or None,
                                    product_url=p.get("url") or None,
                                    category="ropa",
                                ))
                        logger.info(f"Zara API [{section_key}]: {len(api_items)} products")
                        continue
                except Exception as e:
                    logger.warning(f"Zara API [{section_key}] failed ({e}), falling back to HTML")

            # 2. Fallback: HTML scraping — use premium proxy to bypass Cloudflare
            soup = None
            for wait_ms, use_premium in [(6000, False), (8000, True)]:
                try:
                    soup = await fetch_page(url, country="es", wait=wait_ms, premium=use_premium)
                    break
                except Exception:
                    logger.warning(f"Zara [{section_key}] HTML retry (premium={use_premium}, wait={wait_ms}ms)")

            if not soup:
                logger.error(f"Zara [{section_key}] failed after retries: {url}")
                continue

            try:
                # Try __NEXT_DATA__ first (full product data with prices)
                next_items = _extract_next_data(soup)
                if next_items:
                    for p in next_items[:40]:
                        if p.get("name"):
                            products.append(ScrapedProduct(
                                name=p["name"], section=section_key,
                                price=p.get("price"), currency="EUR",
                                image_url=p.get("image") or None,
                                product_url=p.get("url") or None,
                                category="ropa",
                            ))
                    logger.info(f"Zara __NEXT_DATA__ [{section_key}]: {len(next_items)} products")
                else:
                    # Fall back to HTML grid parsing
                    parsed = _parse_zara_html(soup, section_key)
                    products.extend(parsed)
                    logger.info(f"Zara HTML [{section_key}]: {len(parsed)} products")
            except Exception as e:
                logger.error(f"Zara [{section_key}] parse error: {e}")

        return products
