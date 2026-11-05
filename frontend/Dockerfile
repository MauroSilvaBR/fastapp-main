FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app ./

EXPOSE 3000
CMD ["sh", "-c", "npm run start -- -p ${PORT:-3000}"]

