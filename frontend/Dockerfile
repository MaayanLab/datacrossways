FROM node:18.13.0-alpine3.17 as builder

ARG BASE_URL

RUN apk update && apk add vim curl git sed


WORKDIR /
RUN git clone -b main https://github.com/MaayanLab/ihdh_frontend.git
WORKDIR /app
RUN cp -a /ihdh_frontend/. /app/
RUN rm -r /ihdh_frontend

RUN sed -i "s|BASE_URL|$BASE_URL|g" /app/src/data/config.json
RUN sed -i "s|BASE_URL|$BASE_URL|g" /app/.env

RUN npm install --legacy-peer-deps

RUN npm run build

FROM nginx
COPY --from=builder /app/build /usr/share/nginx/html
RUN rm /etc/nginx/conf.d/default.conf  # <= This line solved my issue
COPY nginx.conf /etc/nginx/conf.d
EXPOSE 80