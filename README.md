# AccessGuard

An executable user access review prototype for the Dialog Axiata TransitionX problem statement. Consolidate identity and entitlement evidence, prioritize access reviews, record accountable decisions, and verify remediation against an independent mock source.

The hosted app is private. Initial people, providers, activity and historical reviews are synthetic. No AWS, GitHub, Microsoft or finance credentials are required.

## Implemented

- Responsive dashboard with database-derived counts, activity charts and certification progress.
- Normalized SQL model for employees, accounts, entitlements, grants, sources, review campaigns, decisions, jobs, policies and audit events.
- Six configurable risk policies: departed employees, inactive human accounts, unverified owners, privileged department mismatches, expired contractors and expired temporary permissions.
- Validated, atomic HR and access CSV upserts. Exact-file deduplication, stable identifiers, conflicting-record detection and bounded SQL parameters. Up to 1 MB / 1,000 rows per import.
- Manager-based reviewer assignment with security fallback; self-approval prevention and mandatory independent approval for critical decisions.
- Keep, remove, investigate and expiring exception decisions with mandatory reasons.
- Durable remediation records, optimistic concurrency, worker leases, safe retries, independent mock-source writes and read-back verification.
- Evidence snapshots that include identity context, source timestamps, permission versions and policy settings. Evidence changes invalidate stale decisions and executions.
- Application append-only audit events, authenticated principal attribution and CSV evidence exports protected against spreadsheet formula injection.
- 35 automated tests including full API/service workflows, authorization, tenant isolation, concurrency, failure recovery and a 1,000-row import.

## Actual stack

React 19 + TypeScript; Vinext server routes running in a Cloudflare Worker; Cloudflare D1 (SQLite) + Drizzle migrations; Sites-owned ChatGPT authentication; Lucide icons; native Node test runner and an in-memory SQLite integration adapter.

The initial planning suggested NestJS/PostgreSQL. This implementation keeps the domain and service layers separate while using the supported hosted React/server/SQL environment so the complete prototype can be opened immediately. It does not contain a NestJS server, PostgreSQL instance, Keycloak deployment or trained ML model.

## Run locally

Prerequisites: Node.js 24+, pnpm 10, Git. Windows, macOS and Linux are supported by the portable starter profile.

```sh
pnpm install --frozen-lockfile
pnpm build
pnpm db:migrate:local
pnpm dev
```

Open the URL printed by the development server (normally `http://localhost:5173`). On a portable local preview, use the starter's `/signin-with-chatgpt?return_to=/` flow if prompted. The development-only API identity is `local-demo-owner` when no platform identity is present; it is disabled in production. Your demo workspace is seeded on its first authorized request.

`db:migrate:local` applies tracked SQL migrations through Wrangler's local migration runner. It does not contact or change a remote database. It requires a completed build so the local D1 binding configuration is available. Repeated runs skip migrations recorded by that runner. Do not replay SQL files manually against an existing database.

```sh
pnpm typecheck
pnpm test
pnpm build
```

Tests use disposable, in-memory databases and do not modify your preview or hosted data. Node's TypeScript transformation currently emits an experimental warning. This does not indicate a test failure.

## Five-minute demonstration

1. Open **Access reviews** as **Hashan Hirantha / Workspace admin**.
2. Open a critical finding, choose **Remove access**, enter an evidence-based reason and record the decision.
3. Switch to **Daniel Silva / Security reviewer**. Open the same item from **Second approval**, independently confirm it and add a reason.
4. Open **Remediation**, inspect the queued job and choose **Execute & verify**. Optionally simulate a connector failure first to demonstrate a safe retry.
5. Open **View evidence** to inspect the observed mock-source state and version.
6. Inspect **Audit trail** and export the report.
7. Import `sample-data/access-assignments.csv` from **Data sources**, then **Start review** to evaluate the new source. HR sample data is supplied separately.

Demo persona selection is a simulation available to the authenticated owner inside this private workspace. It is not a substitute for enterprise multi-user RBAC. Server-side role and assignment checks are exercised by the prototype, while the owner can intentionally switch between synthetic roles.

