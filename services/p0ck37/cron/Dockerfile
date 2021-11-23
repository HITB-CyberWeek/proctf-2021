FROM debian:latest

RUN apt-get -y update \
  && apt-get install -y cron \
  && rm -rf /var/lib/apt/lists/*

COPY p0ck37.cron /etc/cron.d/p0ck37
RUN chmod 0644 /etc/cron.d/p0ck37
RUN crontab /etc/cron.d/p0ck37

RUN mkdir /data
VOLUME /data

ENTRYPOINT ["cron", "-f"]
