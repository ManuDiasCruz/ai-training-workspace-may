# Production image for the Sing me a Song API.
# Build from the back-end directory:  docker build -t sing-me-a-song-api .
# Run:  docker run -p 5000:5000 -e DATABASE_URL=... sing-me-a-song-api
FROM node:20-slim AS build

# Prisma 3 needs OpenSSL 1.1 to detect its query engine binary target.
RUN apt-get update && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY prisma ./prisma
COPY tsconfig.json tsconfig.build.json ./
COPY src ./src

# `build` runs `prisma generate` before `tsc`, so the client is generated here.
RUN npm run build


FROM node:20-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV NODE_ENV=production
ENV PORT=5000

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY prisma ./prisma
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules/.prisma ./node_modules/.prisma
COPY --from=build /app/node_modules/@prisma/client ./node_modules/@prisma/client

EXPOSE 5000

# Apply pending migrations before serving, so a fresh database works on first
# boot. MODE is intentionally left unset: /tests/* must not exist in production.
CMD ["sh", "-c", "npx prisma migrate deploy && node dist/server.js"]
