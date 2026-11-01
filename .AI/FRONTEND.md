# AccessGuard — Frontend Documentation

## Overview

The AccessGuard frontend is a modern, responsive user access governance interface built with **React 19**, **Next.js 16** (via **Vinext** on **Vite 8**), and **Tailwind CSS 4**. It features comprehensive access review workflows, risk visualizations, role-based persona switching, and verified remediation inspection.

All frontend source files reside in the [`frontend/`](file:///e:/Access-Platform/frontend) directory.

---

## Tech Stack & Libraries

| Category             | Technology                      | Version     | Purpose                                            |
| -------------------- | ------------------------------- | ----------- | -------------------------------------------------- |
| **UI Library**       | React                           | 19.2.6      | Component framework with React Server Components   |
| **Framework**        | Next.js / Vinext                | 16.3.4 / 1.0| Full-stack application runner on Vite 8            |
| **Language**         | TypeScript                      | 5.9.3       | Static type safety and strict schema checking      |
| **Styling**          | Tailwind CSS                    | 4.2.1       | Utility-first responsive design system             |
| **Primitives**       | Radix UI / Base UI              | Latest      | Headless accessible primitives (dialogs, dropdowns)|
| **UI Kit**           | shadcn/ui                       | 0.3.0       | 50+ pre-built, themeable components                |
| **Data Visualization**| Recharts                        | 3.8.0       | Dashboard charts (certification status, risks)     |
| **Icons**            | Lucide React                    | 1.31.0      | Consistent iconography                             |
| **Forms & Validation**| React Hook Form + Zod           | 7.85 / 3.25 | Form state handling and schema validation          |
| **Notifications**    | Sonner                          | 2.0.8       | Toast notifications for actions and errors         |
| **Date Handling**    | date-fns                        | 4.4.0       | Date formatting and relative time calculations     |

---

## Directory Structure (`frontend/`)

```
frontend/
├── app/                              # Next.js App Router
│   ├── layout.tsx                    # Root HTML shell, fonts, and meta tags
│   ├── page.tsx                      # Main page mounting AccessGuard workspace
│   ├── workspace.tsx                 # Core UI component: Dashboard, Reviews, Remediation, Audit
│   ├── globals.css                   # Tailwind CSS 4 theme and global style variables
│   └── api/
│       └── workspace/
│           └── route.ts             # Workspace proxy / Edge route handler
│
├── components/                       # UI Component Library
│   ├── connector-error.tsx          # Error boundary / status fallback
│   └── ui/                          # 50+ shadcn/ui components
│       ├── accordion.tsx            # Expandable finding details
│       ├── alert-dialog.tsx         # Confirmation prompts
│       ├── badge.tsx                # Severity indicators (Critical, High, Medium, Low)
│       ├── button.tsx               # Standard action buttons
│       ├── card.tsx                 # Metric and summary containers
│       ├── chart.tsx                # Chart containers and tooltips
│       ├── dialog.tsx               # Review decision & detail modals
│       ├── dropdown-menu.tsx        # Action menus and persona selector
│       ├── form.tsx                 # Form field bindings
│       ├── input.tsx                # Text and filter inputs
│       ├── select.tsx               # Dropdown selectors
│       ├── sidebar.tsx              # Navigation sidebar
│       ├── table.tsx                # Data grids for reviews and audits
│       ├── tabs.tsx                 # Workflow view switcher
│       └── ...                      # 40+ additional primitives
│
├── hooks/
│   └── use-mobile.ts                # Mobile breakpoint detection (< 768px)
│
├── lib/                              # Client-side helpers and types
│   ├── utils.ts                     # cn() utility (clsx + tailwind-merge)
│   ├── domain.ts                    # Shared types, severity mappings, date math
│   └── service.ts                   # Client-side fetch utilities
│
├── public/
│   └── favicon.svg                  # SVG favicon
│
├── Dockerfile                        # Node 24 multi-stage frontend Dockerfile
├── .dockerignore                     # Docker ignore rules
├── .env.example                      # Frontend environment variable template
├── package.json                      # Dependencies and scripts
├── tsconfig.json                     # TypeScript compiler options
├── vite.config.ts                    # Vite / Vinext bundler configuration
└── components.json                   # shadcn/ui registry config
```

---

## Core Views & Capabilities

### 1. Governance Dashboard
- **Executive KPI Cards**: Real-time counts of pending reviews, critical severity findings, active certifications, and open remediation jobs.
- **Risk Distribution Chart**: Visual breakdown of findings across the 6 policy categories (Leaver, Inactive, Orphaned, Role Mismatch, Contractor, Expired).
- **Campaign Progress**: Visual percentage indicator of certification completion.

### 2. Access Reviews Tab
- **Filterable Data Grid**: Filter by severity (`critical`, `high`, `medium`, `low`), review status, or target application.
- **Evidence Drawer / Modal**: Shows complete snapshot captured at scan time (identity details, entitlement permissions, source sync timestamps).
- **Decision Action Bar**:
  - **Keep**: Retain access with mandatory justification note.
  - **Remove**: Revoke entitlement, triggering an automated remediation job.
  - **Investigate**: Flag uncertain findings back for review.
  - **Exception**: Grant temporary exception (1–90 days).
- **Critical Review Dual-Approval Indicator**: Clear banner indicating when a critical finding requires a second independent approver.

### 3. Remediation Tracking Tab
- **Job Status Pipeline**: View jobs in `queued`, `executing`, `verified`, or `failed` states.
- **Execution & Retry**: Trigger manual remediation execution or retry failed jobs.
- **Verification Evidence**: Inspect read-back confirmation from the independent mock source.

### 4. Audit Trail Tab
- **Event Log**: Searchable table displaying actor, action, target entity, timestamp, and details.
- **CSV Export**: Direct one-click download for review evidence and compliance audit logs.

### 5. Data Sources & CSV Import
- **Connected Systems**: Status cards for AWS, GitHub, Finance ERP, M365, and People Directory.
- **File Uploader**: Drag-and-drop CSV importer for HR identity files and permission assignments with instant preview and validation.

---

## Persona Simulator

The frontend header provides a **Persona Switcher** allowing evaluation of role-based capabilities without separate logins:

| Persona | Name | Role | Badge | Permissions |
| ------- | ---- | ---- | ----- | ----------- |
| `admin` | Hashan Hirantha | Workspace Admin | `Admin` | Full access: Scan, Import, Policy, Execute, Decide |
| `reviewer` | Maya Perera | Department Reviewer | `Reviewer` | Review assigned grants; cannot scan or execute |
| `security` | Daniel Silva | Security Lead | `Security` | 2nd approval for critical reviews; execute remediations |
| `auditor` | Alex Morgan | Compliance Auditor | `Auditor` | Read-only view of dashboard and audit trail |

The selected persona is transmitted via the `x-demo-persona` HTTP header on all API calls.

---

## Development & Build Commands

```bash
# Navigate to frontend
cd frontend

# Install dependencies
pnpm install --frozen-lockfile

# Start local development server (http://localhost:5173)
pnpm dev

# Type check
pnpm typecheck

# Production build
pnpm build

# Linting
pnpm lint
```

## Running with Docker

```bash
# Run standalone frontend container
docker build -t accessguard-frontend ./frontend
docker run -p 5173:5173 accessguard-frontend

# Or run via root docker-compose
docker compose up frontend
```

