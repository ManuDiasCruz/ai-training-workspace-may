# syntax=docker/dockerfile:1

# ---------- Build stage ----------
FROM node:20-alpine AS builder
WORKDIR /app

# Install all dependencies (dev deps are needed for tsc / prisma generate).
COPY package*.json ./
RUN npm ci

# Generate the Prisma client and compile TypeScript to dist/.
COPY prisma ./prisma
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

# ---------- Runtime stage ----------
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Install dependencies (prisma CLI is required at boot for `migrate deploy`).
COPY package*.json ./
RUN npm ci

# Prisma schema + generated client + compiled JS.
COPY prisma ./prisma
RUN npx prisma generate
COPY --from=builder /app/dist ./dist

EXPOSE 5000

# Apply migrations, then start the compiled server.
CMD ["sh", "-c", "npx prisma migrate deploy && node dist/server.js"]
