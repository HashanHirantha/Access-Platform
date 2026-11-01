# AccessGuard — AI Project Context

## Overview

AccessGuard is an **enterprise user access review and governance platform** built as an executable prototype for the Dialog Axiata TransitionX problem statement. It consolidates identity and entitlement evidence, prioritizes access reviews using configurable risk policies, records accountable decisions with independent approvals, and verifies remediation against an independent mock source.

> All data is synthetic. No real AWS, GitHub, Microsoft, or finance credentials are required.

## Tech Stack

| Layer              | Technology                                                     |
| ------------------ | -------------------------------------------------------------- |
| **Frontend**       | React 19, TypeScript 5.9, Tailwind CSS 4, Radix UI, shadcn/ui |
| **Web Framework**  | Next.js 16 (via Vinext on Vite 8)                              |
| **Python Backend** | **FastAPI 0.115**, Uvicorn, Python 3.12                        |
| **ORM & DB Layer** | **SQLAlchemy 2.0 (async)**, **asyncpg**, **Alembic**           |
| **Primary Database**| **PostgreSQL 16** (Alpine) in Docker                           |
| **Containerization**| **Docker** (multi-stage build), **Docker Compose**            |
| **Edge Backend**   | Vinext server routes running in Cloudflare Workers / D1 (dev)  |
| **Validation**     | Pydantic v2 (Python) & Zod (TypeScript)                        |
| **Testing**        | pytest / pytest-asyncio (Python) & Node test runner (TS)       |
| **Package Managers**| `pnpm 11` (Node.js) & `pip` (Python)                          |

## Quick Commands

### Docker (PostgreSQL 16 + FastAPI Backend)
```bash
# Start PostgreSQL, FastAPI backend, and pgAdmin
docker compose up -d

# Check FastAPI health
curl http://localhost:8000/health

# Open interactive Swagger docs
# Browser: http://localhost:8000/docs

# Open pgAdmin (admin@accessguard.local / admin)
# Browser: http://localhost:5050

# Run migrations inside container or locally
docker compose exec backend alembic upgrade head

# Stop containers
docker compose down
```

### Python Backend (Local Dev)
```bash
cd backend
python -m venv venv
source venv/bin/activate   # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
pytest
```

### Frontend (Next.js / Vite)
```bash
pnpm install --frozen-lockfile   # Install dependencies
pnpm dev                         # Dev server (http://localhost:5173)
pnpm build                       # Production build
pnpm typecheck                   # TypeScript check
pnpm test                        # Run frontend tests
```

## Documentation Index

| File                                        | Description                                    |
| ------------------------------------------- | ---------------------------------------------- |
| [DATABASE.md](./DATABASE.md)               | PostgreSQL schema, 12 tables, indexes, Alembic |
| [API.md](./API.md)                         | FastAPI endpoints, actions, and schemas        |
| [ARCHITECTURE.md](./ARCHITECTURE.md)       | Layer architecture, state machines, Docker    |
| [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) | Full annotated directory tree with backend/    |
| [FEATURES.md](./FEATURES.md)               | Core features and risk policies                 |
| [TESTING.md](./TESTING.md)                 | Test strategy for Python and TypeScript        |
| [PERSONAS.md](./PERSONAS.md)              | Demo personas and role-based access            |
