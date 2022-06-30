FROM python:3.10.5-alpine3.16

RUN apk update && apk add vim curl git

RUN apk --no-cache add python3-dev \
        gcc \
        libc-dev \
        libffi-dev \
        openssl-dev \
        musl-dev

RUN pip install --upgrade pip
RUN pip install install cffi

RUN git clone https://github.com/MaayanLab/datacrossways_api.git

RUN pip install -r /datacrossways_api/requirements.txt

EXPOSE 5000
WORKDIR /apilock

RUN chmod -R 777 /datacrossways_api
ENTRYPOINT FLASK_APP=/datacrossways_api/app.py flask run --host=0.0.0.0 --port 5000

