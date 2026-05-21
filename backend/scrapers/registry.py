"""
Central registry of scrapeable sections.
Only Zara and H&M are active — others can be re-added with correct URLs later.
"""

REGISTRY: dict[str, list[dict]] = {
    "Zara": [
        {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.zara.com/es/es/hombre-nuevo-l711.html"},
        {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.zara.com/es/es/mujer-nuevo-l1180.html"},
        {"key": "trending_women",     "label": "Trends · Mujer", "url": "https://www.zara.com/es/es/woman-events-l17929.html"},
    ],
    "H&M": [
        {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www2.hm.com/es_es/mujer/novedades/ver-todo.html"},
        {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www2.hm.com/es_es/hombre/novedades/ver-todo.html"},
    ],
    "& Other Stories": [
        {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.stories.com/es_es/women/new-arrivals.html"},
        {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.stories.com/es_es/men/new-arrivals.html"},
    ],
    "Pull&Bear": [
        {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.pullandbear.com/es/hombre/novedades-n6280"},
        {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.pullandbear.com/es/mujer/novedades-n1009"},
    ],
    "ASOS": [
        {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.asos.com/es/mujer/novedades/cat/?cid=2623"},
        {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.asos.com/es/hombre/novedades/cat/?cid=27108"},
    ],
    "The North Face": [
        {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.thenorthface.com/es-es/c/hombre/novedades-and-tendencias/novedades-226102"},
        {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.thenorthface.com/es-es/c/mujer/novedades-and-tendencias/novedades-226102"},
    ],
    "El Corte Inglés": [
        {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.elcorteingles.es/lo-mas-nuevo/moda-mujer/"},
        {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.elcorteingles.es/lo-mas-nuevo/moda-hombre/"},
    ],
    "The Sting": [
        {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.thesting.com/nl-nl/dames/new-in", "category_id": "dames-new-in"},
        {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.thesting.com/nl-nl/heren/new-in", "category_id": "heren-new-in"},
    ],
}


def get_sections_for_store(store_name: str) -> list[dict]:
    return REGISTRY.get(store_name, [])


def get_all_stores() -> list[str]:
    return list(REGISTRY.keys())
