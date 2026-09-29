# Multi-stage Dockerfile for React 18 SPA with Vite 5
FROM node:20-alpine AS build

WORKDIR /app

# Copy package descriptors and install dependencies
COPY app/frontend/package.json app/frontend/package-lock.json* ./
RUN npm ci --prefer-offline --no-audit

# Copy frontend source code and build production bundle
COPY app/frontend/ ./
RUN npm run build

# Production static serving stage via Nginx
FROM nginx:1.25-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY deployment/nginx/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
