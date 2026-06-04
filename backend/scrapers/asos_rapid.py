"""
ASOS scraper via RapidAPI (asos2.p.rapidapi.com).
Server-side call — no CORS issues, no ScraperAPI needed.

Supports multiple ASOS regional stores (UK/COM, España/ES, Alemania/DE).
Store config (store code, lang, currency, country) is read from section dicts,
so one scraper class handles all three regions.

ASOS is a multi-brand marketplace — products come from hundreds of brands
(Nike, ASOS own-label, Topshop, Missguided, etc.) sold through asos.com.
"""
import os
import httpx
import logging
from .base import BaseScraper, ScrapedProduct
from .registry import REGISTRY

logger = logging.getLogger(__name__)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "asos2.p.rapidapi.com"
BASE_URL = "https://asos2.p.rapidapi.com/products/v2/list"
PRODUCT_BASE = "https://www.asos.com"

HEADERS = {
    "x-rapidapi-host": RAPIDAPI_HOST,
    "x-rapidapi-key": RAPIDAPI_KEY,
}

# Default store config per ASOS regional store name
STORE_DEFAULTS: dict[str, dict] = {
    "ASOS":          {"store": "COM", "lang": "en-GB", "currency": "GBP", "country": "GB"},
    "ASOS España":   {"store": "ES",  "lang": "es-ES", "currency": "EUR", "country": "ES"},
    "ASOS Alemania": {"store": "DE",  "lang": "de-DE", "currency": "EUR", "country": "DE"},
}

# categoryId → section key mapping
CATEGORIES = {
    2623: "new_arrivals_women",
    2606: "new_arrivals_men",
}


def _build_params(category_id: int, store_cfg: dict, offset: int = 0, limit: int = 48) -> dict:
    return {
        "store":      store_cfg.get("store", "COM"),
        "lang":       store_cfg.get("lang", "en-GB"),
        "currency":   store_cfg.get("currency", "GBP"),
        "country":    store_cfg.get("country", "GB"),
        "categoryId": str(category_id),
        "sort":       "freshness",
        "limit":      str(limit),
        "offset":     str(offset),
    }


def _parse_product(item: dict, section_key: str, currency: str) -> ScrapedProduct | None:
    name = (item.get("name") or "").strip()
    if not name or len(name) < 3:
        return None

    brand = (item.get("brandName") or "").strip()
    full_name = f"{brand} — {name}" if brand and brand.lower() not in name.lower() else name

    # Image URL: API returns bare domain without https:// and without file extension
    raw_image = item.get("imageUrl") or ""
    if raw_image:
        if raw_image.startswith("http"):
            image_url = raw_image + "?$n_480w$"
        elif raw_image.startswith("//"):
            image_url = "https:" + raw_image + "?$n_480w$"
        else:
            image_url = "https://" + raw_image + "?$n_480w$"
    else:
        image_url = None

    # Product URL: API returns path without leading slash
    raw_url = item.get("url") or ""
    if raw_url:
        if raw_url.startswith("http"):
            product_url = raw_url
        elif raw_url.startswith("/"):
            product_url = PRODUCT_BASE + raw_url
        else:
            product_url = PRODUCT_BASE + "/" + raw_url
    else:
        product_url = None

    # Price
    price = None
    price_obj = item.get("price") or {}
    if isinstance(price_obj, dict):
        current = price_obj.get("current") or {}
        price = current.get("value")
    elif isinstance(price_obj, (int, float)):
        price = float(price_obj)

    return ScrapedProduct(
        name=full_name,
        section=section_key,
        price=float(price) if price is not None else None,
        currency=currency,
        image_url=image_url,
        product_url=product_url,
        category="ropa",
    )


class ASOSRapidScraper(BaseScraper):
    """
    Scraper for any ASOS regional store.
    store_name must match a key in STORE_DEFAULTS (e.g. "ASOS", "ASOS España", "ASOS Alemania").
    Store config is pulled from STORE_DEFAULTS, then overrideable per-section via section dict fields.
    """
    store_url = "https://www.asos.com/"

    def __init__(self, store_name: str = "ASOS", sections: list[dict] | None = None):
        self.store_name = store_name
        self._default_cfg = STORE_DEFAULTS.get(store_name, STORE_DEFAULTS["ASOS"])
        self.sections = sections or REGISTRY.get(store_name, [])

    async def _scrape(self) -> list[ScrapedProduct]:
        if not RAPIDAPI_KEY:
            logger.error(f"{self.store_name}: RAPIDAPI_KEY not set — skipping")
            return []

        products: list[ScrapedProduct] = []

        for sec in self.sections:
            section_key = sec["key"]

            # Resolve category ID from section dict or fall back via section key
            cat_id = sec.get("category_id") or next(
                (cid for cid, key in CATEGORIES.items() if key == section_key), None
            )
            if cat_id is None:
                logger.warning(f"{self.store_name} [{section_key}]: no category_id — skipping")
                continue

            # Merge default store config with any per-section overrides
            store_cfg = {**self._default_cfg, **{
                k: sec[k] for k in ("store", "lang", "currency", "country") if k in sec
            }}
            currency = store_cfg["currency"]

            section_products: list[ScrapedProduct] = []
            seen_names: set[str] = set()

            for page in range(3):
                offset = page * 48
                params = _build_params(int(cat_id), store_cfg, offset=offset, limit=48)

                try:
                    async with httpx.AsyncClient(timeout=20, headers=HEADERS) as client:
                        resp = await client.get(BASE_URL, params=params)
                        resp.raise_for_status()
                        data = resp.json()
                except Exception as e:
                    logger.error(f"{self.store_name} [{section_key}] fetch failed (offset={offset}): {e}")
                    break

                items = data.get("products") or []
                if not items:
                    logger.info(f"{self.store_name} [{section_key}] page {page + 1}: no products")
                    break

                new_count = 0
                for item in items:
                    p = _parse_product(item, section_key, currency)
                    if p and p.name.lower() not in seen_names:
                        seen_names.add(p.name.lower())
                        section_products.append(p)
                        new_count += 1

                logger.info(f"{self.store_name} [{section_key}] p{page + 1}: {new_count} new ({len(section_products)} total)")

                if len(section_products) >= 48 or new_count == 0:
                    break

            products.extend(section_products[:50])
            logger.info(f"{self.store_name} [{section_key}]: {len(section_products[:50])} saved")

        return products


# Convenience factory — each regional store is a distinct class instance
def make_asos_scraper(store_name: str):
    class _Scraper(ASOSRapidScraper):
        def __init__(self, sections=None):
            super().__init__(store_name=store_name, sections=sections)
    _Scraper.__name__ = f"ASOS{store_name.replace(' ', '')}Scraper"
    return _Scraper


ASOSUKScraper = make_asos_scraper("ASOS")
ASOSEspanaScraper = make_asos_scraper("ASOS España")
ASOSAlemaniaScraper = make_asos_scraper("ASOS Alemania")
