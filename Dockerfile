FROM alpine:3.19 AS build
RUN apk update
RUN apk add nodejs
RUN apk add npm
RUN apk add make
RUN apk add g++
RUN apk add cmake
RUN apk add python3
RUN apk cache clean
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
RUN apk update
RUN apk add nodejs npm
RUN apk add make
RUN apk add g++
RUN apk add cmake
RUN apk add python3
RUN apk cache clean
WORKDIR /app/runtime
COPY --from=build /app/build/package.json .
RUN npm install --omit=dev
RUN apk del g++
RUN apk del cmake
RUN apk del python3
RUN apk del make
COPY --from=build /app/build/dist .
ENTRYPOINT [ "/bin/sh" ]