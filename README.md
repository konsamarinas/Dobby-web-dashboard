# DOBBY Intelligence

Standalone Flask dashboard for the existing [DOBBY API](https://dobby-api-system.onrender.com/docs). It does not contain recommendation or forecasting logic: all model output is requested from the API over HTTP.

## Features

- Overview with live health, recommendation metrics, forecast metrics, model versions, and measured business impact.
- Metrics and health pages with transparent evaluation details and manual refresh.
- Recommendations playground using the verified `POST /recommendations` schema.
- Forecasting page using the verified `GET /forecast` query parameters.
- Responsive Bootstrap 5 UI, Chart.js visualizations, and loading/error/empty states.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Open http://localhost:5050. The application loads `.env` directly when started with either `python run.py` or the Flask CLI. Environment variables:

Run the two applications locally in separate terminals:

```bash
# Terminal 1: DOBBY FastAPI (from the DOBBY API repository)
cd /path/to/DOBBY/src
source venv/bin/activate
uvicorn src.main:app --reload --port 8000

# Terminal 2: dashboard
cd /path/to/dobby-web-platform
source venv/bin/activate
python run.py
```

The dashboard then uses `http://127.0.0.1:8000` from `.env` and listens on `http://127.0.0.1:5050`. A shell environment variable takes precedence over `.env`, so the deployed API can be selected explicitly with `DOBBY_API_URL=https://dobby-api-system.onrender.com python run.py`.

| Variable | Default | Description |
| --- | --- | --- |
| `DOBBY_API_URL` | `https://dobby-api-system.onrender.com` | Existing API base URL |
| `DOBBY_API_CONNECT_TIMEOUT` | `5` | Connection timeout in seconds |
| `DOBBY_API_READ_TIMEOUT` | `45` | Response read timeout in seconds, allowing for Render cold starts |
| `DOBBY_CACHE_TTL` | `30` | Cache duration for health and metrics |
| `DOBBY_API_RETRIES` | `1` | Maximum additional retry for transient GET failures |
| `LOG_LEVEL` | `INFO` | Python logging level |

## Architecture

`app/services/dobby_client.py` is the only module that communicates with DOBBY. Flask routes expose server-rendered pages and JSON proxy endpoints consumed by vanilla JavaScript.

## Render deployment

Create a separate Render Web Service:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn run:app`
- Set `DOBBY_API_URL` to the DOBBY API base URL.

No API credentials are placed in browser JavaScript.

## API limitations

The inspected API has no catalog/list endpoint and no business-level forecast mode. The forecast contract supports `level=product` with product IDs such as `shop_commercial_prod_freddo_espresso`, and `level=category` with category IDs such as `shop_commercial_cat_coffee`. The playground accepts operator-entered IDs and rejects category/product level mismatches before making a request. Forecast responses contain forecast points, bounds, selected model, and evaluation metrics, but no historical observations, so the UI does not fabricate historical data.