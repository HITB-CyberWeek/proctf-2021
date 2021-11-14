FROM gcc:11-bullseye

ADD . /app

WORKDIR /app

RUN make -j4

# REMOVE
RUN mkdir /app/keys
RUN apt-get update
RUN apt-get install -y gdb
RUN wget -q -O- https://github.com/hugsy/gef/raw/master/scripts/gef.sh | sh

CMD /app/main
