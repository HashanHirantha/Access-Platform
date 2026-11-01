# Project Structure

```
Access-Platform/
├── backend/                          # FastAPI + PostgreSQL Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app entry point, CORS, lifespan, /health
│   │   ├── config.py                # Pydantic BaseSettings (DB URL, secrets, origins)
│   │   ├── database.py              # SQLAlchemy async engine, sessionmaker, Base
│   │   ├── models.py                # 12 SQLAlchemy models (UUID, JSONB, ARRAY, Indexes)
│   │   ├── schemas.py               # Pydantic v2 schemas for snapshots, requests, responses
│   │   ├── domain.py                # Pure business logic: risk scoring, authorization
│   │   ├── repository.py            # Async DB repository, queries, tenant scoping
│   │   ├── seed.py                  # Deterministic demo workspace seed data generator
│   │   ├── service.py               # Use cases: scan, decide, execute, import, policy
│   │   └── routers/
│   │       ├── __init__.py
│   │       └── workspace.py         # /api/workspace GET snapshot/exports & POST actions
│   ├── alembic/
│   │   ├── env.py                   # Async Alembic migration environment
│   │   ├── script.py.mako           # Migration script template
│   │   └── versions/
│   │       └── 0001_initial_schema.py # Complete PostgreSQL 16 schema migration
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_domain.py           # Unit tests: 6 risk policies, self-review, dual approval
│   │   └── test_api.py              # API tests: /health, /openapi.json, persona headers
│   ├── Dockerfile                   # Multi-stage production build for FastAPI backend
│   ├── alembic.ini                  # Alembic migration configuration
│   ├── requirements.txt             # Python dependencies (FastAPI, SQLAlchemy, asyncpg, etc.)
│   ├── .env.example                 # Sample backend environment variables
│   └── .dockerignore                # Backend docker ignore rules
│
├── frontend/                         # React 19 + Next.js / Vite Frontend
│   ├── app/
│   │   ├── layout.tsx               # Root layout with metadata
│   │   ├── page.tsx                 # Main entry point mounting AccessGuard workspace
│   │   ├── workspace.tsx            # Complete dashboard, review, remediation & audit UI
│   │   ├── globals.css              # Tailwind CSS 4 theme & responsive tokens
│   │   └── api/
│   │       └── workspace/
│   │           └── route.ts         # Edge route handler / proxy
│   ├── components/
│   │   ├── connector-error.tsx     # Error boundary / status fallback
│   │   └── ui/                     # 50+ shadcn/ui components (accordion, button, card,
│   │                               # dialog, dropdown, form, table, tabs, tooltip, ...)
│   ├── hooks/
│   │   └── use-mobile.ts           # Mobile breakpoint hook
│   ├── lib/
│   │   ├── utils.ts                # cn() class utility
│   │   ├── domain.ts               # Frontend types, severity levels, date helpers
│   │   └── service.ts              # Client-side API fetch utilities
│   ├── public/
│   │   └── favicon.svg             # Application favicon
│   ├── Dockerfile                   # Node 24 multi-stage frontend Dockerfile
│   ├── package.json                 # Frontend dependencies (React 19, Lucide, Tailwind, ...)
│   ├── tsconfig.json                # TypeScript configuration
│   ├── vite.config.ts               # Vite / Vinext bundler configuration
│   ├── postcss.config.mjs          # Tailwind CSS PostCSS configuration
│   ├── components.json              # shadcn/ui registry config
│   ├── eslint.config.mjs           # ESLint configuration
│   ├── .dockerignore                # Frontend docker ignore rules
│   └── .env.example                 # Frontend environment variable template
│
├── docker-compose.yml                # Multi-container orchestration: db + backend + frontend + pgadmin
├── Dockerfile                        # Root Dockerfile (FastAPI backend build)
│
├── sample-data/                      # Demo CSV Import Data
│   ├── hr-identities.csv            # HR identity records for import testing
│   └── access-assignments.csv       # Permission/entitlement assignments
│
├── docs/                             # Original problem statement & walk-through
│   ├── ARCHITECTURE.md              # Original architecture notes
│   └── DEMO_SI.md                   # Sinhala language demonstration guide
│
└── .AI/                              # Comprehensive AI Knowledge Base
    ├── README.md                    # System overview and quick start guide
    ├── FRONTEND.md                  # Frontend architecture, components, views & commands
    ├── BACKEND.md                   # Backend architecture, FastAPI routes, ORM & services
    ├── DATABASE.md                  # PostgreSQL 16 schema, 12 tables, indexes & Alembic
    ├── API.md                       # API endpoints, request schemas & Swagger UI docs
    ├── ARCHITECTURE.md              # Multi-tier architecture & state machines
    ├── PROJECT_STRUCTURE.md         # This annotated file tree
    ├── FEATURES.md                  # 7 core features & 6 risk policy rules
    ├── TESTING.md                   # Testing strategy for Python and TypeScript
    └── PERSONAS.md                  # 4 demo personas & authorization matrix
```

## Key Architectural Separation

| Aspect              | Frontend (`frontend/`)                  | Backend (`backend/`)                     |
| ------------------- | --------------------------------------- | ---------------------------------------- |
| **Language**        | TypeScript 5.9                          | Python 3.12                              |
| **Core Framework**  | React 19 + Next.js 16 (Vinext/Vite)     | FastAPI 0.115                            |
| **Package Manager** | `pnpm`                                  | `pip`                                    |
| **Styling / ORM**   | Tailwind CSS 4 + shadcn/ui              | SQLAlchemy 2.0 (async) + asyncpg         |
| **Port**            | `5173`                                  | `8000`                                   |
| **Docker**          | `frontend/Dockerfile`                   | `backend/Dockerfile`                     |
| **Documentation**   | [`.AI/FRONTEND.md`](./FRONTEND.md)      | [`.AI/BACKEND.md`](./BACKEND.md)         |
