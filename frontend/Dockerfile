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
FROM node:20-alpine

WORKDIR /app

COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000

ENV NODE_ENV=production
ENV ORIGIN=http://localhost

CMD ["node", "build"]