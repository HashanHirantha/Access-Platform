# Demo Personas

## Overview

AccessGuard includes 4 demo personas that simulate role-based access within a private workspace. The authenticated owner can switch between personas using the `x-demo-persona` header to exercise different server-side role checks.

> **Note:** Persona simulation is a demo feature. It is not a substitute for enterprise multi-user RBAC. Server-side role and assignment checks are fully exercised by the prototype.

## Personas

### Hashan Hirantha — Workspace Admin
| Property     | Value         |
| ------------ | ------------- |
| **Key**      | `admin`       |
| **Employee** | `EMP001`      |
| **Initials** | HH            |

**Capabilities:**
- Run risk scans and create campaigns
- Import HR and access CSV data
- Configure and toggle risk policies
- Record review decisions (when assigned)
- Execute and verify remediations
- Sync external data sources
- View dashboard, audit trail, and exports

---

### Maya Perera — Department Reviewer
| Property     | Value         |
| ------------ | ------------- |
| **Key**      | `reviewer`    |
| **Employee** | `EMP002`      |
| **Initials** | MP            |

**Capabilities:**
- Review and decide on assigned access reviews
- Cannot run scans, import data, or execute remediations
- Cannot configure policies

---

### Daniel Silva — Security Reviewer
| Property     | Value         |
| ------------ | ------------- |
| **Key**      | `security`    |
| **Employee** | `EMP003`      |
| **Initials** | DS            |

**Capabilities:**
- Provide independent second approval for critical reviews
- Execute and verify remediations
- Review access assigned to security queue
- Acts as fallback reviewer when manager is unavailable

---

### Alex Morgan — Read-Only Auditor
| Property     | Value         |
| ------------ | ------------- |
| **Key**      | `auditor`     |
| **Employee** | `EMP004`      |
| **Initials** | AM            |

**Capabilities:**
- View dashboard and metrics
- View audit trail
- Cannot make decisions, run scans, or modify data

## Role Authorization Matrix

| Action            | Admin | Reviewer | Security | Auditor |
| ----------------- | :---: | :------: | :------: | :-----: |
| Run risk scan     | ✅    | ❌       | ❌       | ❌      |
| Import CSV data   | ✅    | ❌       | ❌       | ❌      |
| Configure policies| ✅    | ❌       | ❌       | ❌      |
| Sync sources      | ✅    | ❌       | ❌       | ❌      |
| Decide reviews    | ✅*   | ✅*      | ✅*      | ❌      |
| Second approval   | ✅*   | ✅*      | ✅*      | ❌      |
| Execute remediation| ✅   | ❌       | ✅       | ❌      |
| View dashboard    | ✅    | ✅       | ✅       | ✅      |
| Export reports     | ✅    | ✅       | ✅       | ✅      |

*Subject to assignment checks, self-review prevention, and independent approval rules.

## Five-Minute Demo Walkthrough

1. Open **Access reviews** as **Hashan Hirantha / Workspace admin**
2. Open a critical finding → choose **Remove access** → enter evidence-based reason → record
3. Switch to **Daniel Silva / Security reviewer** → open same item from **Second approval** → confirm independently with reason
4. Open **Remediation** → inspect queued job → choose **Execute & verify** (optionally simulate failure first)
5. Open **View evidence** to inspect observed mock-source state and version
6. Inspect **Audit trail** → export the report
7. Import `sample-data/access-assignments.csv` from **Data sources** → **Start review** to evaluate

