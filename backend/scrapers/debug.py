import json as json_lib
from .base import fetch_page
from bs4 import BeautifulSoup


async def inspect_page(url: str, wait: int = 5000) -> dict:
    """Fetch page via ScraperAPI and return structure info for selector debugging."""
    try:
        soup = await fetch_page(url, wait=wait)

        # Count repeated classes
        class_count: dict[str, int] = {}
        for el in soup.find_all(True):
            for c in el.get("class", []):
                class_count[c] = class_count.get(c, 0) + 1

        repeated = sorted(
            [{"class": c, "count": n} for c, n in class_count.items() if 4 <= n <= 100],
            key=lambda x: -x["count"],
        )[:30]

        product_keywords = ["product", "item", "card", "tile", "grid"]
        likely_product = [r for r in repeated if any(k in r["class"].lower() for k in product_keywords)]

        sample_html = ""
        if likely_product:
            el = soup.select_one("." + likely_product[0]["class"])
            if el:
                sample_html = str(el)[:3000]

        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2"])[:5]]
        imgs = [{"src": img.get("src", ""), "alt": img.get("alt", "")} for img in soup.find_all("img")[:5]]

        # Full JSON-LD parsing — extract ItemList products
        json_ld_products = []
        json_ld_raw = []
        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            json_ld_raw.append(script.string[:3000])
            try:
                data = json_lib.loads(script.string)
                if data.get("@type") == "ItemList":
                    for entry in data.get("itemListElement", [])[:5]:
                        item = entry.get("item", entry)
                        offers = item.get("offers", {})
                        image = item.get("image", "")
                        if isinstance(image, list):
                            image = image[0] if image else ""
                        json_ld_products.append({
                            "name": item.get("name", ""),
                            "image": image[:100] if image else "",
                            "price": offers.get("price"),
                            "currency": offers.get("priceCurrency", ""),
                            "url": offers.get("url") or item.get("url", ""),
                        })
            except Exception:
                pass

        # Sample product links
        product_links = [
            a.get("href", "")
            for a in soup.find_all("a", href=True)
            if "product" in a.get("href", "").lower()
        ][:5]

        return {
            "title": soup.title.string if soup.title else "",
            "url": url,
            "headings": headings,
            "repeatedClasses": repeated[:20],
            "likelyProductClasses": likely_product,
            "sampleHtml": sample_html,
            "sampleImages": imgs,
            "jsonLdSnippets": json_ld_raw,
            "jsonLdProducts": json_ld_products,
            "sampleProductLinks": product_links,
        }
    except Exception as e:
        return {"error": str(e), "url": url}
