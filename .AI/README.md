# AccessGuard — AI Project Context

## Overview

AccessGuard is an **enterprise user access review and governance platform** built as an executable prototype for the Dialog Axiata TransitionX problem statement. It consolidates identity and entitlement evidence, prioritizes access reviews using configurable risk policies, records accountable decisions with independent approvals, and verifies remediation against an independent mock source.

> All data is synthetic. No real AWS, GitHub, Microsoft, or finance credentials are required.

## Tech Stack

| Layer              | Technology                                                     |
| ------------------ | -------------------------------------------------------------- |
| **Frontend**       | React 19, TypeScript 5.9, Tailwind CSS 4, Radix UI, shadcn/ui |
| **Framework**      | Next.js 16 (via Vinext on Vite 8)                              |
| **Backend**        | Vinext server routes running in a Cloudflare Worker             |
| **Database**       | Cloudflare D1 (SQLite) with Drizzle ORM & migrations           |
| **Auth**           | ChatGPT Sites-owned authentication (local dev: mock auth)      |
| **Icons**          | Lucide React                                                   |
| **Forms**          | React Hook Form + Zod validation                               |
| **Charts**         | Recharts                                                       |
| **Package Manager**| pnpm 11                                                        |
| **Runtime**        | Node.js 24+                                                    |
| **CI/CD**          | GitHub Actions (typecheck → test → build)                      |
| **Testing**        | Native Node.js test runner with in-memory SQLite adapter        |

## Quick Commands

```bash
pnpm install --frozen-lockfile   # Install dependencies
pnpm dev                         # Dev server (http://localhost:5173)
pnpm build                       # Production build
pnpm start                       # Local preview via Wrangler
pnpm typecheck                   # TypeScript check
pnpm test                        # Run 35 automated tests
pnpm lint                        # ESLint
pnpm db:generate                 # Generate Drizzle migrations
pnpm db:migrate:local            # Apply migrations to local D1
```

## Documentation Index

| File                                        | Description                                    |
| ------------------------------------------- | ---------------------------------------------- |
| [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) | Full annotated directory tree                 |
| [FEATURES.md](./FEATURES.md)               | Core features and capabilities                  |
| [DATABASE.md](./DATABASE.md)               | Schema, tables, and data model                   |
| [API.md](./API.md)                         | API endpoints and actions                        |
| [ARCHITECTURE.md](./ARCHITECTURE.md)       | Architecture, patterns, and design decisions     |
| [TESTING.md](./TESTING.md)                 | Test strategy, coverage, and commands            |
| [PERSONAS.md](./PERSONAS.md)              | Demo personas and role-based access               |

