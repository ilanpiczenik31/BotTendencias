from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from bs4 import BeautifulSoup, Tag
import asyncio
import httpx
import logging
import os
import re

logger = logging.getLogger(__name__)

SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "")
SCRAPER_API_BASE = "http://api.scraperapi.com"

# Free tier allows ~5 concurrent requests — use 3 to stay safe
_semaphore = asyncio.Semaphore(3)


@dataclass
class ScrapedProduct:
    name: str
    section: str  # new_arrivals | best_sellers | trending
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    price: Optional[float] = None
    currency: str = "EUR"
    category: Optional[str] = None


_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://www.zara.com/es/es/",
    "X-Requested-With": "XMLHttpRequest",
}


async def fetch_json_direct(url: str, extra_headers: dict | None = None) -> dict | list | None:
    """Fetch a JSON endpoint directly (no proxy) with browser-like headers."""
    headers = {**_BROWSER_HEADERS, **(extra_headers or {})}
    try:
        async with httpx.AsyncClient(timeout=20, headers=headers, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.debug(f"fetch_json_direct failed for {url}: {e}")
    return None


async def fetch_page_static(url: str, country: str = "es") -> BeautifulSoup | None:
    """Fetch raw SSR HTML via ScraperAPI (no JS rendering). Faster and returns SSR state."""
    params = {
        "api_key": SCRAPER_API_KEY,
        "url": url,
        "country_code": country,
    }
    async with _semaphore:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(SCRAPER_API_BASE, params=params)
                if resp.status_code == 200:
                    return BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            logger.debug(f"fetch_page_static failed: {e}")
    return None


async def fetch_json(url: str, country: str = "es") -> dict | list | None:
    """Fetch a JSON endpoint through ScraperAPI without browser rendering."""
    params = {
        "api_key": SCRAPER_API_KEY,
        "url": url,
        "country_code": country,
    }
    async with _semaphore:
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.get(SCRAPER_API_BASE, params=params)
                    if resp.status_code == 429:
                        await asyncio.sleep(10 * (attempt + 1))
                        continue
                    resp.raise_for_status()
                    return resp.json()
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(5)
                    continue
                logger.debug(f"fetch_json failed: {e}")
    return None


async def fetch_page(url: str, country: str = "es", wait: int = 3000, scroll: bool = False, premium: bool = False) -> BeautifulSoup:
    """Fetch a page through ScraperAPI with concurrency limiting and retry."""
    params = {
        "api_key": SCRAPER_API_KEY,
        "url": url,
        "render": "true",
        "country_code": country,
        "wait_for_selector": "body",
        "wait": str(wait),
    }
    if scroll:
        params["scroll"] = "true"
    if premium:
        params["premium"] = "true"
    async with _semaphore:
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=90) as client:
                    resp = await client.get(SCRAPER_API_BASE, params=params)
                    if resp.status_code == 429:
                        await asyncio.sleep(10 * (attempt + 1))
                        continue
                    resp.raise_for_status()
                    return BeautifulSoup(resp.text, "lxml")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < 2:
                    await asyncio.sleep(10 * (attempt + 1))
                    continue
                raise
        raise Exception(f"Failed after 3 attempts: {url}")


def parse_price(raw: Optional[str]) -> Optional[float]:
    if not raw:
        return None
    # Split on separators first to avoid joining "98 - 118" → "98118"
    parts = re.split(r"[-–—/]", raw)
    first = parts[0].strip()
    match = re.search(r"\d{1,4}(?:[.,]\d{1,2})?", first)
    if not match:
        return None
    try:
        value = float(match.group().replace(",", "."))
        return value if value < 9999 else None  # sanity cap
    except ValueError:
        return None


def find_image(tag: Tag) -> Optional[str]:
    for img in tag.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""
        if src and not src.endswith(".gif") and "placeholder" not in src.lower():
            return src if src.startswith("http") else None
    return None


def extract_json_ld_products(soup: BeautifulSoup, base_url: str = "") -> list[dict]:
    """Extract product list from JSON-LD structured data (schema.org ItemList)."""
    import json
    results = []
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
                    # Fix relative URLs
                    if url and not url.startswith("http") and base_url:
                        url = base_url.rstrip("/") + "/" + url.lstrip("/")
                    results.append({
                        "name": item.get("name", "").strip(),
                        "image": image,
                        "price": float(price) if price is not None else None,
                        "currency": offers.get("priceCurrency", "EUR"),
                        "url": url,
                    })
        except Exception:
            pass
    return results


def find_link(tag: Tag, base_url: str) -> Optional[str]:
    a = tag.find("a", href=True)
    if not a:
        return None
    href = a["href"]
    if href.startswith("http"):
        return href
    return base_url.rstrip("/") + "/" + href.lstrip("/")


class BaseScraper(ABC):
    store_name: str = ""
    store_url: str = ""
    country: str = "es"

    async def scrape(self) -> list[ScrapedProduct]:
        try:
            products = await self._scrape()
            seen: set[tuple] = set()
            unique = []
            for p in products:
                # Deduplicate only within the same section
                key = (p.name.strip().lower(), p.section)
                if key not in seen:
                    seen.add(key)
                    unique.append(p)
            removed = len(products) - len(unique)
            logger.info(f"[{self.store_name}] scraped {len(unique)} products" + (f" ({removed} dupes removed)" if removed else ""))
            return unique
        except Exception as e:
            logger.error(f"[{self.store_name}] scrape failed: {e}")
            return []

    @abstractmethod
    async def _scrape(self) -> list[ScrapedProduct]:
        ...
