"""Debug scraper — call /api/debug/inspect?url=... to see what classes/structure a page has."""
from playwright.async_api import async_playwright


async def inspect_page(url: str) -> dict:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            ignore_https_errors=True,
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            # Scroll once
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await page.wait_for_timeout(2000)

            result = await page.evaluate("""() => {
                // Get all unique classes on the page (filtered to product-looking ones)
                const allElements = document.querySelectorAll('*');
                const classSet = new Set();
                allElements.forEach(el => {
                    el.classList.forEach(c => {
                        if (c.length > 2 && c.length < 60) classSet.add(c);
                    });
                });

                // Find likely product containers (elements repeated 4+ times with same class)
                const classCount = {};
                allElements.forEach(el => {
                    el.classList.forEach(c => {
                        classCount[c] = (classCount[c] || 0) + 1;
                    });
                });
                const repeatedClasses = Object.entries(classCount)
                    .filter(([c, n]) => n >= 4 && n <= 100)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 30)
                    .map(([c, n]) => ({class: c, count: n}));

                // Try to find product names (text that looks like product names)
                const productKeywords = ['product', 'item', 'card', 'tile', 'grid'];
                const likelyProductClasses = repeatedClasses.filter(({class: c}) =>
                    productKeywords.some(k => c.toLowerCase().includes(k))
                );

                // Get sample HTML of first likely product container
                let sampleHtml = '';
                if (likelyProductClasses.length > 0) {
                    const el = document.querySelector('.' + likelyProductClasses[0].class);
                    if (el) sampleHtml = el.outerHTML.substring(0, 2000);
                }

                // Get page title and h1/h2
                const headings = Array.from(document.querySelectorAll('h1,h2')).slice(0,5).map(h => h.innerText.trim());

                // Find images with product-like src
                const imgs = Array.from(document.querySelectorAll('img')).slice(0, 5).map(img => ({
                    src: img.src,
                    alt: img.alt,
                    classes: img.className
                }));

                // JSON-LD
                const jsonLd = Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
                    .map(s => s.textContent.substring(0, 500));

                return {
                    title: document.title,
                    url: window.location.href,
                    headings,
                    repeatedClasses: repeatedClasses.slice(0, 20),
                    likelyProductClasses,
                    sampleHtml,
                    sampleImages: imgs,
                    jsonLdSnippets: jsonLd.slice(0, 3),
                };
            }""")
            return result
        except Exception as e:
            return {"error": str(e), "url": url}
        finally:
            await browser.close()
