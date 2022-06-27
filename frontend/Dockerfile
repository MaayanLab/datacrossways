FROM node:18-alpine3.15

RUN apk update && apk add vim curl git

RUN git clone https://github.com/MaayanLab/datacrossways_frontend.git

WORKDIR /datacrossways_frontend
RUN npm install --legacy-peer-deps

EXPOSE 3000

RUN npm run build

CMD ["npm", "run", "start"]
