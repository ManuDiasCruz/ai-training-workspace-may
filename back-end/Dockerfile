# ---- Build & run the Sing Me a Song API ----
FROM node:20-alpine

WORKDIR /app

# Install dependencies (needs dev deps to compile TypeScript + generate Prisma).
COPY package*.json ./
RUN npm ci

# Copy source and build (prisma generate + tsc -> dist/).
COPY . .
RUN npm run build

ENV PORT=5000
EXPOSE 5000

# Apply pending migrations, then start the compiled server.
CMD ["sh", "-c", "npx prisma migrate deploy && npm start"]
