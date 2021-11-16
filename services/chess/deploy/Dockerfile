FROM ubuntu@sha256:26cd4ff32a9c031eaca3d6f589a7799f28b34a539e1bd81acbf1a6efeec4b1ce
LABEL maintainer="bay@hackerdom.ru"

RUN apt-get update && apt-get install -y socat
RUN useradd -M -u 1000 chess

WORKDIR /home/chess/
CMD ./start.sh
