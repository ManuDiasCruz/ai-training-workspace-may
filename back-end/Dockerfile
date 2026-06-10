# Prisma 3.x loads the system OpenSSL, so use a glibc image and make sure
# openssl is present (bookworm ships OpenSSL 3, matching the 3.0.x engine).
FROM node:20-bookworm-slim

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package*.json ./
RUN npm ci --no-audit --no-fund

COPY . .
RUN npm run build

ENV NODE_ENV=production
EXPOSE 5000

# Apply pending migrations, then start the compiled server.
CMD ["sh", "-c", "npx prisma migrate deploy && node dist/server.js"]
