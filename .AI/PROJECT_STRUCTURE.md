# Project Structure

```
Access-Platform/
├── app/                              # Next.js app directory
│   ├── layout.tsx                    # Root layout with metadata
│   ├── page.tsx                      # Entry point → renders AccessGuard workspace
│   ├── workspace.tsx                 # Dashboard and all workflow UI interfaces
│   ├── globals.css                   # Responsive design system (Tailwind)
│   ├── chatgpt-auth.ts              # ChatGPT authentication helpers
│   └── api/
│       └── workspace/
│           └── route.ts             # Authenticated API — GET snapshot/exports, POST actions
│
├── lib/                              # Core application logic
│   ├── domain.ts                    # Pure domain: risk assessment, decision rules, authorization, CSV parsing
│   ├── service.ts                   # Use cases: scan, decide, execute, import, policy, sync
│   ├── repository.ts               # Tenant-scoped SQL access, transactions, seeding
│   ├── seed.ts                      # Reproducible synthetic workspace data generator
│   ├── connectors.ts               # Connector bindings for request context
│   ├── connector-contract.mts      # Connector contract/protocol definition
│   ├── connector-context.ts        # Request-scoped connector binding context
│   ├── connector-errors.mts        # Connector error types
│   ├── connector-preview.d.ts      # Connector preview type declarations
│   └── utils.ts                     # Utility functions (cn, className merging)
│
├── db/                               # Database layer
│   ├── schema.ts                    # Drizzle ORM schema — all 12 tables
│   └── index.ts                     # Database exports
│
├── drizzle/                          # Versioned SQL migrations
│   ├── 0000_handy_zuras.sql         # Initial schema
│   ├── 0001_productive_dreadnoughts.sql
│   ├── 0002_light_killmonger.sql
│   ├── 0003_marvelous_magdalene.sql
│   └── meta/                        # Migration snapshots and journal
│       ├── 0000_snapshot.json
│       ├── 0001_snapshot.json
│       ├── 0002_snapshot.json
│       ├── 0003_snapshot.json
│       └── _journal.json
│
├── components/                       # UI components
│   ├── connector-error.tsx          # Connector error display component
│   └── ui/                          # 50+ shadcn/ui primitives
│       ├── accordion.tsx
│       ├── alert-dialog.tsx
│       ├── alert.tsx
│       ├── aspect-ratio.tsx
│       ├── attachment.tsx
│       ├── avatar.tsx
│       ├── badge.tsx
│       ├── breadcrumb.tsx
│       ├── bubble.tsx
│       ├── button-group.tsx
│       ├── button.tsx
│       ├── calendar.tsx
│       ├── card.tsx
│       ├── carousel.tsx
│       ├── chart.tsx
│       ├── checkbox.tsx
│       ├── collapsible.tsx
│       ├── combobox.tsx
│       ├── command.tsx
│       ├── context-menu.tsx
│       ├── dialog.tsx
│       ├── direction.tsx
│       ├── drawer.tsx
│       ├── dropdown-menu.tsx
│       ├── empty.tsx
│       ├── field.tsx
│       ├── form.tsx
│       ├── hover-card.tsx
│       ├── input-group.tsx
│       ├── input-otp.tsx
│       ├── input.tsx
│       ├── item.tsx
│       ├── kbd.tsx
│       ├── label.tsx
│       ├── marker.tsx
│       ├── menubar.tsx
│       ├── message-scroller.tsx
│       ├── message.tsx
│       ├── native-select.tsx
│       ├── navigation-menu.tsx
│       ├── pagination.tsx
│       ├── popover.tsx
│       ├── progress.tsx
│       ├── radio-group.tsx
│       ├── resizable.tsx
│       ├── scroll-area.tsx
│       ├── select.tsx
│       ├── separator.tsx
│       ├── sheet.tsx
│       ├── sidebar.tsx
│       ├── skeleton.tsx
│       ├── slider.tsx
│       ├── sonner.tsx
│       ├── spinner.tsx
│       ├── switch.tsx
│       ├── table.tsx
│       ├── tabs.tsx
│       ├── textarea.tsx
│       ├── toggle-group.tsx
│       ├── toggle.tsx
│       └── tooltip.tsx
│
├── hooks/                            # Custom React hooks
│   └── use-mobile.ts               # Mobile breakpoint detection
│
├── tests/                            # 35 automated tests
│   ├── domain.test.ts               # Pure domain logic tests
│   ├── workflows.test.ts           # Full API/service workflow integration tests
│   ├── auth.ts                      # Test auth utilities
│   ├── database.ts                  # In-memory SQLite test adapter
│   ├── env.ts                       # Test environment setup
│   └── register.mjs                 # Test runner registration
│
├── worker/                           # Cloudflare Worker
│   └── index.ts                     # Worker entry point
│
├── scripts/                          # Build, CI, and dev tooling
│   ├── run-framework.mjs           # Framework runner (dev/build)
│   ├── migrate-local.mjs           # Local D1 migration runner
│   ├── execution-profile.mjs       # Execution environment detection
│   ├── sites-env.mjs               # Sites environment configuration
│   ├── sites-env.sh                # Sites env shell variant
│   ├── tool-environment.mjs        # Tool environment configuration
│   ├── build-verified.sh           # Build verification script
│   ├── install-ci.mjs              # CI installation (JS)
│   ├── install-ci.sh               # CI installation (shell)
│   ├── install-pnpm.sh             # pnpm installer
│   ├── npm-install.mjs             # npm install helper
│   ├── pnpm-install.mjs            # pnpm install helper
│   ├── connector-preview/          # Connector preview dev server
│   │   ├── connector-preview-session.mjs
│   │   ├── host-binding.mjs
│   │   ├── protocol.mjs
│   │   └── worker.mjs
│   └── vite/                        # Custom Vite plugins
│       ├── sites-vite-plugin.ts     # Sites integration plugin
│       ├── sites-vite-plugin.LICENSE
│       └── connector-preview-plugin.mjs
│
├── sample-data/                      # Importable demo data
│   ├── hr-identities.csv           # HR identity records
│   └── access-assignments.csv      # Permission/entitlement assignments
│
├── docs/                             # Documentation
│   ├── ARCHITECTURE.md              # Architecture, decision flow, requirement traceability
│   └── DEMO_SI.md                   # Sinhala language demonstration guide
│
├── examples/
│   └── d1/                          # D1 database example
│       ├── app/api/                 # Example API routes
│       └── db/schema.ts            # Example schema
│
├── public/
│   └── favicon.svg                  # App favicon
│
├── vendor/                           # Vendored dependencies
│
├── .github/workflows/
│   ├── ci.yml                       # CI pipeline: typecheck → test → build
│   └── main.yml                     # AccessGuard checks workflow
│
├── .openai/
│   └── hosting.json                 # ChatGPT Sites hosting configuration
│
├── package.json                      # Project manifest (accessguard v1.0.0)
├── vite.config.ts                    # Vite + Vinext + Cloudflare plugin config
├── drizzle.config.ts                # Drizzle-Kit config (SQLite dialect)
├── next.config.ts                   # Next.js configuration
├── tsconfig.json                    # TypeScript configuration
├── eslint.config.mjs                # ESLint configuration
├── postcss.config.mjs               # PostCSS config (Tailwind)
├── components.json                   # shadcn/ui component registry
├── cloudflare-env.d.ts              # Cloudflare env types (D1, R2)
├── pnpm-workspace.yaml              # pnpm workspace config
└── .npmrc                           # npm/pnpm configuration
```

## Key File Roles

| File                          | Responsibility                                              |
| ----------------------------- | ----------------------------------------------------------- |
| `app/workspace.tsx`           | Main UI — dashboard, reviews, remediation, audit, imports   |
| `app/api/workspace/route.ts`  | Auth boundary, origin checks, request/response routing     |
| `lib/domain.ts`               | Pure functions: risk scoring, authorization, CSV parsing    |
| `lib/service.ts`              | Orchestrates use cases (scan, decide, execute, import)      |
| `lib/repository.ts`           | SQL builder, tenant scoping, batch transactions, seeding    |
| `lib/seed.ts`                 | Generates reproducible synthetic demo workspace             |
| `db/schema.ts`                | Single source of truth for all database tables              |
| `vite.config.ts`              | Configures Vinext, Cloudflare Workers, D1/R2 bindings       |

