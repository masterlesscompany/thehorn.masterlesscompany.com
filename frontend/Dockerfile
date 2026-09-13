FROM node:24-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:24-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules node_modules
COPY . .
# 빌드에 환경변수를 주지 않는다. 모든 라우트가 요청 시점 렌더라 빌드가
# 백엔드를 부르지 않는다 — 더미 값을 넣어 두면 그 사실이 가려진다.
RUN npm run build

FROM node:24-slim
WORKDIR /app
ENV NODE_ENV=production PORT=3000
COPY --from=build /app/.next .next
COPY --from=build /app/node_modules node_modules
COPY --from=build /app/package.json ./
COPY --from=build /app/public public
EXPOSE 3000
CMD ["npm", "run", "start"]
