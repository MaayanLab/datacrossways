FROM node:18.13.0-alpine3.17 as builder

ARG BASE_URL

RUN apk update && apk add vim curl git sed


WORKDIR /
RUN git clone https://github.com/MaayanLab/ihdh_frontend.git

WORKDIR /ihdh_frontend
RUN sed -i "s|BASE_URL|$BASE_URL|g" /ihdh_frontend/src/data/config.json
RUN sed -i "s|BASE_URL|$BASE_URL|g" /ihdh_frontend/.env

RUN npm install --legacy-peer-deps

RUN npm run build

FROM nginx
COPY --from=builder /ihdh_frontend/build /usr/share/nginx/html
RUN rm /etc/nginx/conf.d/default.conf  # <= This line solved my issue
COPY nginx.conf /etc/nginx/conf.d
EXPOSE 80