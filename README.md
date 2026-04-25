# VISION-SOP

> **Leveraging Computer Vision to Automate and Refine Standard Operating Procedures in Manufacturing**
>
> Capstone Project — Mrudul Mamtani (22BCE3721)

[![CI](https://github.com/your-org/vision-sop/actions/workflows/ci.yml/badge.svg)](./.github/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11-blue)
![React](https://img.shields.io/badge/react-18-blue)
![License](https://img.shields.io/badge/license-MIT-green)

VISION-SOP turns existing factory CCTV into a living SOP system. It watches a "gold-standard" operator, breaks the work down into timestamped actions using YOLOv8 + MediaPipe, asks an LLM to author a clean SOP document, then keeps watching every shift to flag deviations, PPE violations, and ergonomic waste — no new hardware required.

---

## What it does

| Phase | Capability | How |
| --- | --- | --- |
| **1. Observation & Digitization** | Ingests RTSP / video file of the reference operator and emits a structured action log + draft SOP | YOLOv8 object/hand detection + MediaPipe pose → Temporal Action Localization → LLM SOP authoring |
| **2. Process Optimization** | Surfaces Muda (waste), reach heatmaps, layout recommendations, cycle-time variance | Pose aggregation across shifts, KDE heatmaps, cycle-time statistics |
| **3. Continuous Compliance** | Compares live footage against the gold-standard SOP and alerts supervisors in real time | Sliding-window action matcher + rule engine + WebSocket notifications |

Headline features from the spec deck:

- **Auto-SOP Generator** — produces a document with video snippets, step text, and target times.
- **"Golden Batch" Compare** — side-by-side play-back of a trainee vs. veteran operator.
- **Ergonomic Heatmaps** — movement density visualisation per station.
- **Privacy-first** — skeletal-only tracking with optional face blur; process-level, not identity-level.

---

## Architecture

```
┌────────────────┐     RTSP/MP4      ┌───────────────────────────┐
│  CCTV / NVR    │ ───────────────▶  │  Ingest Worker (Python)   │
└────────────────┘                   │   ├─ YOLOv8 actions       │
                                     │   ├─ MediaPipe pose       │
                                     │   ├─ Face blur            │
                                     │   └─ Temporal Localizer   │
                                     └────────────┬──────────────┘
                                                  │ frames + actions
                                                  ▼
┌───────────────────┐   REST/WS    ┌───────────────────────────┐
│  React Dashboard  │ ◀──────────▶ │  FastAPI (api + ws)       │
│  - SOP library    │              │   ├─ SOP generator (LLM)  │
│  - Live monitor   │              │   ├─ Compliance engine    │
│  - Heatmaps       │              │   ├─ Alert router         │
│  - Alerts         │              │   └─ Analytics            │
└───────────────────┘              └─────┬───────────┬─────────┘
                                         ▼           ▼
                                   PostgreSQL    Redis Streams
```

Read [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for detailed sequence diagrams and the data model.

---

## Quick start

### Prerequisites

- Docker 24+ and docker-compose v2
- An `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`) for SOP authoring — you can also run fully offline with `LLM_PROVIDER=stub`
- ~4 GB disk for model weights (downloaded on first run)

```bash
git clone https://github.com/your-org/vision-sop.git
cd vision-sop
cp .env.example .env
# edit .env and set OPENAI_API_KEY

docker compose up --build
```

That brings up:

| Service | URL | Purpose |
| --- | --- | --- |
| `api` | http://localhost:8000/docs | FastAPI + Swagger |
| `web` | http://localhost:5173 | React dashboard |
| `worker` | — | Video ingestion & analysis |
| `postgres` | localhost:5432 | Persistence |
| `redis` | localhost:6379 | Job queue + WS fan-out |

First-time setup:

```bash
# run migrations and seed demo SOP
docker compose exec api alembic upgrade head
docker compose exec api python -m app.scripts.seed_demo
```

Then open the dashboard, upload a reference video, and click **Generate SOP**.

### Running without Docker

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# frontend
cd ../frontend
npm install
npm run dev
```

---

## Repo layout

```
vision-sop/
├── backend/
│   ├── app/
│   │   ├── api/routes/         # REST + WebSocket routes
│   │   ├── vision/             # YOLOv8, MediaPipe, TAL, heatmap
│   │   ├── sop/                # SOP generator + golden-batch compare
│   │   ├── alerts/             # Compliance rules & alert router
│   │   ├── streaming/          # RTSP reader + frame buffer
│   │   ├── privacy/            # Face blur + anonymiser
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic models
│   │   ├── core/               # Config, security, logging
│   │   └── db/                 # Session, migrations
│   ├── tests/
│   └── alembic/
├── frontend/
│   └── src/
│       ├── pages/              # Dashboard, SOPLibrary, LiveMonitor, Alerts
│       ├── components/
│       └── lib/                # api client, ws hooks
├── docs/
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
├── scripts/                    # data tools, model downloader, seed
├── data/                       # runtime artefacts (gitignored)
├── docker-compose.yml
└── .github/workflows/ci.yml
```

---

## Tech stack

| Layer | Choice | Why |
| --- | --- | --- |
| **Vision** | Ultralytics YOLOv8 (pose + detect), MediaPipe Hands, OpenCV | Best-in-class lightweight pose & detection, runs on edge GPU |
| **Temporal** | Custom sliding-window TAL over action scores | Deterministic, auditable, easy to tune per line |
| **LLM** | Pluggable — OpenAI / Anthropic / local Ollama / stub | No vendor lock-in; `stub` works fully offline |
| **API** | FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic | Type-safe, fast, auto-Swagger |
| **Realtime** | FastAPI WebSocket + Redis pub/sub | Horizontal scale-out for alerts |
| **Frontend** | React 18 + Vite + TailwindCSS + Recharts | Fast, modern, easy to theme |
| **Infra** | Docker Compose → production Helm chart (see DEPLOYMENT) | One command up; K8s-ready |
| **Tests** | pytest + pytest-asyncio + httpx, Vitest + Testing Library | Covers vision, API, UI smoke |

Maps cleanly to the presentation tech table (Input → Vision → Logic → GenAI).

---

## Demo data

The repo ships with a `scripts/generate_demo_video.py` that creates a synthetic "pick-place-screw" video so you can exercise the full pipeline without a real CCTV feed. Run it inside the worker container:

```bash
docker compose exec worker python scripts/generate_demo_video.py --out data/videos/demo.mp4
```

Then in the UI: **Upload → data/videos/demo.mp4 → Generate SOP**.

---

## Privacy & ethics

- Face blur is **on by default** (`PRIVACY_FACE_BLUR=1`).
- Only skeletal key-points are stored for analytics — no raw biometrics.
- Worker IDs are pseudonymous (`op-7f3a…`) unless an admin opts in per-SOP.
- A full audit log of who viewed which clip lives in `audit_log`.

Read `docs/PRIVACY.md` for the full policy and the risks-and-mitigations matrix from the project spec.

---

## Roadmap (from the capstone)

| Month | Milestone |
| --- | --- |
| **1** | Camera integration (2–4 RTSP feeds), train on 5 core tasks |
| **2** | Calibration & detection refinement with floor managers |
| **3** | Floor-wide SOP generation + safety alerts |
| **4** | ROI measurement: cycle-time, defects, training cost |

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the detailed plan and KPIs.

---

## License

MIT © 2026 Mrudul Mamtani