See [the Sinhala demonstration guide](docs/DEMO_SI.md) and [architecture and requirements](docs/ARCHITECTURE.md).

## Project layout

```text
app/workspace.tsx                 Dashboard and workflow interfaces
app/globals.css                   Responsive design system
app/api/workspace/route.ts        Authentication, origin checks, request/response boundary
lib/domain.ts                    Pure risk, decision, authorization and CSV logic
lib/service.ts                   Use cases and workflow orchestration
lib/repository.ts                Tenant-scoped SQL access and transactions
lib/seed.ts                      Reproducible synthetic workspace
db/schema.ts                     Drizzle schema
drizzle/                         Versioned SQL migrations and metadata
tests/                           Domain, API and database integration tests
sample-data/                     Importable HR and permission examples
docs/                            Architecture, scope and Sinhala walkthrough
.github/workflows/ci.yml         Type checks, tests and production build
```

## API

`GET /api/workspace` returns the current authenticated owner's workspace snapshot.

`GET /api/workspace?export=reviews` downloads a review evidence CSV, including captured evidence. `export=audit` downloads the audit history. Both export operations are audited. The UI displays the latest 500 audit events; audit export reads all stored events.

`POST /api/workspace` accepts JSON with one of the following actions:

| Action | Required demo role | Additional fields |
| --- | --- | --- |
| `scan` | admin | `name`, `dueDays` |
| `decide` | assigned reviewer, admin, or security, subject to independent approval checks | `id`, `version`, `decision`, `note`, optional `exceptionUntil` |
| `execute` | admin or security | `id`, optional `simulateFailure` |
| `policy` | admin | `id`, `enabled`, optional `threshold` |
| `sync` | admin | source `id` |
| `import` | admin | `kind` (`hr` / `access`), `csv`, `filename` |

The browser uses `x-demo-persona` to select a synthetic actor inside the authenticated owner's isolated sandbox. The header never grants membership in another owner's workspace. Unknown personas, cross-origin writes, stale evidence, conflicting versions and unauthorized decisions are rejected.

## Deliberate prototype boundaries

- All connectors, including execution for imported CSV permissions, modify the demo's independent source-state table. They do not change real external permissions. A CSV import is an additive/upsert snapshot, not an instruction to delete omitted accounts or grants.
- Scans, source syncs and execution are user-triggered. There is no unattended scheduler, email integration or production job daemon. Job records and leases survive requests, and execution/retry is explicitly initiated in the UI.
- Policies use transparent rules, not a trained model. A risk score is a review priority index, not attack probability. Imported permissions default to an unrestricted department baseline; privileged role-mismatch checks on those require a future configurable baseline catalog.
- No automated separation-of-duties detection, delegated reviewer management, external identity provider or live SCIM connector is implemented.
- The client receives the workspace snapshot and performs UI pagination/filtering locally. High-volume enterprise deployment needs server pagination, streamed exports, partitioned scans, connector rate limits and a dedicated worker/queue design.
- Audit records are protected from modification through application endpoints. They are not cryptographically immutable or externally certified. Database administrators retain database-level capabilities.
- The prototype has functional security tests; it has not received an independent penetration test or compliance certification.

## Before live enterprise integration

Replace persona simulation with verified organization membership and server-side role bindings; implement scoped read-only connectors; validate authoritative HR mappings and data retention policies; introduce a real approval-controlled write adapter and revocation rollback procedures; add background scheduling/queue execution, operational alerting, backup/restore validation, independent security review and a tamper-evident external audit sink. Use organization-approved policy thresholds and exception owners.

## Design references

- [NIST: least privilege](https://csrc.nist.gov/glossary/term/least_privilege)
- [OWASP authorization guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP logging guidance](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- [Microsoft access-review recommendations](https://learn.microsoft.com/en-us/entra/id-governance/review-recommendations-access-reviews)

These references inform the design; they do not constitute certification.
