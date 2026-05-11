# TrendEuropa — Fashion Trend Tracker

Rastreador semanal de tendencias de moda europea para el mercado argentino.

## Arquitectura

```
├── backend/    → Python + FastAPI + Playwright (deploy: Railway)
└── frontend/   → Next.js 14 + Tailwind (deploy: Vercel)
```

**Base de datos**: PostgreSQL en Railway  
**Análisis**: Claude Haiku API (Anthropic)  
**Schedule automático**: Lunes 08:00 UTC

---

## Setup local

### Backend

```bash
cd backend
pip install -r requirements.txt
playwright install chromium

# Crear .env con:
# DATABASE_URL=postgresql://...
# ANTHROPIC_API_KEY=sk-ant-...
# ALLOWED_ORIGINS=http://localhost:3000

uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install

# Crear .env.local con:
# NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
```

---

## Deploy en Railway (backend)

1. Crear nuevo proyecto en Railway
2. Agregar servicio **PostgreSQL** → copiar `DATABASE_URL`
3. Agregar servicio **Python** desde este repo (carpeta `backend/`)
4. Agregar variables de entorno:
   - `DATABASE_URL` → string de conexión de Railway Postgres
   - `ANTHROPIC_API_KEY` → tu API key
   - `ALLOWED_ORIGINS` → URL de tu app en Vercel
5. El `railway.json` ya configura el start command con `playwright install chromium`

## Deploy en Vercel (frontend)

1. Importar repo en Vercel
2. **Root Directory**: `frontend`
3. Agregar variable de entorno:
   - `NEXT_PUBLIC_API_URL` → URL del backend en Railway
4. Deploy

---

## Tiendas soportadas

| Tienda | País | Secciones |
|---|---|---|
| Zara | España | Nuevos (mujer + hombre) |
| H&M | Suecia | Novedades + Tendencias |
| Bershka | España | Nuevos (mujer + hombre) |
| Springfield | España | Novedades |
| The Sting | Países Bajos | Nuevos |
| J.Crew | EE.UU. | Nuevos (mujer + hombre) |
| The North Face | EE.UU. | Nuevos + Best sellers |
| El Corte Inglés | España | Novedades + Tendencias |

---

## Agentes

| Agente | Archivo | Función |
|---|---|---|
| Scraper | `scrapers/*.py` | Extrae productos por tienda con Playwright |
| Analyzer | `agents/analyzer.py` | Analiza tendencias usando Claude Haiku |
| Reporter | `agents/orchestrator.py` | Genera reporte semanal global |
| Orchestrator | `agents/orchestrator.py` | Coordina el pipeline completo |

---

## API endpoints principales

```
POST /api/runs/trigger          → disparar corrida manual
GET  /api/runs                  → listar corridas
GET  /api/runs/{id}/products    → productos de una corrida
GET  /api/runs/{id}/analyses    → análisis por tienda
GET  /api/reports/latest        → último reporte
GET  /api/reports               → histórico de reportes
GET  /api/stats                 → stats del dashboard
```
