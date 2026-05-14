import json
import re
from .base import BaseScraper, ScrapedProduct, fetch_page, fetch_page_static, parse_price
from .registry import REGISTRY
import logging

logger = logging.getLogger(__name__)

BASE = "https://shop.mango.com"


def _parse_mango_jld(soup, section_key: str) -> list[ScrapedProduct]:
    """Extract products from Mango JSON-LD (schema.org ItemList)."""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if data.get("@type") == "ItemList":
                results = []
                seen: set[str] = set()
                for entry in data.get("itemListElement", []):
                    if len(results) >= 20:
                        break
                    item = entry.get("item", entry)
                    if item.get("@type") != "Product":
                        continue
                    name = item.get("name", "").strip()
                    if not name or name.lower() in seen:
                        continue
                    seen.add(name.lower())
                    offers = item.get("offers", {})
                    image = item.get("image", "")
                    if isinstance(image, list):
                        image = image[0] if image else ""
                    price = offers.get("price")
                    url = offers.get("url") or item.get("url", "")
                    if url and not url.startswith("http"):
                        url = BASE + url
                    results.append(ScrapedProduct(
                        name=name, section=section_key,
                        price=float(price) if price is not None else None,
                        currency=offers.get("priceCurrency", "EUR"),
                        image_url=image or None,
                        product_url=url or None,
                        category="ropa",
                    ))
                if results:
                    return results
        except Exception:
            pass
    return []


def _parse_mango_next_data(soup, section_key: str) -> list[ScrapedProduct]:
    """Extract products from Mango Next.js __NEXT_DATA__ SSR state."""
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        return []
    try:
        data = json.loads(script.string)
        products = _walk_next_data(data)
        if not products:
            return []
        results = []
        seen: set[str] = set()
        for p in products:
            if len(results) >= 20:
                break
            name = p.get("name", "").strip()
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            image = p.get("image", "")
            if isinstance(image, list):
                image = image[0] if image else ""
            price = p.get("price")
            url = p.get("url", "")
            if url and not url.startswith("http"):
                url = BASE + url
            results.append(ScrapedProduct(
                name=name, section=section_key,
                price=float(price) if price else None,
                currency=p.get("currency", "EUR"),
                image_url=image or None,
                product_url=url or None,
                category="ropa",
            ))
        logger.info(f"Mango __NEXT_DATA__ [{section_key}]: {len(results)} products")
        return results
    except Exception as e:
        logger.debug(f"Mango __NEXT_DATA__ parse failed: {e}")
    return []


def _walk_next_data(obj, depth: int = 0, _seen: set | None = None) -> list[dict]:
    """Walk Next.js data looking for product-like objects."""
    if _seen is None:
        _seen = set()
    if depth > 12 or not isinstance(obj, (dict, list)):
        return []
    obj_id = id(obj)
    if obj_id in _seen:
        return []
    _seen.add(obj_id)

    results = []
    if isinstance(obj, list):
        for item in obj[:200]:
            results.extend(_walk_next_data(item, depth + 1, _seen))
    elif isinstance(obj, dict):
        name = str(obj.get("name", "")).strip()
        # Looks like a product: has name + price or image
        if (len(name) > 3 and
                ("price" in obj or "image" in obj or "images" in obj) and
                ("id" in obj or "sku" in obj or "url" in obj)):
            price = obj.get("price") or obj.get("salePrice")
            if isinstance(price, dict):
                price = price.get("value") or price.get("amount")
            image = obj.get("image") or obj.get("mainImage") or ""
            if isinstance(image, dict):
                image = image.get("url", "")
            url = obj.get("url") or obj.get("href") or ""
            if name:
                results.append({"name": name, "price": price, "image": image, "url": url, "currency": "EUR"})
                return results  # Don't recurse deeper into this product
        for v in obj.values():
            results.extend(_walk_next_data(v, depth + 1, _seen))
    return results


def _parse_mango_html(soup, section_key: str) -> list[ScrapedProduct]:
    """Parse Mango product grid HTML as last resort."""
    results = []
    # Mango uses various product container patterns
    items = (
        soup.select("article[class*='product']") or
        soup.select("[class*='product-item']") or
        soup.select("[class*='product-list'] li") or
        soup.select("li[class*='item']")
    )[:30]

    for item in items:
        name = None
        image_url = None
        product_url = None
        price = None

        # Name
        for sel in ["[class*='name']", "[class*='title']", "h2", "h3", "h4"]:
            el = item.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text and len(text) > 3:
                    name = text
                    break

        # Image
        for img in item.find_all("img"):
            src = (img.get("src") or img.get("data-src") or
                   img.get("data-lazy-src") or "")
            if src and ("mango" in src.lower() or "shop.mango" in src) and (
                    ".jpg" in src or ".webp" in src):
                image_url = src
                break

        # Link
        link = item.select_one("a[href]")
        if link:
            href = link.get("href", "")
            product_url = href if href.startswith("http") else BASE + href

        # Price
        for sel in ["[class*='price']", "[class*='amount']", "[class*='cost']"]:
            el = item.select_one(sel)
            if el:
                price = parse_price(el.get_text(strip=True))
                if price:
                    break

        if name:
            results.append(ScrapedProduct(
                name=name, section=section_key,
                price=price, currency="EUR",
                image_url=image_url,
                product_url=product_url,
                category="ropa",
            ))

    return results


class MangoScraper(BaseScraper):
    store_name = "Mango"
    store_url = "https://shop.mango.com/es/"

    def __init__(self, sections: list[dict] | None = None):
        self.sections = sections or REGISTRY.get("Mango", [])

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for sec in self.sections:
            url, section_key = sec["url"], sec["key"]
            soup = None

            # 1. Try static fetch (no render) — like H&M
            soup = await fetch_page_static(url, country="es")
            if soup:
                # Try JSON-LD first
                parsed = _parse_mango_jld(soup, section_key)
                if parsed:
                    logger.info(f"Mango JSON-LD static [{section_key}]: {len(parsed)} products")
                    products.extend(parsed)
                    continue
                # Try __NEXT_DATA__
                parsed = _parse_mango_next_data(soup, section_key)
                if parsed:
                    products.extend(parsed)
                    continue
                # Got HTML but no products — try render
                soup = None

            # 2. Fall back to rendered page
            if not soup:
                for wait_ms, use_premium in [(5000, False), (8000, True)]:
                    try:
                        soup = await fetch_page(url, country="es", wait=wait_ms, premium=use_premium)
                        parsed = _parse_mango_jld(soup, section_key)
                        if parsed:
                            logger.info(f"Mango JSON-LD render [{section_key}]: {len(parsed)} products")
                            products.extend(parsed)
                            soup = None
                            break
                        parsed = _parse_mango_next_data(soup, section_key)
                        if parsed:
                            products.extend(parsed)
                            soup = None
                            break
                        # Last resort: HTML grid
                        parsed = _parse_mango_html(soup, section_key)
                        if parsed:
                            logger.info(f"Mango HTML [{section_key}]: {len(parsed)} products")
                            products.extend(parsed[:20])
                            soup = None
                            break
                        logger.warning(f"Mango [{section_key}] render got page but no products (premium={use_premium})")
                        soup = None
                    except Exception:
                        logger.warning(f"Mango [{section_key}] render retry (premium={use_premium})")

            if not products and soup is None:
                logger.error(f"Mango [{section_key}] failed: {url}")

        return products
