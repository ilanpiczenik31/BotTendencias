import anthropic
import json
import logging
from dataclasses import asdict
from scrapers.base import ScrapedProduct

logger = logging.getLogger(__name__)

client = anthropic.Anthropic()


async def analyze_store_trends(store_name: str, products: list[ScrapedProduct]) -> dict:
    """Send product list to Claude and get structured trend analysis."""
    if not products:
        return _empty_analysis()

    product_list = "\n".join([
        f"- {p.name} | ${p.price} {p.currency} | sección: {p.section} | categoría: {p.category or 'N/A'}"
        for p in products[:60]
    ])

    prompt = f"""Sos un experto en moda europea y tendencias de indumentaria.
Analizás los productos de la tienda "{store_name}" para ayudar a un vendedor de ropa en Argentina a entender qué está de moda en Europa esta semana.

Productos scraped esta semana de {store_name}:
{product_list}

Analizá estos productos y respondé ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
  "summary": "resumen breve de 2-3 oraciones sobre lo que predomina en esta tienda esta semana",
  "colors": ["lista de colores predominantes que aparecen en los nombres"],
  "styles": ["estilos o tendencias de corte/diseño detectados"],
  "categories": ["tipos de prenda más frecuentes"],
  "price_range": {{
    "min": número_o_null,
    "max": número_o_null,
    "average": número_o_null,
    "currency": "EUR_o_USD"
  }},
  "keywords": ["palabras clave de tendencia que se repiten"],
  "trend_score": número del 1 al 10 indicando qué tan fuerte es la tendencia esta semana
}}

Solo respondé con el JSON, sin texto adicional."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        # Remove markdown code blocks if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Analyzer JSON parse error for {store_name}: {e}")
        return _empty_analysis()
    except Exception as e:
        logger.error(f"Analyzer Claude API error for {store_name}: {e}")
        return _empty_analysis()


async def generate_weekly_report(
    analyses: list[dict],
    previous_report: dict | None = None,
) -> dict:
    """Generate global weekly report comparing all stores."""
    stores_summary = "\n\n".join([
        f"**{a['store_name']}**\n{json.dumps(a['trends'], ensure_ascii=False, indent=2)}"
        for a in analyses
    ])

    prev_context = ""
    if previous_report:
        prev_context = f"\n\nReporte de la semana anterior para comparar:\n{json.dumps(previous_report.get('top_trends', {}), ensure_ascii=False)}"

    prompt = f"""Sos un experto en tendencias de moda europea. Generá un reporte semanal global basado en el análisis de múltiples tiendas europeas.

Análisis por tienda esta semana:
{stores_summary}
{prev_context}

Respondé ÚNICAMENTE con un JSON válido:
{{
  "summary": "resumen ejecutivo de 3-4 oraciones sobre las tendencias generales de esta semana en Europa",
  "top_trends": {{
    "colors": ["top 5 colores más tendencia esta semana en todas las tiendas"],
    "styles": ["top 5 estilos más repetidos"],
    "categories": ["top 5 prendas más presentes"],
    "keywords": ["top 10 palabras clave de tendencia"]
  }},
  "store_highlights": [
    {{"store": "nombre", "highlight": "qué tiene de especial esta tienda esta semana"}}
  ],
  "argentina_recommendation": "recomendación específica para un vendedor de ropa en Argentina: qué tendencias europeas tiene sentido importar/replicar y por qué",
  "vs_last_week": "descripción de qué cambió vs semana anterior (si hay datos) o null si es la primera corrida"
}}

Solo respondé con el JSON, sin texto adicional."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Weekly report generation error: {e}")
        return {
            "summary": "Error generando reporte",
            "top_trends": {},
            "store_highlights": [],
            "argentina_recommendation": "",
            "vs_last_week": None,
        }


def _empty_analysis() -> dict:
    return {
        "summary": "Sin datos suficientes para analizar",
        "colors": [],
        "styles": [],
        "categories": [],
        "price_range": {"min": None, "max": None, "average": None, "currency": "EUR"},
        "keywords": [],
        "trend_score": 0,
    }
