# AccessGuard — Backend Documentation

## Overview

The AccessGuard backend is a high-performance, asynchronous REST API built with **FastAPI 0.115**, **SQLAlchemy 2.0 (async)**, and **PostgreSQL 16**. It implements access governance logic, multi-rule risk engines, optimistic concurrency control (OCC), durable remediation leases, and compliance auditing.

All backend source files reside in the [`backend/`](file:///e:/Access-Platform/backend) directory.

---

## Tech Stack & Architecture

| Category             | Technology                      | Version     | Purpose                                            |
| -------------------- | ------------------------------- | ----------- | -------------------------------------------------- |
| **API Framework**    | FastAPI                         | 0.115.12    | Async Web Framework with automatic OpenAPI/Swagger |
| **ASGI Server**      | Uvicorn                         | 0.34.3      | High-speed ASGI server                             |
| **Database**         | PostgreSQL                      | 16 (Alpine) | ACID relational storage, UUID, JSONB, Arrays       |
| **ORM**              | SQLAlchemy (Asyncio)            | 2.0.41      | Async Object Relational Mapper                     |
| **Database Driver**  | asyncpg                         | 0.31.0      | Fastest async PostgreSQL driver for Python         |
| **Migrations**       | Alembic                         | 1.15.2      | Version-controlled database schema migrations      |
| **Validation**       | Pydantic v2                     | 2.11.3      | Fast data validation and serialization             |
| **Settings**         | pydantic-settings               | 2.9.1       | Type-safe environment variable parsing             |
| **Testing**          | pytest + pytest-asyncio         | 8.3.5       | Unit and integration testing                       |
| **Container**        | Docker & Docker Compose         | Multi-stage | Isolated production & development environments     |

---

## Directory Structure (`backend/`)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point, CORS, lifespan, /health
│   ├── config.py                    # Settings class (DATABASE_URL, secrets, origins)
│   ├── database.py                  # SQLAlchemy async engine, sessionmaker, init_db()
│   ├── models.py                    # 12 SQLAlchemy ORM models (UUID, JSONB, ARRAY)
│   ├── schemas.py                   # Pydantic v2 request/response models & snapshot
│   ├── domain.py                    # Pure domain logic: 6 risk policies, authorization
│   ├── service.py                   # Use case workflows: scan, decide, execute, import
│   ├── repository.py                # Tenant-scoped async database queries
│   ├── seed.py                      # Deterministic demo workspace seed generator
│   └── routers/
│       ├── __init__.py
│       └── workspace.py             # Route handlers: GET snapshot/export, POST actions
│
├── alembic/
│   ├── env.py                       # Async migration environment
│   ├── script.py.mako               # Migration template
│   └── versions/
│       └── 0001_initial_schema.py   # Initial migration for 12 PostgreSQL tables
│
├── tests/
│   ├── __init__.py
│   ├── test_domain.py               # Unit tests: 6 risk policies, self-review, 2nd approval
│   └── test_api.py                  # API tests: /health, /openapi.json, persona headers
│
├── Dockerfile                        # Multi-stage Python 3.12 production Dockerfile
├── .dockerignore                     # Docker ignore patterns
├── .env.example                     # Sample backend environment configuration
├── alembic.ini                      # Alembic CLI configuration
└── requirements.txt                 # Pinned Python package dependencies
```

---

## Database Schema (12 PostgreSQL Tables)

| Table            | Primary Key | Key Features / Types                                | Description                                |
| ---------------- | ----------- | --------------------------------------------------- | ------------------------------------------ |
| `workspaces`     | `UUID`      | Tenant isolation root; `name`, `created_at`         | Workspaces / multi-tenant boundary        |
| `identities`     | `UUID`      | `VARCHAR`, self-referencing `manager_id`, `status`  | Employee directory records (HR source)     |
| `sources`        | `UUID`      | `VARCHAR`, `last_sync` timestamp, `mode`            | Connected identity sources (AWS, GitHub)   |
| `accounts`       | `UUID`      | `external_id`, `kind` (user/service), `last_active` | System accounts linked to employees        |
| `entitlements`   | `UUID`      | `privileged` boolean, `allowed_departments` (ARRAY) | Permissions/roles in external systems      |
| `grants`         | `UUID`      | `version` (OCC), `state` (active/revoked), expires  | Assignment of entitlements to accounts     |
| `source_access`  | `UUID`      | `grant_id`, `state`, `version`, `updated_at`        | Independent mock source state for readback |
| `campaigns`      | `UUID`      | `name`, `started_at`, `due_at`                      | Access review campaign cycles              |
| `reviews`        | `UUID`      | `score`, `severity`, `reasons` (JSONB), `codes`     | Access review findings and decisions       |
| `remediations`   | `UUID`      | `status`, `attempts`, `lease_until`, `evidence`     | Durable remediation queue and worker lease |
| `policies`       | `UUID`      | `code`, `name`, `enabled`, `threshold`              | Configurable risk detection policy rules   |
| `audits`         | `UUID`      | `actor`, `principal`, `action`, `target`, `detail`  | Immutable append-only compliance log       |
| `imports`        | `UUID`      | `checksum` (SHA-256), `filename`, `row_count`       | Checksum-based import deduplication        |

---

## Pure Domain Engine (`app/domain.py`)

The risk assessment engine evaluates active grants against enabled policies with zero external I/O:

1. **LEAVER (Score 100, Critical)**: Active accounts belonging to employees marked as terminated.
2. **CONTRACT (Score 90, Critical)**: Active access retained past contractor contract end date.
3. **EXPIRED (Score 88, High)**: Temporary grants whose expiration timestamp has passed.
4. **INACTIVE (Score 56–85, High/Medium)**: Human accounts with no activity beyond the threshold (default 90 days). Skipped if employee is on approved leave.
5. **ROLE_MISMATCH (Score 82, High)**: Privileged entitlements held by an employee whose department is outside the allowed list.
6. **ORPHANED (Score 78, High)**: Human accounts with no linked employee identity record.

### Review Authorization Rules
- **Self-Approval Guard**: Employees are strictly prevented from approving their own access (`DomainError: 403`).
- **Independent Dual-Approval**: Reviews with `critical` severity (score ≥ 90) must receive first approval (`awaiting_second`) and second approval from two distinct reviewers.
- **Role Permissions**: Scans, imports, and policy changes require `admin`; remediations require `admin` or `security`.

---

## API Endpoints (`app/routers/workspace.py`)

### 1. Workspace Snapshot & Exports
- `GET /health` — Service health probe (`{"status":"healthy","database":"postgresql"}`)
- `GET /api/workspace` — Returns full `WorkspaceSnapshot` (all 12 entity collections)
- `GET /api/workspace?export=reviews` — Downloads review evidence CSV (formula-injection sanitized)
- `GET /api/workspace?export=audit` — Downloads complete compliance audit trail CSV

### 2. Workspace Actions (`POST /api/workspace`)
- `action: "scan"` — Initiates campaign scan, evaluates all grants, and generates findings.
- `action: "decide"` — Submits review decision (`keep`, `revoke`, `investigate`, `exception`). Revoke triggers remediation queueing.
- `action: "execute"` — Claims worker lease, updates mock source, verifies readback, and confirms grant revocation.
- `action: "policy"` — Enables/disables policy rule and updates threshold.
- `action: "import"` — Validates and imports HR or access assignment CSVs with SHA-256 deduplication.

---

## Development & Run Commands

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate       # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server (http://localhost:8000)
uvicorn app.main:app --reload --port 8000

# Run automated tests
pytest -v
```

## Running with Docker

```bash
# Run standalone backend container
docker build -t accessguard-backend ./backend
docker run -p 8000:8000 accessguard-backend

# Or run via root docker-compose (spins up Postgres + FastAPI)
docker compose up -d db backend
```

