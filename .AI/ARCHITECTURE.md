# Architecture

## Design Principles

- **Single deployable** — Modular monolith with separated concerns, not microservices
- **Clean layer separation** — `domain.ts` → `service.ts` → `repository.ts`
- **Tenant isolation** — All queries scoped by workspace ID derived from authenticated identity, never from client input
- **Transactional consistency** — D1 batch API for atomic multi-statement operations
- **Evidence integrity** — Evidence changes invalidate stale decisions and executions
- **Optimistic concurrency** — Version checks prevent lost updates on all mutable entities

## Layer Architecture

```mermaid
flowchart TD
    UI["React Workspace UI<br/>(app/workspace.tsx)"] --> API["Authenticated Server API<br/>(app/api/workspace/route.ts)"]
    API --> Domain["Pure Domain Logic<br/>(lib/domain.ts)"]
    API --> Service["Workflow Service<br/>(lib/service.ts)"]
    Service --> Domain
    Service --> Repo["Tenant-Scoped Repository<br/>(lib/repository.ts)"]
    Repo --> DB["Cloudflare D1<br/>(SQLite)"]
    Service --> Adapter["Mock Source Adapter<br/>(lib/connectors.ts)"]
    Adapter --> Source["Independent Source State<br/>(source_access table)"]
    Source --> Verify["Read-back Verification"]
    Verify --> DB
    DB --> Reports["Audit & Evidence CSV Reports"]
```

### Layer Responsibilities

| Layer               | File                  | Responsibility                                                  |
| ------------------- | --------------------- | --------------------------------------------------------------- |
| **UI**              | `app/workspace.tsx`   | Dashboard, review workflow, remediation, audit trail, imports   |
| **API Boundary**    | `app/api/.../route.ts`| Authentication, origin checks, request routing, response format |
| **Domain (Pure)**   | `lib/domain.ts`       | Risk scoring, authorization, decision rules, CSV parsing — zero I/O |
| **Service**         | `lib/service.ts`      | Use case orchestration, transaction assembly, Zod validation    |
| **Repository**      | `lib/repository.ts`   | SQL construction, tenant scoping, batch transactions, seeding   |
| **Seed**            | `lib/seed.ts`         | Reproducible synthetic data for demo workspace initialization   |

## Decision State Machine

```mermaid
stateDiagram-v2
    [*] --> pending: Risk scan creates review

    pending --> keep: Reviewer approves
    pending --> revoke: Reviewer revokes (non-critical)
    pending --> exception: Reviewer grants exception
    pending --> investigation: Reviewer investigates
    pending --> awaiting_second: Reviewer proposes (critical)

    investigation --> keep: Reviewer approves
    investigation --> revoke: Reviewer revokes
    investigation --> exception: Reviewer grants exception
    investigation --> awaiting_second: Reviewer proposes (critical)

    awaiting_second --> keep: Second reviewer confirms keep
    awaiting_second --> revoke: Second reviewer confirms revoke
    awaiting_second --> exception: Second reviewer confirms exception
    awaiting_second --> investigation: Second reviewer returns

    revoke --> [*]: Remediation verified
    keep --> [*]: Review complete
    exception --> [*]: Exception expires → re-scan
```

## Remediation Lifecycle

```mermaid
stateDiagram-v2
    [*] --> queued: Revoke decision creates job

    queued --> executing: Worker claims lease
    executing --> verified: Source write + read-back OK
    executing --> failed: Source write fails

    failed --> queued: Retry requested
    queued --> executing: Re-claim lease

    verified --> [*]: Grant marked revoked
```

## Security Model

- **Authentication:** Platform identity established by ChatGPT Sites auth
- **Workspace isolation:** Workspace ID derived from authenticated principal — client cannot choose workspace
- **Role-based access:** 4 roles with server-side enforcement (admin, reviewer, security, auditor)
- **Self-review prevention:** Employees cannot review their own access
- **Independent approval:** Critical decisions require two different reviewers
- **Concurrency safety:** Optimistic version checks on reviews, grants, and source records
- **Audit attribution:** Every action attributed to authenticated principal
- **Export protection:** CSV exports sanitized against formula injection

## Prototype Boundaries

- All connectors are **simulations** — no real external permissions are modified
- Scans and execution are **user-triggered** — no background scheduler or job daemon
- Policies use **transparent rules**, not ML/AI models
- Client receives full workspace snapshot — pagination/filtering is client-side
- Audit records are application-protected but **not cryptographically immutable**
- No penetration test or compliance certification performed

## Scaling Considerations

For enterprise deployment:
- Server-side filtering and pagination
- Partitioned scan jobs with bounded batch sizes
- Real source adapters with rate limiting
- Outbox dispatcher and monitored queue
- Retry backoff and dead-letter handling
- Streamed exports and external audit event sinks
- Organization-approved policy thresholds and exception owners

