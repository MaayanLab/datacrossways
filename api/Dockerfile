FROM python:3.10.5-alpine3.16


RUN apk update
RUN apk add vim
RUN apk add curl
RUN apk add git

RUN git clone https://github.com/MaayanLab/apilock.git

RUN pip install -r /apilock/requirements.txt

