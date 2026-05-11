from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from bs4 import BeautifulSoup, Tag
import httpx
import asyncio
import logging
import os
import re

logger = logging.getLogger(__name__)

SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "")
SCRAPER_API_BASE = "http://api.scraperapi.com"


@dataclass
class ScrapedProduct:
    name: str
    section: str  # new_arrivals | best_sellers | trending
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    price: Optional[float] = None
    currency: str = "EUR"
    category: Optional[str] = None


async def fetch_page(url: str, country: str = "es", wait: int = 3000) -> BeautifulSoup:
    """Fetch a page through ScraperAPI (residential IPs + JS rendering)."""
    params = {
        "api_key": SCRAPER_API_KEY,
        "url": url,
        "render": "true",
        "country_code": country,
        "wait_for_selector": "body",
        "wait": str(wait),
    }
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.get(SCRAPER_API_BASE, params=params)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")


def parse_price(raw: Optional[str]) -> Optional[float]:
    if not raw:
        return None
    cleaned = re.sub(r"[^\d,.]", "", raw.replace(",", "."))
    # Take first number-like string
    match = re.search(r"\d+\.?\d*", cleaned)
    try:
        return float(match.group()) if match else None
    except ValueError:
        return None


def find_image(tag: Tag) -> Optional[str]:
    for img in tag.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""
        if src and not src.endswith(".gif") and "placeholder" not in src.lower():
            return src if src.startswith("http") else None
    return None


def extract_json_ld_products(soup: BeautifulSoup) -> list[dict]:
    """Extract product list from JSON-LD structured data (schema.org ItemList)."""
    import json
    results = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if data.get("@type") == "ItemList":
                for entry in data.get("itemListElement", []):
                    item = entry.get("item", entry)  # some sites nest, some don't
                    if item.get("@type") != "Product":
                        continue
                    offers = item.get("offers", {})
                    # image can be string or list
                    image = item.get("image", "")
                    if isinstance(image, list):
                        image = image[0] if image else ""
                    price = offers.get("price")
                    results.append({
                        "name": item.get("name", "").strip(),
                        "image": image,
                        "price": float(price) if price is not None else None,
                        "currency": offers.get("priceCurrency", "EUR"),
                        "url": offers.get("url") or item.get("url", ""),
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
            logger.info(f"[{self.store_name}] scraped {len(products)} products")
            return products
        except Exception as e:
            logger.error(f"[{self.store_name}] scrape failed: {e}")
            return []

    @abstractmethod
    async def _scrape(self) -> list[ScrapedProduct]:
        ...
