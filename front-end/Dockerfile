# Front-end (Create React App) build, served by nginx
FROM node:18-bullseye-slim AS build

WORKDIR /app

# Cypress is a dev dependency we don't need for the production build.
ENV CYPRESS_INSTALL_BINARY=0

COPY package*.json ./
RUN npm ci

COPY . .

# REACT_APP_API_BASE_URL is baked in at build time. Default is empty so the
# SPA calls the API on its own origin and nginx proxies it to the back-end.
ARG REACT_APP_API_BASE_URL=""
ENV REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
