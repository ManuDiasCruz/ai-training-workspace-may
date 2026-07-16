# syntax=docker/dockerfile:1

# ---------- Build stage ----------
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

# The API base URL is baked into the static bundle at build time.
ARG REACT_APP_API_BASE_URL=http://localhost:5000
ENV REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL

COPY . .
RUN npm run build

# ---------- Runtime stage (static files served by nginx) ----------
FROM nginx:alpine AS runner
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
