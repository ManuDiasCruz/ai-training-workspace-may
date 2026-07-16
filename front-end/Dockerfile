# ---- Build the React app ----
FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# The API base URL is baked in at build time (Create React App requirement).
ARG REACT_APP_API_BASE_URL=http://localhost:5000
ENV REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL
RUN npm run build

# ---- Serve the static build with nginx ----
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
# SPA fallback so client-side routes (/top, /random) resolve to index.html.
RUN printf 'server {\n  listen 80;\n  location / {\n    root /usr/share/nginx/html;\n    try_files $uri /index.html;\n  }\n}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 80
