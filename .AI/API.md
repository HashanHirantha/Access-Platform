# API Reference

## Base Endpoint

All API requests go through `/api/workspace`.

## Authentication

Requests are authenticated via ChatGPT Sites-owned authentication. In local development, the `local-demo-owner` identity is used when no platform identity is present (disabled in production).

The `x-demo-persona` header selects a synthetic actor inside the authenticated owner's isolated sandbox. It never grants membership in another owner's workspace.

---

## GET Endpoints

### Get Workspace Snapshot

```
GET /api/workspace
```

Returns the current authenticated owner's complete workspace snapshot including identities, sources, accounts, entitlements, grants, reviews, remediations, policies, audits, and campaigns.

### Export Review Evidence

```
GET /api/workspace?export=reviews
```

Downloads a CSV file containing review evidence including captured evidence snapshots. This export operation is itself audited.

### Export Audit History

```
GET /api/workspace?export=audit
```

Downloads a CSV file containing the full audit history. The UI displays the latest 500 events; this export reads all stored events. This export operation is itself audited.

---

## POST Actions

```
POST /api/workspace
Content-Type: application/json

{ "action": "<action_name>", ...fields }
```

### `scan` — Run Risk Scan

Creates a new review campaign and evaluates all active grants against enabled policies.

| Field     | Type   | Required | Default                     |
| --------- | ------ | -------- | --------------------------- |
| `name`    | string | No       | "Continuous access review"  |
| `dueDays` | number | No       | 7                           |

**Required role:** admin  
**Response:** `{ message, created, refreshed }`

### `decide` — Record Review Decision

Records a keep, revoke, investigation, or exception decision on a review.

| Field            | Type   | Required | Description                    |
| ---------------- | ------ | -------- | ------------------------------ |
| `id`             | string | Yes      | Review ID                      |
| `version`        | number | Yes      | Current review version (OCC)   |
| `decision`       | string | Yes      | keep, revoke, investigate, exception |
| `note`           | string | Yes      | Mandatory reason for decision  |
| `exceptionUntil` | string | No       | ISO date for exception expiry  |

**Required role:** Assigned reviewer, admin, or security (subject to independent approval checks)  
**Error cases:** Version conflict (409), stale evidence (409), unauthorized (403)

### `execute` — Execute Remediation

Executes and verifies a remediation job for a revoked permission.

| Field             | Type    | Required | Description                    |
| ----------------- | ------- | -------- | ------------------------------ |
| `id`              | string  | Yes      | Remediation job ID             |
| `simulateFailure` | boolean | No       | Simulate a connector failure   |

**Required role:** admin or security

### `policy` — Update Policy

Enables/disables a risk policy or adjusts its threshold.

| Field       | Type    | Required | Description                 |
| ----------- | ------- | -------- | --------------------------- |
| `id`        | string  | Yes      | Policy ID                   |
| `enabled`   | boolean | Yes      | Enable/disable the policy   |
| `threshold` | number  | No       | Configurable threshold      |

**Required role:** admin

### `sync` — Sync Source

Synchronizes an external data source.

| Field | Type   | Required | Description |
| ----- | ------ | -------- | ----------- |
| `id`  | string | Yes      | Source ID   |

**Required role:** admin

### `import` — Import CSV Data

Imports HR identities or access assignments from CSV files.

| Field      | Type   | Required | Description                  |
| ---------- | ------ | -------- | ---------------------------- |
| `kind`     | string | Yes      | `hr` or `access`             |
| `csv`      | string | Yes      | CSV content (max 1 MB)       |
| `filename` | string | Yes      | Original filename            |

**Required role:** admin  
**Limits:** 1 MB / 1,000 rows per import

---

## Error Responses

| Status | Condition                                    |
| ------ | -------------------------------------------- |
| 400    | Validation error or domain rule violation    |
| 403    | Insufficient role or authorization           |
| 404    | Review or resource not found                 |
| 409    | Version conflict or stale evidence           |

