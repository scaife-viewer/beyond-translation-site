FROM node:12.19.0-alpine

RUN apk add python make gcc g++
RUN yarn global add @vue/cli

WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install

COPY . .
RUN yarn build
