# Core Features

## 1. Risk Assessment Engine

Six configurable policies that automatically detect access risks:

| Policy Code      | Risk Score | What It Detects                                             |
| ---------------- | ---------- | ----------------------------------------------------------- |
| `LEAVER`         | 100        | Terminated employees with still-active access               |
| `CONTRACT`       | 90         | Contractors past their contract end date                    |
| `EXPIRED`        | 88         | Temporary permissions past their approved expiry            |
| `INACTIVE`       | 56–85      | Human accounts with no activity beyond configurable threshold|
| `ROLE_MISMATCH`  | 82         | Privileged permissions outside department baseline          |
| `ORPHANED`       | 78         | Unverified-owner accounts (no identity mapping)             |

Additional detection:
- `DATA_QUALITY` (score 40–45) — Stale source data or missing activity records

Each finding produces:
- **Risk score** (0–100)
- **Severity** — critical (≥90), high (≥70), medium (≥40), low (<40)
- **Reason codes** — machine-readable policy identifiers
- **Human-readable explanations** — actionable descriptions for reviewers
- **Recommendation** — suggested action (remove, investigate, confirm)

Policies are individually togglable and threshold-configurable per workspace.

---

## 2. Access Review Workflow

- **Campaign-based scanning** — Reviews are grouped into named campaigns with due dates
- **Automated reviewer assignment** — Manager of the identity, with security team fallback
- **Self-approval prevention** — Reviewers cannot approve their own access
- **Decision options:**
  - **Keep** — Access is legitimate and needed
  - **Remove** — Access should be revoked (creates remediation job)
  - **Investigate** — Return for further analysis
  - **Expiring exception** — Temporary approval (1–90 days)
- **Evidence snapshots** — Each review captures identity context, source timestamps, permission versions, and policy settings at scan time

---

## 3. Critical Independent Approval

For critical-severity findings (score ≥ 90):
- First reviewer proposes a decision → status moves to `awaiting_second`
- A different reviewer independently confirms or returns to investigation
- The same employee **cannot** supply both approvals
- Nobody may review **their own** access
- Exceptions must still expire within 1–90 days at confirmation time

---

## 4. Remediation & Verification

- **Durable job queue** — Remediation jobs persist across requests
- **Status lifecycle:** `queued` → `executing` → `verified` / `failed`
- **Optimistic concurrency** — Version-conditional writes prevent conflicts
- **Worker leases** — Two-minute leases enable crash recovery
- **Independent verification** — Mock source write + read-back confirmation
- **Safe retries** — Failed or lease-expired jobs can be safely re-executed
- **Transactional consistency** — Remediation created in same batch as the review decision

---

## 5. Data Import (CSV)

- **Supported types:** HR identities (`hr`) and access assignments (`access`)
- **Validation:** Full parse and validation before transaction begins
- **Deduplication:** Exact file checksum prevents re-import of identical files
- **Stable identifiers:** Employee/provider keys preserved across imports
- **Conflict detection:** Conflicting owner or activity metadata is rejected
- **Bounded SQL:** Multi-row inserts capped at 100 bound parameters per statement
- **Limits:** Up to 1 MB / 1,000 rows per import
- **Additive/upsert:** Omitted rows are retained; imports don't delete existing data
- **Foreign key safety:** Insertion order respects FK constraints

---

## 6. Audit & Compliance

- **Append-only audit events** for every significant action
- **Authenticated principal attribution** — Every event tied to verified identity
- **CSV exports:**
  - Review evidence export (includes captured evidence snapshots)
  - Full audit history export
- **Formula injection protection** — Exports sanitize cells against spreadsheet formula attacks
- **Export operations are themselves audited**
- **Latest 500 events** displayed in UI; full history available via export

---

## 7. Dashboard & UI

- **Responsive design** — Works on desktop and narrow screens
- **Database-derived metrics** — Real-time counts from live data
- **Activity charts** — Visual representation of review progress (Recharts)
- **Certification progress** — Track campaign completion
- **Persona simulation** — Switch between 4 demo roles to exercise different capabilities
- **50+ shadcn/ui components** — Consistent, accessible design system

