# ---- Build Stage ----
FROM node:23-alpine AS build

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .
RUN npm run build

# ---- Serve Stage ----
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Forward VITE_* env vars to the nginx-served app at runtime
# The nginx entrypoint script handles this for VITE_ prefixed vars
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]