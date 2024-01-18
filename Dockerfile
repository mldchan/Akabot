FROM alpine:3.19 AS build
RUN apk update
RUN apk add nodejs npm make g++ cmake python3 yarn
RUN apk cache clean
WORKDIR /app/build
COPY package.json .
RUN yarn install
COPY index.ts .
COPY tsconfig.json .
COPY utilities/ utilities/.
COPY types/ types/.
COPY modules/ modules/.
COPY data/ data/.
RUN npx tsc
RUN cp package.json dist/package.json
WORKDIR /app/build/dist
RUN yarn install --omit=dev

FROM alpine:3.19 AS runtime
WORKDIR /app/runtime
RUN apk add --no-cache nodejs
COPY --from=build /app/build/dist .
ENTRYPOINT [ "node", "index.js" ]