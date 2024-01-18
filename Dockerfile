FROM alpine:3.19 AS build
RUN apk add nodejs
RUN apk add npm
RUN apk add yarn
RUN apk cache clean
WORKDIR /app/build
COPY package.json .
COPY index.ts .
COPY tsconfig.json .
COPY utilities/ .
COPY types/ .
COPY modules/ .
COPY data/ .
RUN yarn install
RUN npx tsc
# The build should be located under /app/build/dist
RUN ls -l /app/build/dist