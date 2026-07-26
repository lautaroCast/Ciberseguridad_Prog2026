# Frontend — React + TypeScript dashboard (Módulo 8). Vite bakes
# VITE_* env vars into the static bundle at build time, not runtime, so
# VITE_API_BASE_URL arrives as a build ARG (see docker-compose.yml's
# `build.args`), never as a container-run env var.
FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
