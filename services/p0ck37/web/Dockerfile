FROM node:latest

WORKDIR /app
COPY ./package.json ./
RUN npm install

COPY ./views/ ./views/
COPY ./app.js ./

RUN adduser --system --uid=31337 --disabled-password --disabled-login --gecos '' p0ck37
RUN mkdir /data && chown -R p0ck37 /data
VOLUME /data

USER p0ck37
EXPOSE 3000

CMD ["node", "app.js"]
