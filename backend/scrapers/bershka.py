from .base import BaseScraper, ScrapedProduct
from playwright.async_api import BrowserContext
import logging

logger = logging.getLogger(__name__)


class BershkaScraper(BaseScraper):
    store_name = "Bershka"
    store_url = "https://www.bershka.com/es/"

    async def _scrape(self, context: BrowserContext) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        sections = [
            ("https://www.bershka.com/es/mujer/nuevo-l1558051.html", "new_arrivals"),
            ("https://www.bershka.com/es/hombre/nuevo-l1558080.html", "new_arrivals"),
        ]

        for url, section in sections:
            page = await self._get_page(context)
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)

                try:
                    await page.click('[id="onetrust-accept-btn-handler"]', timeout=3000)
                    await page.wait_for_timeout(1000)
                except Exception:
                    pass

                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await page.wait_for_timeout(1500)

                items = await page.query_selector_all("li.grid-item")
                for item in items[:30]:
                    try:
                        name_el = await item.query_selector(".grid-card-element__title")
                        name = (await name_el.inner_text()).strip() if name_el else None

                        price_el = await item.query_selector(".price-item--regular")
                        if not price_el:
                            price_el = await item.query_selector(".price")
                        price_raw = (await price_el.inner_text()).strip() if price_el else None

                        img_el = await item.query_selector("img.grid-card-element__image")
                        image_url = await img_el.get_attribute("src") if img_el else None

                        link_el = await item.query_selector("a.grid-card-element")
                        product_url = await link_el.get_attribute("href") if link_el else None
                        if product_url and not product_url.startswith("http"):
                            product_url = "https://www.bershka.com" + product_url

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
                        logger.debug(f"Bershka item parse error: {e}")
            except Exception as e:
                logger.error(f"Bershka section {url} error: {e}")
            finally:
                await page.close()

        return products
