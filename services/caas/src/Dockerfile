FROM python:3-slim

RUN apt-get update && \
    apt-get install --no-install-recommends -y curl libpq-dev build-essential
RUN pip install grpcio grpcio-tools psycopg2 minio

WORKDIR /app
COPY . /app/

RUN python -m grpc_tools.protoc -I ./proto --python_out=. --grpc_python_out=. ./proto/caas.proto
