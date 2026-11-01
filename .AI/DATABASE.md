# Database Schema

## Overview

AccessGuard uses **PostgreSQL 16** with **SQLAlchemy 2.0** (async) as the ORM and **Alembic** for migrations. The schema defines **12 tables** with tenant isolation via `workspace_id` foreign keys with `CASCADE` deletes. All primary keys are `UUID v4`. The backend is powered by **FastAPI** with **asyncpg** as the async PostgreSQL driver.

## Entity Relationship

```mermaid
erDiagram
    workspaces ||--o{ identities : contains
    workspaces ||--o{ sources : contains
    workspaces ||--o{ campaigns : contains
    workspaces ||--o{ policies : contains
    workspaces ||--o{ audits : contains
    workspaces ||--o{ imports : contains

    sources ||--o{ accounts : provides
    sources ||--o{ entitlements : defines

    identities ||--o{ accounts : owns

    accounts ||--o{ grants : has
    entitlements ||--o{ grants : "granted via"

    grants ||--o{ reviews : "reviewed in"
    grants ||--o{ source_access : "tracked in"
    grants ||--o{ remediations : "remediated by"

    campaigns ||--o{ reviews : groups
    reviews ||--o{ remediations : triggers
```

## Connection Configuration

```python
# backend/app/config.py
DATABASE_URL = "postgresql+asyncpg://accessguard:accessguard@localhost:5432/accessguard"
```

```yaml
# docker-compose.yml — PostgreSQL 16 Alpine
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: accessguard
      POSTGRES_PASSWORD: accessguard
      POSTGRES_DB: accessguard
    ports:
      - "5432:5432"
```

## Tables

### `workspaces`
Tenant isolation root. Every other table references a workspace via `ON DELETE CASCADE`.

```sql
CREATE TABLE workspaces (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

| Column      | Type          | Constraints        | Description            |
| ----------- | ------------- | ------------------ | ---------------------- |
| `id`        | `UUID`        | PK, default uuid   | Workspace identifier   |
| `name`      | `VARCHAR(255)`| NOT NULL           | Display name           |
| `created_at`| `TIMESTAMPTZ` | NOT NULL, default  | Creation timestamp     |

---

### `identities`
Employee/people records imported from HR systems.

```sql
CREATE TABLE identities (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  UUID         NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    employee_id   VARCHAR(100) NOT NULL,
    name          VARCHAR(255) NOT NULL,
    email         VARCHAR(255) NOT NULL,
    department    VARCHAR(255) NOT NULL,
    job_title     VARCHAR(255) NOT NULL,
    manager_id    UUID         REFERENCES identities(id) ON DELETE SET NULL,
    status        VARCHAR(50)  NOT NULL DEFAULT 'active',
    contract_end  TIMESTAMPTZ
);

