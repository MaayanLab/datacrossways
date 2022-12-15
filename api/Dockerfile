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

RUN git reset --hard
RUN git clone https://github.com/MaayanLab/datacrossways_api.git

WORKDIR /app
RUN cp -a /datacrossways_api/. /app/
RUN rm -r /datacrossways_api

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

EXPOSE 5000

RUN chmod -R 777 /app
ENTRYPOINT FLASK_APP=/app/app.py flask run --host=0.0.0.0 --port 5000
