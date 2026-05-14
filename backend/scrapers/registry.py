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
    "COS": [
        {"key": "new_arrivals_women", "label": "Nuevo · Mujer",  "url": "https://www.cos.com/es_es/women/new-arrivals.html"},
        {"key": "new_arrivals_men",   "label": "Nuevo · Hombre", "url": "https://www.cos.com/es_es/men/new-arrivals.html"},
    ],
}


def get_sections_for_store(store_name: str) -> list[dict]:
    return REGISTRY.get(store_name, [])


def get_all_stores() -> list[str]:
    return list(REGISTRY.keys())
