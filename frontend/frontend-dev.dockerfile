FROM node:12.19.0-alpine
RUN apk add python make gcc g++
RUN yarn global add @vue/cli
