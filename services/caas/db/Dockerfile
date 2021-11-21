FROM postgres:14

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    apt-get clean

RUN curl https://dl.min.io/client/mc/release/linux-amd64/mc > /usr/local/bin/mc && \
    chmod +x /usr/local/bin/mc

COPY archive.sh /opt/archive.sh
COPY postgresql.conf /opt/postgresql.conf
