# ============================================================================
# AccessGuard — React 19 / Next.js Frontend Dockerfile
# ============================================================================

FROM node:24-alpine AS base

# Install pnpm
RUN corepack enable && corepack prepare pnpm@11.25.0 --activate

WORKDIR /app

# ---------------------------------------------------------------------------
# Stage 1: Dependencies
# ---------------------------------------------------------------------------
FROM base AS deps
WORKDIR /app

COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

# ---------------------------------------------------------------------------
# Stage 2: Development / Builder
# ---------------------------------------------------------------------------
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=development
ENV PORT=5173

COPY --from=deps /app/node_modules ./node_modules
COPY . .

EXPOSE 5173

CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "5173"]

