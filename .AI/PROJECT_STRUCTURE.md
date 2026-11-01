# Project Structure

```
Access-Platform/
├── backend/                          # FastAPI + PostgreSQL backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app entry point, CORS, lifespan
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
│   ├── alembic.ini                  # Alembic migration configuration
│   ├── requirements.txt             # Python dependencies (FastAPI, SQLAlchemy, asyncpg, etc.)
│   ├── .env.example                 # Sample environment variables
│   └── .dockerignore                # Python / backend docker ignore rules
│
├── Dockerfile                        # Multi-stage production build for FastAPI backend
├── docker-compose.yml                # PostgreSQL 16 + FastAPI + pgAdmin multi-container setup
│
├── app/                              # Next.js app directory (Frontend)
│   ├── layout.tsx                    # Root layout with metadata
│   ├── page.tsx                      # Entry point → renders AccessGuard workspace
│   ├── workspace.tsx                 # Dashboard and all workflow UI interfaces
│   ├── globals.css                   # Responsive design system (Tailwind)
│   ├── chatgpt-auth.ts              # ChatGPT authentication helpers
│   └── api/
│       └── workspace/
│           └── route.ts             # Edge API route (Cloudflare Worker environment)
│
├── lib/                              # Frontend / Edge core application logic
│   ├── domain.ts                    # TypeScript pure domain: risk assessment, decisions
│   ├── service.ts                   # TypeScript use cases
│   ├── repository.ts               # D1 SQL repository
│   ├── seed.ts                      # D1 seed generator
│   ├── connectors.ts               # Connector bindings for request context
│   ├── connector-contract.mts      # Connector contract/protocol definition
│   ├── connector-context.ts        # Request-scoped connector binding context
│   ├── connector-errors.mts        # Connector error types
│   ├── connector-preview.d.ts      # Connector preview type declarations
│   └── utils.ts                     # Utility functions (cn, className merging)
│
├── db/                               # SQLite / Drizzle layer (Edge dev)
│   ├── schema.ts                    # Drizzle ORM schema — all 12 tables
│   └── index.ts                     # Database exports
│
├── drizzle/                          # Versioned SQL migrations (SQLite/D1)
│   ├── 0000_handy_zuras.sql
│   ├── 0001_productive_dreadnoughts.sql
│   ├── 0002_light_killmonger.sql
│   ├── 0003_marvelous_magdalene.sql
│   └── meta/                        # Migration snapshots and journal
│
├── components/                       # UI components
│   ├── connector-error.tsx          # Connector error display component
│   └── ui/                          # 50+ shadcn/ui primitives
│       ├── accordion.tsx, alert.tsx, button.tsx, card.tsx, chart.tsx,
│       ├── dialog.tsx, dropdown-menu.tsx, form.tsx, input.tsx, select.tsx,
│       ├── sidebar.tsx, table.tsx, tabs.tsx, tooltip.tsx, ...
│
├── hooks/                            # Custom React hooks
│   └── use-mobile.ts               # Mobile breakpoint detection
│
├── tests/                            # TypeScript tests (35 automated tests)
│   ├── domain.test.ts               # Pure domain logic tests
│   ├── workflows.test.ts           # Full API/service workflow integration tests
│   ├── auth.ts                      # Test auth utilities
│   ├── database.ts                  # In-memory SQLite test adapter
│   ├── env.ts                       # Test environment setup
│   └── register.mjs                 # Test runner registration
│
├── worker/                           # Cloudflare Worker
│   └── index.ts                     # Worker entry point
│
├── scripts/                          # Build, CI, and dev tooling
│   ├── run-framework.mjs           # Framework runner (dev/build)
│   ├── migrate-local.mjs           # Local D1 migration runner
│   ├── execution-profile.mjs       # Execution environment detection
│   ├── sites-env.mjs               # Sites environment configuration
│   └── vite/                        # Custom Vite plugins
│
├── sample-data/                      # Importable demo data
│   ├── hr-identities.csv           # HR identity records
│   └── access-assignments.csv      # Permission/entitlement assignments
│
├── docs/                             # Documentation
│   ├── ARCHITECTURE.md              # Architecture, decision flow, requirement traceability
│   └── DEMO_SI.md                   # Sinhala language demonstration guide
│
├── .AI/                              # AI Assistant Knowledge Base & Context
│   ├── README.md                    # System overview and quick start
│   ├── PROJECT_STRUCTURE.md         # This annotated file tree
│   ├── DATABASE.md                  # PostgreSQL 16 schema, tables, indexes, Alembic
│   ├── API.md                       # FastAPI / API endpoints, schemas, actions
│   ├── ARCHITECTURE.md              # Multi-tier architecture, state machines, Docker
│   ├── FEATURES.md                  # 7 core features, risk rules, policies
│   ├── TESTING.md                   # Testing strategy for Python and TypeScript
│   └── PERSONAS.md                  # 4 demo personas and role matrix
│
├── package.json                      # Node project manifest (accessguard v1.0.0)
├── vite.config.ts                    # Vite + Vinext + Cloudflare plugin config
├── drizzle.config.ts                # Drizzle-Kit config (SQLite dialect)
├── tsconfig.json                    # TypeScript configuration
└── eslint.config.mjs                # ESLint configuration
```

## Key File Roles

| Path                          | Technology          | Responsibility                                           |
| ----------------------------- | ------------------- | -------------------------------------------------------- |
| `backend/app/main.py`         | FastAPI             | Backend app lifecycle, CORS, router mounting, health     |
| `backend/app/models.py`       | SQLAlchemy (async)  | 12 PostgreSQL models with UUID, JSONB, ARRAY, and indexes|
| `backend/app/routers/workspace.py` | FastAPI        | Workspace endpoints: snapshot, CSV export, actions       |
| `backend/app/domain.py`       | Python              | Pure risk rules (LEAVER, INACTIVE, etc.), authorization  |
| `backend/app/service.py`      | Python              | Async business workflow orchestrator                     |
| `backend/app/seed.py`         | Python              | Deterministic synthetic demo data generator               |
| `Dockerfile`                  | Docker              | Multi-stage minimal production image for FastAPI         |
| `docker-compose.yml`          | Docker Compose      | PostgreSQL 16, FastAPI backend, pgAdmin services         |
| `app/workspace.tsx`           | React 19 / TS       | Frontend interface: dashboard, reviews, remediations     |
