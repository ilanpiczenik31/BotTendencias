"""
Central registry of all scrapeable sections per store.
Each entry defines a label shown in the UI and the URL to scrape.
"""

REGISTRY: dict[str, list[dict]] = {
    "Zara": [
        {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.zara.com/es/es/hombre-nuevo-l711.html"},
        {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.zara.com/es/es/mujer-nuevo-l1180.html"},
        {"key": "trending_women",     "label": "Trends · Mujer", "url": "https://www.zara.com/es/es/woman-events-l17929.html"},
    ],
    "Bershka": [
        {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.bershka.com/es/hombre/novedades-n3745.html"},
        {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.bershka.com/es/mujer/novedades-n3283.html"},
    ],
    "H&M": [
        {"key": "new_arrivals_women",  "label": "Nuevo · Mujer",             "url": "https://www2.hm.com/es_es/mujer/novedades/ver-todo.html"},
        {"key": "new_arrivals_men",    "label": "Nuevo · Hombre",            "url": "https://www2.hm.com/es_es/hombre/novedades/ver-todo.html"},
        {"key": "best_sellers_women",  "label": "Más vendidos · Mujer",      "url": "https://www2.hm.com/es_es/mujer/mejores-ventas/ver-todo.html"},
        {"key": "best_sellers_men",    "label": "Más vendidos · Hombre",     "url": "https://www2.hm.com/es_es/hombre/mejores-ventas/ver-todo.html"},
    ],
    "Springfield": [
        {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.springfield.com/es/mujer/"},
        {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.springfield.com/es/hombre/"},
    ],
    "The Sting": [
        {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.thesting.com/nl-nl/dames"},
        {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.thesting.com/nl-nl/heren"},
    ],
    "J.Crew": [
        {"key": "new_arrivals_women",  "label": "Nuevo · Mujer",         "url": "https://www.jcrew.com/plp/womens/features/new-arrivals"},
        {"key": "new_arrivals_men",    "label": "Nuevo · Hombre",        "url": "https://www.jcrew.com/plp/mens/features/new-arrivals"},
        {"key": "best_sellers_women",  "label": "Más vendidos · Mujer",  "url": "https://www.jcrew.com/plp/womens/features/best-sellers"},
        {"key": "best_sellers_men",    "label": "Más vendidos · Hombre", "url": "https://www.jcrew.com/plp/mens/features/best-sellers"},
    ],
    "The North Face": [
        {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.thenorthface.com/en-gb/womens"},
        {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.thenorthface.com/en-gb/mens"},
    ],
    "El Corte Inglés": [
        {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.elcorteingles.es/moda-mujer/"},
        {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.elcorteingles.es/moda-hombre/"},
    ],
}


def get_sections_for_store(store_name: str) -> list[dict]:
    return REGISTRY.get(store_name, [])


def get_all_stores() -> list[str]:
    return list(REGISTRY.keys())
