# ---- Build stage ----
FROM node:22-slim AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

# The API base URL is baked into the bundle at build time (Create React App).
# Override with: docker build --build-arg REACT_APP_API_BASE_URL=https://api.example.com
ARG REACT_APP_API_BASE_URL=http://localhost:5000
ENV REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL

COPY . .
RUN npm run build

# ---- Runtime stage ----
FROM nginx:1.27-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
