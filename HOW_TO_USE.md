# VISION-SOP — How to access everything

One-page guide. Copy-paste commands. Nothing extra.

## 1. First-time setup (30s)

```bash
cd vision-sop
cp .env.example .env          # stub LLM, SQLite-friendly defaults
docker compose up --build     # api + web + postgres + redis
```

That's it. Wait ~2 min for the YOLO weights to cache on first boot.

## 2. URLs

| Thing                   | URL                                       |
| ----------------------- | ----------------------------------------- |
| Web dashboard           | http://localhost:5173                     |
| API + Swagger docs      | http://localhost:8000/docs                |
| WebSocket live feed     | ws://localhost:8000/api/monitor/ws/{id}   |
| Postgres                | localhost:5432  (user/pass: `vision`)     |
| Redis                   | localhost:6379                            |

Default login (seeded): `admin@vision-sop.local` / `changeme`

## 3. Typical flow

1. **Generate a demo video** (if you don't have CCTV footage handy):
   ```bash
   python scripts/generate_demo_video.py --output data/videos/demo.mp4
   ```
2. **Create an SOP from it** — open the dashboard → *SOPs* → *New from video* → pick `demo.mp4`. The pipeline extracts actions and the LLM writes the markdown SOP.
3. **Run a monitoring session** — *Sessions* → *New* → pick the SOP and a video. Open the session page for live Golden-Batch comparison, alerts, and ergonomic heatmap.
4. **Review deviations** — the *Alerts* tab shows PPE / skipped-step / cycle-time violations as they fire.

## 4. Dev without Docker

Backend:
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## 5. Tests

```bash
cd backend && pytest -q               # Python
cd frontend && npm test               # Vitest
```

## 6. Where things live

```
backend/app/vision/        YOLOv8 + MediaPipe + temporal localisation
backend/app/sop/           SOP generator (LLM) + Golden-Batch comparator
backend/app/analytics/     Ergonomics (RULA-lite) + Muda/waste detection
backend/app/alerts/        Real-time compliance rules (PPE, skip, cycle)
backend/app/api/routes/    FastAPI endpoints + WebSocket
frontend/src/pages/        Dashboard / SOPs / Sessions / Alerts / LiveMonitor
data/videos/               Drop reference videos here
data/heatmaps/             Generated ergonomic heatmaps
docker-compose.yml         All services
.env.example               All tunable env vars (copy to .env)
```

## 7. Switching LLMs

Edit `.env`:
```
LLM_PROVIDER=openai        # or anthropic / ollama / stub
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```
`stub` works offline — useful for demos and tests.

## 8. Privacy knobs

```
PRIVACY_FACE_BLUR=1        # Haar-cascade face blur before processing
PRIVACY_STORE_RAW_CLIPS=0  # keep only skeletal data, not video
PRIVACY_RETENTION_DAYS=30
```

## 9. Troubleshooting

- **YOLO download stalls** → pre-download: `python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"`
- **Port in use** → change `APP_PORT` in `.env`, restart compose.
- **WebSocket disconnects** → check Redis is up: `docker compose logs redis`.
- **Migrations fail** → `docker compose run --rm api alembic upgrade head`.
