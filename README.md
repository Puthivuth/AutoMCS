# AutoMCS

AI-assisted decimal table extraction, labeling, verification, evaluation and dataset export.
Frontend: Next.js + TypeScript + Tailwind. Backend: Django REST Framework + PostgreSQL + Celery/Redis.

## Run (Docker)
1. `cp .env.example .env` and fill in the secrets and paths. Create the three host folders (data, models, pgdata).
2. First time only, generate migrations and commit them:
   `docker compose run --rm backend python manage.py makemigrations core`
3. `docker compose up -d --build`
4. Create the first user (public registration is disabled by design):
   `docker compose exec backend python manage.py createsuperuser`
5. Open http://localhost:3000 and sign in. Django admin is at http://localhost:8000/admin/.

## Run without Docker (development)
Backend: `cd backend && pip install -r requirements.txt && DJANGO_DEBUG=1 CELERY_EAGER=1 python manage.py migrate && DJANGO_DEBUG=1 CELERY_EAGER=1 python manage.py runserver`
Frontend: `cd frontend && npm install && npm run dev`  (proxies /api to http://localhost:8000)

## Required decisions before real use
- `LOCAL_MODEL_REVISION`: a pinned commit hash. Auto-download refuses to run without it.
- `GEMINI_MODEL`: choose a vision-capable model; the API key stays on the server.
- Rounding rule (`ROUND_HALF_UP` is the default in settings.py) must match your research protocol.
- Supervisor / institution / contact email: set in Settings (admin). Nothing is invented.

## Design notes
- Predictions are immutable (`Prediction`, `PredictionCell`). Human work lives in `Cell`. Re-running extraction never overwrites approved cells.
- Every lookup goes through `permissions.scoped()` so users only reach projects they own or belong to.
- Exports include fully approved documents only (partial export is opt-in and lists the unapproved cells).
- Local DeepSeek is text-only: Tesseract OCR + a layout step feed it text; it never sees pixels.
- Backups: dump PostgreSQL and copy `/data` and `/models` together; test a restore before relying on it.
- Put nginx/Caddy with HTTPS in front in production (set `DJANGO_SECURE=1`) and raise its upload size limit.
- Training is intentionally unavailable: the endpoint returns 501 and the page says "Coming later".
- PDF pages are rendered server-side (pypdfium2) into images for the viewer; swap in PDF.js later if you want native PDF rendering.

## Tests
`cd backend && pip install pytest pytest-django && pytest` (decimal tests need no database).
