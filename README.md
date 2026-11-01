# AccessGuard

An executable enterprise user access review and governance platform built for the Dialog Axiata TransitionX problem statement. Consolidate identity and entitlement evidence, prioritize access reviews, record accountable decisions, and verify remediation against an independent mock source.

The application is architected as a clean full-stack monorepo with separate **Frontend** and **Backend** directories.

---

## Architecture & Layout

```text
Access-Platform/
├── backend/                       # FastAPI + PostgreSQL 16 Backend
│   ├── app/                       # FastAPI application & SQLAlchemy models
│   ├── alembic/                   # Database migrations (PostgreSQL)
│   ├── tests/                     # Backend automated tests (pytest)
│   ├── Dockerfile                 # Python 3.12 production Dockerfile
│   └── requirements.txt           # Python dependencies
│
├── frontend/                      # React 19 + Next.js / Vite Frontend
│   ├── app/                       # Next.js App Router (Dashboard & Reviews)
│   ├── components/                # 50+ shadcn/ui components
│   ├── lib/                       # Domain logic & utilities
│   ├── tests/                     # Frontend automated tests
│   ├── Dockerfile                 # Node 24 production Dockerfile
│   └── package.json               # Frontend dependencies
│
├── .AI/                           # Project documentation & AI knowledge base
│   ├── FRONTEND.md                # Dedicated Frontend documentation
│   ├── BACKEND.md                 # Dedicated Backend documentation
│   ├── DATABASE.md                # PostgreSQL 16 schema & tables
│   ├── API.md                     # REST API & Swagger UI specifications
│   ├── ARCHITECTURE.md            # Multi-tier architecture & state machines
│   └── PROJECT_STRUCTURE.md       # Annotated project tree
│
├── docker-compose.yml             # Full-stack multi-container orchestration
├── sample-data/                   # Importable HR and permission CSV examples
└── docs/                          # Architecture, scope and Sinhala walkthrough
```

---

## Quick Start with Docker Compose

Run the entire platform (PostgreSQL 16, FastAPI backend, React frontend, and pgAdmin):

```bash
docker compose up -d
```

| Service | URL | Description |
| --- | --- | --- |
| **Frontend UI** | [http://localhost:5173](http://localhost:5173) | Governance Dashboard & Reviews |
| **FastAPI Backend** | [http://localhost:8000](http://localhost:8000) | REST API & Health Check |
| **Swagger UI** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API Documentation |
| **ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Alternative API Docs |
| **pgAdmin 4** | [http://localhost:5050](http://localhost:5050) | PostgreSQL Visual Manager (`admin@accessguard.local` / `admin`) |

To stop all services:
```bash
docker compose down
```

---

## Running Locally Without Docker

### 1. Backend (FastAPI + PostgreSQL)

Prerequisites: Python 3.12+, PostgreSQL running on `localhost:5432`.

```bash
cd backend
python -m venv venv
source venv/bin/activate       # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Run backend tests:
```bash
pytest -v
```

### 2. Frontend (React 19 + Next.js / Vite)

Prerequisites: Node.js 24+, pnpm 11+.

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

Run frontend tests & verification:
```bash
pnpm typecheck
pnpm test
pnpm build
```

---

## Key Capabilities

- **6 Configurable Risk Policies**: Departed employees (`LEAVER`), inactive accounts (`INACTIVE`), unverified owners (`ORPHANED`), department mismatches (`ROLE_MISMATCH`), expired contractors (`CONTRACT`), and expired temporary permissions (`EXPIRED`).
- **Independent Dual Approval**: Critical-severity findings (score ≥ 90) enforce a mandatory second independent reviewer.
- **Self-Approval Guard**: Reviewers cannot approve or review their own accounts.
- **Durable Remediation & Leases**: Revocation decisions queue durable remediation jobs with 2-minute worker leases and independent read-back verification.
- **Validated CSV Data Import**: Exact-file checksum deduplication, stable identifiers, conflicting-record detection, and bounded SQL parameters.
- **Append-Only Auditing**: Every decision, campaign scan, and policy modification is permanently recorded.
- **Formula Injection Protection**: Review evidence and audit CSV exports sanitize leading trigger characters (`=`, `+`, `-`, `@`).

---

## Five-Minute Demonstration

1. Open the UI as **Hashan Hirantha / Workspace admin**.
2. Navigate to **Access reviews**, open a critical finding, choose **Remove access**, enter a reason, and submit.
3. Switch to **Daniel Silva / Security reviewer**. Open the item under **Second approval** and confirm it independently.
4. Navigate to **Remediation**, inspect the queued job, and click **Execute & verify** (optionally simulate failure first to test safe retry).
5. Open **View evidence** to inspect the read-back source verification.
6. Inspect the **Audit trail** and download the CSV report.
7. Import `sample-data/access-assignments.csv` from **Data sources** to test CSV ingestion.
