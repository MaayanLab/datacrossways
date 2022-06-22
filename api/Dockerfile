FROM python:3.10.5-alpine3.16

RUN apk update && apk add vim curl git


RUN apk add python3-dev \
        gcc \
        libc-dev

RUN git clone https://github.com/MaayanLab/apilock.git

RUN pip install --upgrade pip
RUN pip install -r /apilock/requirements.txt

