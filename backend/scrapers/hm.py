from .base import BaseScraper, ScrapedProduct
from playwright.async_api import BrowserContext
import logging

logger = logging.getLogger(__name__)


class HMScraper(BaseScraper):
    store_name = "H&M"
    store_url = "https://www2.hm.com/es_es/"

    async def _scrape(self, context: BrowserContext) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        sections = [
            ("https://www2.hm.com/es_es/mujer/novedades/ver-todo.html", "new_arrivals"),
            ("https://www2.hm.com/es_es/hombre/novedades/ver-todo.html", "new_arrivals"),
            ("https://www2.hm.com/es_es/mujer/tendencias.html", "trending"),
        ]

        for url, section in sections:
            page = await self._get_page(context)
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)

                try:
                    await page.click("#onetrust-accept-btn-handler", timeout=3000)
                    await page.wait_for_timeout(1000)
                except Exception:
                    pass

                for _ in range(4):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await page.wait_for_timeout(1500)

                items = await page.query_selector_all("li.product-item")
                for item in items[:30]:
                    try:
                        name_el = await item.query_selector("h2.item-heading a")
                        name = (await name_el.inner_text()).strip() if name_el else None

                        price_el = await item.query_selector("span.price.regular")
                        if not price_el:
                            price_el = await item.query_selector("span.price")
                        price_raw = (await price_el.inner_text()).strip() if price_el else None

                        img_el = await item.query_selector("img.item-image")
                        image_url = await img_el.get_attribute("src") if img_el else None
                        if image_url and image_url.startswith("//"):
                            image_url = "https:" + image_url

                        link_el = await item.query_selector("a.item-link")
                        product_url = await link_el.get_attribute("href") if link_el else None
                        if product_url and not product_url.startswith("http"):
                            product_url = "https://www2.hm.com" + product_url

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
                        logger.debug(f"H&M item parse error: {e}")
            except Exception as e:
                logger.error(f"H&M section {url} error: {e}")
            finally:
                await page.close()

        return products
