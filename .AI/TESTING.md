# Testing

## Overview

AccessGuard has **35 automated tests** covering domain logic, API workflows, authorization, concurrency, failure recovery, and data import. Tests use the **native Node.js test runner** with disposable in-memory SQLite databases — no external dependencies or test frameworks required.

## Running Tests

```bash
# Run all tests
pnpm test

# TypeScript check (runs before tests in CI)
pnpm typecheck

# Full CI pipeline
pnpm typecheck && pnpm test && pnpm build
```

## Test Files

| File                    | Type           | Description                                             |
| ----------------------- | -------------- | ------------------------------------------------------- |
| `tests/domain.test.ts`  | Unit           | Pure domain logic — risk rules, authorization, CSV parsing |
| `tests/workflows.test.ts`| Integration   | Full API/service workflows against disposable databases  |
| `tests/auth.ts`         | Helper         | Test authentication utilities                            |
| `tests/database.ts`     | Helper         | In-memory SQLite adapter (simulates D1)                  |
| `tests/env.ts`          | Helper         | Test environment setup                                   |
| `tests/register.mjs`    | Setup          | Test runner registration and TypeScript support           |

## Test Coverage Areas

### Domain Logic Tests
- ✅ Risk assessment — positive and negative cases for all 6 policies
- ✅ Service account exemptions (no human inactivity rules)
- ✅ Leave-status handling (inactive policy skipped for employees on leave)
- ✅ Data quality flags for missing or stale activity data
- ✅ Authorization checks — role-based access enforcement
- ✅ Self-approval prevention
- ✅ Independent critical approval rules
- ✅ CSV parsing and validation

### Workflow Integration Tests
- ✅ Full scan → decide → execute → verify lifecycle
- ✅ Critical dual-approval workflow
- ✅ Remediation failure and safe retry
- ✅ Optimistic concurrency conflict detection
- ✅ Evidence change invalidation
- ✅ Lease recovery after worker interruption
- ✅ Tenant isolation — cross-workspace protection
- ✅ 1,000-row CSV import stress test
- ✅ CSV export and formula injection protection
- ✅ Import deduplication (checksum-based)

## Test Infrastructure

- **In-memory SQLite adapter** — Reproduces D1 SQL execution and batch rollback behavior
- **Disposable databases** — Each test gets a fresh database, no cleanup needed
- **No network** — All tests run offline
- **No external services** — No Docker, no cloud dependencies
- **TypeScript support** — `--experimental-transform-types` flag (warning is expected, not a failure)

## CI Pipeline

Defined in `.github/workflows/ci.yml` and `.github/workflows/main.yml`:

```yaml
steps:
  - pnpm install --frozen-lockfile
  - pnpm typecheck
  - pnpm test
  - pnpm build
```

Runs on: `ubuntu-latest`, Node.js 24, pnpm (version from `packageManager` field)

