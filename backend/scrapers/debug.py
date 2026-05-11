from .base import fetch_page
from bs4 import BeautifulSoup


async def inspect_page(url: str) -> dict:
    """Fetch page via ScraperAPI and return structure info for selector debugging."""
    try:
        soup = await fetch_page(url, wait=5000)

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
        json_ld = [s.string[:500] for s in soup.find_all("script", type="application/ld+json") if s.string][:3]

        return {
            "title": soup.title.string if soup.title else "",
            "url": url,
            "headings": headings,
            "repeatedClasses": repeated[:20],
            "likelyProductClasses": likely_product,
            "sampleHtml": sample_html,
            "sampleImages": imgs,
            "jsonLdSnippets": json_ld,
        }
    except Exception as e:
        return {"error": str(e), "url": url}
