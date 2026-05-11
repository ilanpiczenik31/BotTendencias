from .base import BaseScraper, ScrapedProduct
from playwright.async_api import BrowserContext
import logging

logger = logging.getLogger(__name__)


class ElCorteInglesScraper(BaseScraper):
    store_name = "El Corte Inglés"
    store_url = "https://www.elcorteingles.es/moda/"

    async def _scrape(self, context: BrowserContext) -> list[ScrapedProduct]:
        products: list[ScrapedProduct] = []

        sections = [
            ("https://www.elcorteingles.es/moda/mujer/novedades/", "new_arrivals"),
            ("https://www.elcorteingles.es/moda/hombre/novedades/", "new_arrivals"),
            ("https://www.elcorteingles.es/moda/mujer/tendencias/", "trending"),
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

                items = await page.query_selector_all(".c-product-card, .product-card, [data-product]")
                for item in items[:30]:
                    try:
                        name_el = await item.query_selector(".c-product-card__description-title, .product-title")
                        name = (await name_el.inner_text()).strip() if name_el else None

                        price_el = await item.query_selector(".c-product-card__price, .price")
                        price_raw = (await price_el.inner_text()).strip() if price_el else None

                        img_el = await item.query_selector("img")
                        image_url = await img_el.get_attribute("src") if img_el else None
                        if not image_url:
                            image_url = await img_el.get_attribute("data-src") if img_el else None

                        link_el = await item.query_selector("a")
                        product_url = await link_el.get_attribute("href") if link_el else None
                        if product_url and not product_url.startswith("http"):
                            product_url = "https://www.elcorteingles.es" + product_url

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
                        logger.debug(f"El Corte Inglés item parse error: {e}")
            except Exception as e:
                logger.error(f"El Corte Inglés section {url} error: {e}")
            finally:
                await page.close()

        return products
