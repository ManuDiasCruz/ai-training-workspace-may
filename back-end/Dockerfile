# Back-end (Express + Prisma) production image
FROM node:18-bullseye-slim

WORKDIR /app

# Prisma needs OpenSSL available to load its query engine.
RUN apt-get update \
  && apt-get install -y --no-install-recommends openssl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Install dependencies first for better layer caching.
COPY package*.json ./
RUN npm ci

# Copy sources and build.
COPY . .
RUN npx prisma generate && npm run build

EXPOSE 5000

# Apply pending migrations, then start the compiled server.
CMD ["sh", "-c", "npx prisma migrate deploy && node dist/server.js"]
