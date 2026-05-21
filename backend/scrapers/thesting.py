"""
The Sting scraper — SFCC (Salesforce Commerce Cloud) platform.
Uses the SFCC Ajax endpoint directly — no ScraperAPI needed, completely free.
Products are in data-gtm-items JSON attributes with name, price, brand, URL.
"""
import json
import re
from .base import BaseScraper, ScrapedProduct
from .registry import REGISTRY
import httpx
import logging

logger = logging.getLogger(__name__)

BASE = "https://www.thesting.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
    "X-Requested-With": "XMLHttpRequest",
}

SFCC_BASE = "https://www.thesting.com/on/demandware.store/Sites-TheSting-Site/nl_NL"


def _sfcc_url(category_id: str, sz: int = 60) -> str:
    return f"{SFCC_BASE}/Search-ShowAjax?cgid={category_id}&prefn1=eligibleForPLP&prefv1=true&sz={sz}&start=0&sortingRule=new-days-available"


def _parse_sting_html(html: str, section_key: str) -> list[ScrapedProduct]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    results = []
    seen: set[str] = set()

    # Build image map: extract ALL xcdn image URLs from HTML, map by product code
    # Images appear as: https://thesting.xcdn.nl/439539-ORA_F05.jpg (various _Fxx codes)
    # Product code = everything before _F (dots converted to dashes in image names)
    img_map: dict[str, str] = {}
    for m in re.finditer(r'https://thesting\.xcdn\.nl/(\d{6}-[A-Z0-9.-]+)_F\d+\.jpg', html):
        full_url = m.group(0)
        img_code = m.group(1)  # e.g. "439539-ORA" or "445412-BLW-D"
        if img_code not in img_map:
            img_map[img_code] = full_url

    # Also build URL map from href links
    url_map: dict[str, str] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/nl-nl/" in href and ".html" in href:
            # Extract product code from URL like /nl-nl/dames/.../439539-ORA.html
            m = re.search(r"/(\d{6}-[A-Z0-9.]+)\.html", href)
            if m:
                code = m.group(1)
                if code not in url_map:
                    url_map[code] = BASE + href if not href.startswith("http") else href

    # Parse products from data-gtm-items attributes
    for tile in soup.find_all(attrs={"data-gtm-items": True}):
        raw = tile.get("data-gtm-items", "")
        # Unescape HTML entities
        raw = raw.replace("&quot;", '"').replace("&amp;", "&")
        try:
            items = json.loads(raw)
        except Exception:
            continue

        for item in items:
            if len(results) >= 50:
                break
            name = item.get("item_name", "").strip()
            if not name or name.lower() in seen:
                continue
            # Skip campaign looks (not individual products)
            if "campaign-look" in item.get("item_id", "").lower():
                continue
            seen.add(name.lower())

            pid = item.get("item_id", "")
            price = item.get("price")
            currency = item.get("currency", "EUR")
            product_url = url_map.get(pid)

            # Look up image: product ID uses dots (BLW.D), image map uses dashes (BLW-D)
            img_code = pid.replace(".", "-")
            image_url = img_map.get(img_code) or img_map.get(pid)

            results.append(ScrapedProduct(
                name=name,
                section=section_key,
                price=float(price) if price is not None else None,
                currency=currency,
                image_url=image_url,
                product_url=product_url,
                category="ropa",
            ))

    return results


class TheStingScraper(BaseScraper):
    store_name = "The Sting"
    store_url = "https://www.thesting.com/nl-nl/"

    def __init__(self, sections: list[dict] | None = None):
        self.sections = sections or REGISTRY.get("The Sting", [])

    async def _scrape(self) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        for sec in self.sections:
            category_id = sec.get("category_id") or sec["key"]
            section_key = sec["key"]
            url = _sfcc_url(category_id)

            try:
                async with httpx.AsyncClient(timeout=30, headers=HEADERS, follow_redirects=True) as client:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    html = resp.text
            except Exception as e:
                logger.error(f"The Sting [{section_key}] fetch failed: {e}")
                continue

            parsed = _parse_sting_html(html, section_key)
            if parsed:
                logger.info(f"The Sting [{section_key}]: {len(parsed)} products")
                products.extend(parsed)
            else:
                logger.warning(f"The Sting [{section_key}]: 0 products")

        return products
