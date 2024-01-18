FROM alpine:3.19 AS build
RUN apk add --no-cache nodejs
RUN apk add --no-cache npm
RUN apk add --no-cache make
RUN apk add --no-cache g++
RUN apk add --no-cache cmake
RUN apk add --no-cache python3
WORKDIR /app/build
COPY package.json .
RUN npm install
COPY index.ts .
COPY tsconfig.json .
COPY utilities/ utilities/.
COPY types/ types/.
COPY modules/ modules/.
COPY data/ data/.
RUN npx tsc

FROM alpine:3.19 AS runtime
RUN apk add --no-cache nodejs npm
RUN apk add --no-cache make
RUN apk add --no-cache g++
RUN apk add --no-cache cmake
RUN apk add --no-cache python3
WORKDIR /app/runtime
COPY --from=build /app/build/package.json .
RUN npm install --omit=dev
COPY --from=build /app/build/dist .
ENTRYPOINT [ "/bin/sh" ]