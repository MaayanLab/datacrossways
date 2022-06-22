FROM python:3.8.0-alpine3.16

RUN apk update && apk add vim curl git


RUN apk --no-cache add python3-dev \
        gcc \
        libc-dev \
        libffi-dev \
        openssl-dev \
        musl-dev

RUN pip install --upgrade pip
RUN pip install install cffi

RUN git clone https://github.com/MaayanLab/apilock.git

RUN pip install -r /apilock/requirements.txt
