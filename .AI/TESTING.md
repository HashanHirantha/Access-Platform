# Testing

## Overview

AccessGuard includes automated testing across both its **Python FastAPI backend** and its **TypeScript frontend**.

---

## 1. Python Backend Testing (pytest)

### Running Python Tests

```bash
cd backend
# With virtual environment active:
pytest -v

# Run only domain tests
pytest tests/test_domain.py -v

# Run only API tests
pytest tests/test_api.py -v
```

### Python Test Suite (`backend/tests/`)

| File                           | Type        | Description                                                          |
| ------------------------------ | ----------- | -------------------------------------------------------------------- |
| `tests/test_domain.py`         | Unit        | Pure risk rules (6 policies), self-review prevention, dual approval   |
| `tests/test_api.py`            | Integration | FastAPI endpoints (`/health`, `/api/workspace`, headers, OpenAPI)    |

### Backend Coverage Highlights
- ✅ **LEAVER Policy**: Terminated employee with active account yields score 100, critical severity.
- ✅ **ORPHANED Policy**: Human account without linked identity yields score 78, high severity.
- ✅ **INACTIVE Policy**: Human account without activity beyond threshold triggers review; elevated score for privileged grants.
- ✅ **Leave Status Exemption**: Inactive policy skipped when employee is on approved leave.
- ✅ **ROLE_MISMATCH Policy**: Privileged grant outside approved department baseline flagged.
- ✅ **CONTRACT Policy**: Contractor past contract end date triggers critical score 90.
- ✅ **EXPIRED Policy**: Temporary grant past approved expiration date flagged with score 88.
- ✅ **Self-Review Prevention**: Rejects reviewer attempting to approve their own access (`DomainError: 403`).
- ✅ **Critical Dual Approval**: Rejects when the same reviewer attempts to provide both first and second approval.

---

## 2. TypeScript / Frontend Testing (Node.js Test Runner)

### Running TypeScript Tests

```bash
# Run all 35 tests
pnpm test

# TypeScript type checking
pnpm typecheck

# Full CI verification pipeline
pnpm typecheck && pnpm test && pnpm build
```

### TypeScript Test Files (`tests/`)

| File                     | Type         | Description                                                |
| ------------------------ | ------------ | ---------------------------------------------------------- |
| `tests/domain.test.ts`   | Unit         | TypeScript domain logic, risk policies, CSV parsing        |
| `tests/workflows.test.ts`| Integration  | Full API/service workflows against in-memory SQLite D1 DB  |
| `tests/auth.ts`          | Test Utility | Authentication mocks                                       |
| `tests/database.ts`      | Test Utility | In-memory SQLite transaction & D1 batch adapter            |
| `tests/env.ts`           | Test Utility | Test environment configuration                             |

### Frontend / Edge Coverage Highlights
- ✅ Full scan → decide → execute → verify lifecycle
- ✅ Safe retry after simulated connector failure
- ✅ Optimistic concurrency conflict detection
- ✅ Evidence change invalidation & re-scan requirement
- ✅ Worker lease recovery after failure
- ✅ Cross-tenant isolation verification
- ✅ 1,000-row CSV import stress test
- ✅ CSV export formula injection protection (`=`, `+`, `-`, `@`)

---

## CI Pipeline

Continuous integration is defined in `.github/workflows/main.yml` and `ci.yml`:

```yaml
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 24
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm typecheck
      - run: pnpm test
      - run: pnpm build
```
