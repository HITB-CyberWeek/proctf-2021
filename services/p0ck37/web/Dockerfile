FROM node:latest

WORKDIR /app
COPY ./package.json ./
RUN npm install

COPY ./views/ ./views/
COPY ./app.js ./

ADD server.crt /usr/local/share/ca-certificates/oauth.crt
RUN chmod 644 /usr/local/share/ca-certificates/oauth.crt && update-ca-certificates
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/oauth.crt

RUN adduser --system --uid=31337 --disabled-password --disabled-login --gecos '' p0ck37
RUN mkdir /data && chown -R p0ck37 /data
VOLUME /data

USER p0ck37
EXPOSE 3000

CMD ["node", "app.js"]