CREATE INDEX ix_identities_workspace ON identities(workspace_id);
CREATE UNIQUE INDEX ix_identities_employee ON identities(workspace_id, employee_id);
```

| Column        | Type           | Constraints                                | Description                    |
| ------------- | -------------- | ------------------------------------------ | ------------------------------ |
| `id`          | `UUID`         | PK                                         | Identity identifier            |
| `workspace_id`| `UUID`         | FK → workspaces, CASCADE                   | Tenant isolation               |
| `employee_id` | `VARCHAR(100)` | NOT NULL, unique per workspace             | Stable HR employee ID          |
| `name`        | `VARCHAR(255)` | NOT NULL                                   | Full name                      |
| `email`       | `VARCHAR(255)` | NOT NULL                                   | Email address                  |
| `department`  | `VARCHAR(255)` | NOT NULL                                   | Department name                |
| `job_title`   | `VARCHAR(255)` | NOT NULL                                   | Job title                      |
| `manager_id`  | `UUID`         | FK → identities, SET NULL                  | Self-referencing manager       |
| `status`      | `VARCHAR(50)`  | NOT NULL, default `active`                 | active / terminated / leave    |
| `contract_end`| `TIMESTAMPTZ`  | nullable                                   | Contractor end date            |

---

### `sources`
External systems providing access data (AWS, GitHub, Salesforce, etc.).

```sql
CREATE TABLE sources (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  UUID         NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name          VARCHAR(255) NOT NULL,
    category      VARCHAR(100) NOT NULL,
    icon          VARCHAR(100) NOT NULL,
    last_sync     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    status        VARCHAR(50)  NOT NULL DEFAULT 'healthy',
    mode          VARCHAR(50)  NOT NULL DEFAULT 'read'
);
```

| Column        | Type           | Constraints          | Description                 |
| ------------- | -------------- | -------------------- | --------------------------- |
| `id`          | `UUID`         | PK                   | Source identifier            |
| `workspace_id`| `UUID`         | FK → workspaces      | Tenant isolation             |
| `name`        | `VARCHAR(255)` | NOT NULL             | System name                  |
| `category`    | `VARCHAR(100)` | NOT NULL             | cloud / devops / finance     |
| `icon`        | `VARCHAR(100)` | NOT NULL             | UI icon identifier           |
| `last_sync`   | `TIMESTAMPTZ`  | NOT NULL, default    | Last sync timestamp          |
| `status`      | `VARCHAR(50)`  | NOT NULL, default    | healthy / degraded           |
| `mode`        | `VARCHAR(50)`  | NOT NULL, default    | Connection mode              |

---

### `accounts`
Provider-specific user accounts linked to identities.

```sql
CREATE TABLE accounts (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  UUID         NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    source_id     UUID         NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    identity_id   UUID         REFERENCES identities(id) ON DELETE SET NULL,
    external_id   VARCHAR(255) NOT NULL,
    kind          VARCHAR(50)  NOT NULL DEFAULT 'user',
    status        VARCHAR(50)  NOT NULL DEFAULT 'enabled',
    last_active   TIMESTAMPTZ,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX ix_accounts_workspace ON accounts(workspace_id);
CREATE INDEX ix_accounts_source ON accounts(source_id);
```

| Column        | Type           | Constraints                  | Description                  |
| ------------- | -------------- | ---------------------------- | ---------------------------- |
| `id`          | `UUID`         | PK                           | Account identifier           |
| `workspace_id`| `UUID`         | FK → workspaces, CASCADE     | Tenant isolation             |
| `source_id`   | `UUID`         | FK → sources, CASCADE        | Parent source system         |
| `identity_id` | `UUID`         | FK → identities, SET NULL    | Linked employee (nullable)   |
| `external_id` | `VARCHAR(255)` | NOT NULL                     | External account ID          |
| `kind`        | `VARCHAR(50)`  | NOT NULL, default `user`     | user / service / emergency   |
| `status`      | `VARCHAR(50)`  | NOT NULL, default `enabled`  | enabled / disabled           |
| `last_active` | `TIMESTAMPTZ`  | nullable                     | Last activity timestamp      |
| `created_at`  | `TIMESTAMPTZ`  | NOT NULL, default            | Creation timestamp           |

---

### `entitlements`
Permissions/roles within a source system.

```sql
CREATE TABLE entitlements (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id        UUID         NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    source_id           UUID         NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    privileged          BOOLEAN      NOT NULL DEFAULT false,
    allowed_departments VARCHAR[]    NOT NULL DEFAULT '{}'
);

CREATE INDEX ix_entitlements_source ON entitlements(source_id);
```

| Column              | Type           | Constraints               | Description                              |
| ------------------- | -------------- | ------------------------- | ---------------------------------------- |
| `id`                | `UUID`         | PK                        | Entitlement identifier                   |
| `workspace_id`      | `UUID`         | FK → workspaces, CASCADE  | Tenant isolation                         |
| `source_id`         | `UUID`         | FK → sources, CASCADE     | Parent source system                     |
| `name`              | `VARCHAR(255)` | NOT NULL                  | Permission name                          |
| `privileged`        | `BOOLEAN`      | NOT NULL, default `false` | Is this a privileged role                |
| `allowed_departments`| `VARCHAR[]`   | NOT NULL, default `{}`    | PostgreSQL array of allowed departments  |

---

### `grants`
Links accounts to entitlements — who has what access.

```sql
CREATE TABLE grants (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id   UUID        NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    account_id     UUID        NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    entitlement_id UUID        NOT NULL REFERENCES entitlements(id) ON DELETE CASCADE,
    state          VARCHAR(50) NOT NULL DEFAULT 'active',
    expires_at     TIMESTAMPTZ,
    version        INTEGER     NOT NULL DEFAULT 1
);

CREATE INDEX ix_grants_workspace_state ON grants(workspace_id, state);
CREATE INDEX ix_grants_account ON grants(account_id);
```

| Column          | Type          | Constraints                    | Description                    |
| --------------- | ------------- | ------------------------------ | ------------------------------ |
| `id`            | `UUID`        | PK                             | Grant identifier               |
| `workspace_id`  | `UUID`        | FK → workspaces, CASCADE       | Tenant isolation               |
| `account_id`    | `UUID`        | FK → accounts, CASCADE         | Which account                  |
| `entitlement_id`| `UUID`        | FK → entitlements, CASCADE     | Which permission               |
| `state`         | `VARCHAR(50)` | NOT NULL, default `active`     | active / revoked               |
| `expires_at`    | `TIMESTAMPTZ` | nullable                       | Temporary permission expiry    |
| `version`       | `INTEGER`     | NOT NULL, default `1`          | Optimistic concurrency version |

---

### `source_access`
Independent mock source state for remediation write + read-back verification.

```sql
CREATE TABLE source_access (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  UUID        NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    grant_id      UUID        NOT NULL REFERENCES grants(id) ON DELETE CASCADE,
    state         VARCHAR(50) NOT NULL DEFAULT 'active',
    version       INTEGER     NOT NULL DEFAULT 1,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

| Column        | Type          | Constraints                | Description                     |
| ------------- | ------------- | -------------------------- | ------------------------------- |
| `id`          | `UUID`        | PK                         | Source access record ID         |
| `workspace_id`| `UUID`        | FK → workspaces, CASCADE   | Tenant isolation                |
| `grant_id`    | `UUID`        | FK → grants, CASCADE       | Linked grant                    |
| `state`       | `VARCHAR(50)` | NOT NULL, default `active` | active / revoked                |
| `version`     | `INTEGER`     | NOT NULL, default `1`      | Conditional write version       |
| `updated_at`  | `TIMESTAMPTZ` | NOT NULL, default, auto    | Last update (auto-updated)      |

---

### `campaigns`
Review campaign grouping and scheduling.

```sql
CREATE TABLE campaigns (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  UUID         NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name          VARCHAR(255) NOT NULL,
    started_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    due_at        TIMESTAMPTZ  NOT NULL
);
```

---

### `reviews`
Access review findings with evidence, scores, and decisions. Uses **JSONB** for structured evidence and reason arrays.

```sql
CREATE TABLE reviews (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id       UUID         NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    grant_id           UUID         NOT NULL REFERENCES grants(id) ON DELETE CASCADE,
    campaign_id        UUID         NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    assignee_id        VARCHAR(255) NOT NULL,
    score              INTEGER      NOT NULL DEFAULT 0,
    severity           VARCHAR(20)  NOT NULL DEFAULT 'low',
    reasons            JSONB        NOT NULL DEFAULT '[]',
    codes              JSONB        NOT NULL DEFAULT '[]',
    recommendation     TEXT         NOT NULL DEFAULT '',
    status             VARCHAR(50)  NOT NULL DEFAULT 'pending',
    note               TEXT         NOT NULL DEFAULT '',
    first_actor        VARCHAR(255),
    proposal           VARCHAR(50),
    decision_id        UUID,
    snapshot_version   INTEGER      NOT NULL DEFAULT 1,
    source_snapshot_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
    evidence           JSONB        NOT NULL DEFAULT '{}',
    exception_until    TIMESTAMPTZ,
    due_at             TIMESTAMPTZ  NOT NULL,
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    decided_at         TIMESTAMPTZ,
    version            INTEGER      NOT NULL DEFAULT 1
);

CREATE INDEX ix_reviews_workspace_status ON reviews(workspace_id, status);
CREATE INDEX ix_reviews_grant ON reviews(grant_id);
-- Partial unique index: at most one open review per grant
CREATE UNIQUE INDEX ix_reviews_one_open_per_grant ON reviews(grant_id)
    WHERE status IN ('pending', 'investigation', 'awaiting_second');
```

| Column              | Type           | Constraints                  | Description                                    |
| ------------------- | -------------- | ---------------------------- | ---------------------------------------------- |
| `id`                | `UUID`         | PK                           | Review identifier                              |
| `workspace_id`      | `UUID`         | FK → workspaces              | Tenant isolation                               |
| `grant_id`          | `UUID`         | FK → grants                  | Reviewed permission grant                      |
| `campaign_id`       | `UUID`         | FK → campaigns               | Parent campaign                                |
| `assignee_id`       | `VARCHAR(255)` | NOT NULL                     | Assigned reviewer                              |
| `score`             | `INTEGER`      | NOT NULL                     | Risk score (0–100)                             |
| `severity`          | `VARCHAR(20)`  | NOT NULL                     | critical / high / medium / low                 |
| `reasons`           | `JSONB`        | NOT NULL                     | Human-readable reason array                    |
| `codes`             | `JSONB`        | NOT NULL                     | Policy code array                              |
| `recommendation`    | `TEXT`         | NOT NULL                     | Suggested action                               |
| `status`            | `VARCHAR(50)`  | NOT NULL                     | pending / investigation / awaiting_second / keep / revoke / exception |
| `note`              | `TEXT`         | NOT NULL                     | Reviewer's decision note                       |
| `first_actor`       | `VARCHAR(255)` | nullable                     | First approver (critical dual)                 |
| `proposal`          | `VARCHAR(50)`  | nullable                     | Proposed decision (awaiting second)            |
| `decision_id`       | `UUID`         | nullable                     | Unique decision token                          |
| `snapshot_version`  | `INTEGER`      | NOT NULL                     | Grant version at scan time                     |
| `source_snapshot_at`| `TIMESTAMPTZ`  | NOT NULL                     | Source sync timestamp at scan                  |
| `evidence`          | `JSONB`        | NOT NULL                     | Serialized evidence snapshot                   |
| `exception_until`   | `TIMESTAMPTZ`  | nullable                     | Exception expiry date                          |
| `due_at`            | `TIMESTAMPTZ`  | NOT NULL                     | Review due date                                |
| `created_at`        | `TIMESTAMPTZ`  | NOT NULL, default            | Creation timestamp                             |
| `decided_at`        | `TIMESTAMPTZ`  | nullable                     | Decision timestamp                             |
| `version`           | `INTEGER`      | NOT NULL                     | Optimistic concurrency version                 |

---

### `remediations`
Remediation job tracking for revoked access.

```sql
CREATE TABLE remediations (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id     UUID        NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    review_id        UUID        NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    grant_id         UUID        NOT NULL REFERENCES grants(id) ON DELETE CASCADE,
    status           VARCHAR(50) NOT NULL DEFAULT 'queued',
    attempts         INTEGER     NOT NULL DEFAULT 0,
    expected_version INTEGER     NOT NULL,
    error            TEXT,
    evidence         JSONB,
    lease_until      TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    verified_at      TIMESTAMPTZ
);

CREATE INDEX ix_remediations_workspace_status ON remediations(workspace_id, status);
```

---

### `policies`
Configurable risk detection policies.

```sql
CREATE TABLE policies (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  UUID         NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    code          VARCHAR(50)  NOT NULL,
    name          VARCHAR(255) NOT NULL,
    description   TEXT         NOT NULL,
    enabled       BOOLEAN      NOT NULL DEFAULT true,
    threshold     INTEGER      NOT NULL DEFAULT 0
);

CREATE UNIQUE INDEX ix_policies_workspace_code ON policies(workspace_id, code);
```

---

### `audits`
Append-only audit trail.

```sql
CREATE TABLE audits (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  UUID         NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    actor         VARCHAR(255) NOT NULL,
    principal     VARCHAR(255) NOT NULL,
    action        VARCHAR(255) NOT NULL,
    target        VARCHAR(255) NOT NULL,
    detail        TEXT         NOT NULL DEFAULT '',
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX ix_audits_workspace_date ON audits(workspace_id, created_at);
```

---

### `imports`
Import deduplication and history tracking.

```sql
CREATE TABLE imports (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  UUID         NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    checksum      VARCHAR(128) NOT NULL,
    filename      VARCHAR(255) NOT NULL,
    kind          VARCHAR(50)  NOT NULL,
    row_count     INTEGER      NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

---

## PostgreSQL-Specific Features Used

| Feature                  | Usage                                                    |
| ------------------------ | -------------------------------------------------------- |
| `UUID` primary keys      | All tables use `gen_random_uuid()` for distributed IDs   |
| `TIMESTAMPTZ`            | All timestamps are timezone-aware                        |
| `JSONB`                  | Review evidence, reasons, and codes stored as JSONB      |
| `VARCHAR[]` (arrays)     | `allowed_departments` uses native PostgreSQL arrays      |
| Partial unique index     | One open review per grant enforced at DB level           |
| `ON DELETE CASCADE`      | Workspace deletion cascades to all child records         |
| `ON DELETE SET NULL`     | Manager/identity references gracefully nullify           |
| Connection pooling       | SQLAlchemy async pool (20 connections, 10 overflow)      |

## Migrations (Alembic)

```bash
# Generate a new migration from model changes
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Backend Stack

| Component         | Technology          | Version |
| ----------------- | ------------------- | ------- |
| **API Framework** | FastAPI             | 0.115   |
| **ASGI Server**   | Uvicorn             | 0.34    |
| **ORM**           | SQLAlchemy (async)  | 2.0     |
| **PG Driver**     | asyncpg             | 0.31    |
| **Migrations**    | Alembic             | 1.15    |
| **Validation**    | Pydantic v2         | 2.11    |
| **Database**      | PostgreSQL          | 16      |

## Docker Quick Start

```bash
# Start PostgreSQL + FastAPI backend
docker compose up -d

# Check health
curl http://localhost:8000/health

# View logs
docker compose logs -f backend

# Stop
docker compose down

# Stop and remove data
docker compose down -v
```

| Service    | URL                          | Description          |
| ---------- | ---------------------------- | -------------------- |
| Backend    | http://localhost:8000        | FastAPI API          |
| API Docs   | http://localhost:8000/docs   | Swagger UI           |
| ReDoc      | http://localhost:8000/redoc  | ReDoc documentation  |
| PostgreSQL | localhost:5432               | Database             |
| pgAdmin    | http://localhost:5050        | Database admin panel |
