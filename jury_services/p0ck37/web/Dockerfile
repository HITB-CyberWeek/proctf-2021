FROM node:latest

RUN for n in RFCs4001-4500.zip RFCs4501-5000.zip RFCs5001-5500.zip RFCs5501-6000.zip RFCs6001-6500.zip RFCs6501-7000.zip RFCs7001-7500.zip RFCs7501-8000.zip RFCs8001-8500.zip; do \
      wget https://www.rfc-editor.org/in-notes/tar/$n --directory-prefix /var/rfcs && \
      unzip /var/rfcs/$n -d /var/rfcs && \
      rm /var/rfcs/$n; done && \
    rm /var/rfcs/*.pdf

WORKDIR /var/www

COPY ./package.json ./
RUN npm install

COPY ./*.js ./
COPY ./favicon.ico ./

EXPOSE 8080

CMD ["node", "app.js"]
