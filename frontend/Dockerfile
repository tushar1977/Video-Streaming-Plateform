# =========================================
# Stage 1: Build the React Application
# =========================================

ARG NODE_VERSION=24.14.0-alpine
FROM node:${NODE_VERSION} AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

COPY . .

RUN npm run build


# =========================================
# Stage 2: Run the application
# =========================================

FROM node:${NODE_VERSION} AS runner

ENV NODE_ENV=development

WORKDIR /app

# Copy app and dependencies from builder
COPY --from=builder /app /app

# Fix permissions
RUN chown -R node:node /app

USER node

EXPOSE 3001

CMD ["npm", "start"]
