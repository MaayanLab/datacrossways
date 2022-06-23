FROM node:18-alpine3.15

RUN apk update && apk add vim curl git

RUN git clone https://github.com/MaayanLab/nextjatest.git

WORKDIR /nextjatest/test
RUN npm install

EXPOSE 3000

CMD ["npm", "run", "dev"]
