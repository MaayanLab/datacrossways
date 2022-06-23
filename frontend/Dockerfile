FROM node:17-alpine3.15

RUN apk update && apk add vim curl git

RUN git clone https://github.com/MaayanLab/nextjatest.git

RUN npm install -g npm@8.13.0

WORKDIR /nextjatest/test
RUN npm install --legacy-peer-deps

EXPOSE 3000

CMD ["npm", "run", "dev"]
