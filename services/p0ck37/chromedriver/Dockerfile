FROM debian:latest

RUN  apt-get update \
  && apt-get install -y wget gnupg2 curl unzip xvfb cron psmisc

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update \
  && apt-get install -y google-chrome-stable \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp
RUN wget -O chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip chromedriver.zip chromedriver -d /usr/local/bin/ && rm chromedriver.zip

COPY wrapper /usr/local/bin/
COPY start.sh /usr/local/bin/

RUN adduser --system --uid=31337 --disabled-password --disabled-login --gecos '' chromedriver

RUN mkdir /data && chown -R chromedriver /data
VOLUME /data

COPY chrome.cron /etc/cron.d/chrome
RUN chmod 0644 /etc/cron.d/chrome
RUN crontab /etc/cron.d/chrome

EXPOSE 4444

ENTRYPOINT ["/usr/local/bin/start.sh"]
