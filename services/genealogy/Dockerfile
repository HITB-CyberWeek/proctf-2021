FROM gcc:11-bullseye
LABEL maintainer="andgein@hackerdom.ru"

RUN mkdir /app

ADD genealogy /app/genealogy

WORKDIR /app

RUN useradd -M -u 1000 genealogy

CMD /app/genealogy
