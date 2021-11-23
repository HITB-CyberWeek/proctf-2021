FROM python:3.8.10-slim

RUN echo "deb http://deb.debian.org/debian buster-backports main" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install --no-install-recommends -y -t buster-backports curl libpq-dev build-essential
RUN pip install grpcio grpcio-tools psycopg2 minio

WORKDIR /app
COPY . /app/

RUN python -m grpc_tools.protoc -I ./proto --python_out=. --grpc_python_out=. ./proto/caas.proto
