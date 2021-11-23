FROM gcc:11-bullseye
LABEL maintainer="andgein@hackerdom.ru"

RUN mkdir /app
RUN mkdir /app/keys

ADD genealogy /app/genealogy
ADD src/static/ /app/static/

WORKDIR /app

RUN useradd -M -u 1000 genealogy
RUN chown -R genealogy:genealogy /app

USER genealogy

CMD /app/genealogy
