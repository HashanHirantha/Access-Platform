# API Reference

## Base Endpoints & OpenAPI Documentation

When running the FastAPI backend via Docker or local uvicorn:
- **Base URL:** `http://localhost:8000`
- **Interactive Swagger UI:** `http://localhost:8000/docs`
- **ReDoc Documentation:** `http://localhost:8000/redoc`
- **OpenAPI JSON Specification:** `http://localhost:8000/openapi.json`
- **Health Check:** `http://localhost:8000/health`

---

## Authentication & Headers

| Header | Type | Description |
| ------ | ---- | ----------- |
| `x-demo-persona` | string | Selects synthetic role: `admin`, `reviewer`, `security`, or `auditor` (default: `admin`) |
| `Authorization` | Bearer token | Platform authentication token in production |

---

## Endpoints

### 1. Health Check

```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "postgresql"
}
```

---

### 2. Get Workspace Snapshot

```http
GET /api/workspace
```

Returns the authenticated tenant's complete state: identities, connected sources, accounts, entitlements, active grants, review findings, remediations, policies, campaigns, and recent audits.

**Response Structure (`WorkspaceSnapshot`):**
```json
{
  "workspace": { "id": "UUID", "name": "Northstar workspace", "created_at": "ISO-8601" },
  "identities": [...],
  "sources": [...],
  "accounts": [...],
  "entitlements": [...],
  "grants": [...],
  "reviews": [...],
  "remediations": [...],
  "policies": [...],
  "audits": [...],
  "campaigns": [...]
}
```

---

### 3. Export CSV Reports

#### Review Evidence Export
```http
GET /api/workspace?export=reviews
```
- **Content-Type:** `text/csv`
- **Headers:** `Content-Disposition: attachment; filename=reviews-export.csv`
- **Safety:** Cells sanitized against formula injection (`=`, `+`, `-`, `@`).
- **Audit:** Automatically logs an `Audit` event for compliance.

#### Full Audit History Export
```http
GET /api/workspace?export=audit
```
- **Content-Type:** `text/csv`
- **Headers:** `Content-Disposition: attachment; filename=audit-export.csv`
- **Audit:** Automatically logs an `Audit` export event.

---

### 4. Workspace Actions

```http
POST /api/workspace
Content-Type: application/json
```

All actions are submitted to `POST /api/workspace` with an `"action"` discriminator property:

#### Action: `scan` (Run Risk Scan)
Evaluates all active grants against enabled policies and generates review findings.

```json
{
  "action": "scan",
  "name": "Q4 Continuous Access Review",
  "due_days": 7
}
```
- **Required Role:** `admin`
- **Response (200):**
  ```json
  {
    "message": "Scan complete. 12 new reviews created; 0 refreshed.",
    "created": 12,
    "refreshed": 0
  }
  ```

#### Action: `decide` (Record Review Decision)
Records a decision on a review finding with optimistic concurrency validation.

```json
{
  "action": "decide",
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "version": 1,
  "decision": "revoke",
  "note": "Employee transitioned out of finance department",
  "exception_until": null
}
```
- **Decisions:** `keep`, `revoke`, `investigate`, `exception`
- **Required Role:** Assigned reviewer, `admin`, or `security`
- **Critical Severity (score ≥ 90):** First decision sets status to `awaiting_second`; requires an independent second reviewer to finalize.
- **Revoke:** Automatically creates a durable `Remediation` job in `queued` status.

#### Action: `execute` (Execute & Verify Remediation)
Claims a 2-minute worker lease, executes the revocation against mock source, and reads back to verify.

```json
{
  "action": "execute",
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "simulate_failure": false
}
```
- **Required Role:** `admin` or `security`
- **Response (200):**
  ```json
  {
    "message": "Remediation executed and verified successfully."
  }
  ```

#### Action: `policy` (Update Risk Policy)
Updates policy threshold or toggles policy on/off.

```json
{
  "action": "policy",
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "enabled": true,
  "threshold": 60
}
```
- **Required Role:** `admin`

#### Action: `import` (Import CSV Data)
Imports HR identities or entitlement access assignments.

```json
{
  "action": "import",
  "kind": "hr",
  "filename": "q4-employees.csv",
  "csv": "employee_id,name,email,department,job_title\nEMP100,Jane Doe,jane@northstar.example,Engineering,Lead"
}
```
- **Limits:** Max 1 MB / 1,000 rows per import.
- **Deduplication:** SHA-256 checksum prevents duplicate file imports.
- **Required Role:** `admin`

---

## HTTP Status Codes & Error Handling

| Status Code | Reason | Example |
| ----------- | ------ | ------- |
| `200 OK` | Success | Action completed |
| `400 Bad Request` | Validation failure or illegal state | `"CSV exceeds 1,000 row limit."` |
| `403 Forbidden` | Authorization / role mismatch / self-approval | `"You cannot review your own access."` |
| `404 Not Found` | Entity not found | `"Review not found."` |
| `409 Conflict` | Optimistic concurrency conflict or duplicate import | `"This review changed. Refresh and review latest evidence."` |
| `500 Server Error` | Unexpected error | Database connection failure |
