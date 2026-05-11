from .base import BaseScraper, ScrapedProduct
from playwright.async_api import BrowserContext
import asyncio
import logging

logger = logging.getLogger(__name__)


class ZaraScraper(BaseScraper):
    store_name = "Zara"
    store_url = "https://www.zara.com/es/"

    async def _scrape(self, context: BrowserContext) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        # New arrivals + trending sections
        sections = [
            ("https://www.zara.com/es/es/mujer-nuevo-l1180.html", "new_arrivals"),
            ("https://www.zara.com/es/es/hombre-nuevo-l837.html", "new_arrivals"),
        ]

        for url, section in sections:
            page = await self._get_page(context)
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)

                # Accept cookies if present
                try:
                    await page.click('[id="onetrust-accept-btn-handler"]', timeout=3000)
                    await page.wait_for_timeout(1000)
                except Exception:
                    pass

                # Scroll to load more products
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await page.wait_for_timeout(1500)

                items = await page.query_selector_all("li.product-grid-product")
                for item in items[:30]:
                    try:
                        name_el = await item.query_selector(".product-grid-product-info__name")
                        name = (await name_el.inner_text()).strip() if name_el else None

                        price_el = await item.query_selector(".money-amount__main")
                        price_raw = (await price_el.inner_text()).strip() if price_el else None

                        img_el = await item.query_selector("img.media-image__image")
                        image_url = await img_el.get_attribute("src") if img_el else None

                        link_el = await item.query_selector("a.product-grid-product__figure-wrapper")
                        product_url = await link_el.get_attribute("href") if link_el else None
                        if product_url and not product_url.startswith("http"):
                            product_url = "https://www.zara.com" + product_url

                        if name:
                            products.append(ScrapedProduct(
                                name=name,
                                section=section,
                                price=self._parse_price(price_raw),
                                image_url=image_url,
                                product_url=product_url,
                                category="ropa",
                            ))
                    except Exception as e:
                        logger.debug(f"Zara item parse error: {e}")
            except Exception as e:
                logger.error(f"Zara section {url} error: {e}")
            finally:
                await page.close()

        return products
