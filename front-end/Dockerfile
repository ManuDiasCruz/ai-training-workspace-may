# --- Build stage -----------------------------------------------------------
FROM node:18-bullseye-slim AS build

WORKDIR /app

# The API base URL is baked into the static bundle at build time.
ARG REACT_APP_API_BASE_URL=http://localhost:5000
ENV REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# --- Runtime stage ---------------------------------------------------------
FROM nginx:1.25-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
