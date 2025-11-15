# frontend/Dockerfile

#######################
# FÁZE 1: Build (Builder)
#######################
FROM node:20 AS builder

WORKDIR /app

# Využití cache - instalujeme závislosti jen při změně package.json
COPY package.json package-lock.json* ./
RUN npm install

# Kopírování zbytku kódu a build
COPY . .
RUN npm run build

#######################
# FÁZE 2: Produkce (Prod)
#######################
FROM nginx:1.25-alpine

# Kopírování build assetů z "builder" fáze
# Předpokládáme, že adapter-static ukládá build do adresáře 'build'
COPY --from=builder /app/build /usr/share/nginx/html

# Kopírování vlastní Nginx konfigurace (viz níže)
# Tato konfigurace je klíčová pro SvelteKit routing!
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]