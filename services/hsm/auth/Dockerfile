FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends    \
        python3.8=3.8.10-0ubuntu1~20.04.1         \
        python3.8-dev=3.8.10-0ubuntu1~20.04.1     \
        build-essential                           \
        python3.8-venv=3.8.10-0ubuntu1~20.04.1    \
                                               && \
    apt-get clean

WORKDIR /app

RUN python3.8 -m venv venv

COPY requirements.txt   ./
RUN venv/bin/python3.8 -m pip install -r requirements.txt

COPY tokens.txt         ./
COPY auth.py            ./

CMD venv/bin/python3 ./auth.py
