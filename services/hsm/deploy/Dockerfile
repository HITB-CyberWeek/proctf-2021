FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends    \
        qemu-system-misc=1:4.2-3ubuntu6.18        \
        python3.8=3.8.10-0ubuntu1~20.04.1         \
        python3.8-venv=3.8.10-0ubuntu1~20.04.1    \
                                               && \
    apt-get clean

WORKDIR /hsm

COPY requirements.txt   ./

RUN python3.8 -m venv venv
RUN venv/bin/python3.8 -m pip install -r requirements.txt

COPY firmware.exe       ./
COPY server.py          ./
COPY slot.py            ./
COPY users.py           ./

CMD venv/bin/python3 ./server.py --host 0.0.0.0
