FROM node:18.13.0-alpine3.17 as builder

RUN apk update && apk add vim curl git


WORKDIR /
RUN git clone https://github.com/MaayanLab/datacrossways_frontend.git

WORKDIR /datacrossways_frontend

RUN npm install --legacy-peer-deps

RUN npm run build

FROM nginx
COPY --from=builder /datacrossways_frontend/build /usr/share/nginx/html
RUN rm /etc/nginx/conf.d/default.conf  # <= This line solved my issue
COPY nginx.conf /etc/nginx/conf.d
EXPOSE 80