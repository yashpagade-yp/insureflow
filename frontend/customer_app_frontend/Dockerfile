FROM node:20-alpine AS build

WORKDIR /app

ARG VITE_MAIN_API_BASE_URL=http://localhost:8000
ENV VITE_MAIN_API_BASE_URL=$VITE_MAIN_API_BASE_URL
ARG VITE_BOT_BASE_URL=http://localhost:8002
ENV VITE_BOT_BASE_URL=$VITE_BOT_BASE_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
