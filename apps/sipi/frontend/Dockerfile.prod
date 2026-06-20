# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Instalar versión EXACTA de pnpm (no latest)
RUN corepack enable && corepack prepare pnpm@8.15.0 --activate

# Copiar package files (ahora sí existe lockfile)
COPY package*.json pnpm-lock.yaml ./

# Instalar dependencias (SIEMPRE reproducible)
RUN pnpm install --frozen-lockfile

# Copiar código y build
COPY . .
RUN pnpm build

# Nginx stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]