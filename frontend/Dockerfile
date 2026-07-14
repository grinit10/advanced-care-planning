# ---- Build Stage ----
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .
RUN npm run build

# ---- Serve Stage ----
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# NOTE: VITE_* environment variables are baked into the JS bundle at build time.
# To change API URLs for different environments, rebuild the image with
# different VITE_* values, or use a runtime config injection strategy.
# See: https://vite.dev/guide/env-and-mode
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]