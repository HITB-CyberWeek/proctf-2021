WORKDIR /app

RUN pacman-db-upgrade && \
    pacman -Syyu --noconfirm && \
    pacman -S --noconfirm gcc-fortran curl && \
    curl -sL https://github.com/fortran-lang/fpm/releases/download/v0.4.0/fpm-0.4.0-linux-x86_64 -o /tmp/fpm && \
    mv /tmp/fpm /usr/bin/fpm && \
    chmod +x /usr/bin/fpm

COPY ./src/ /app/

RUN /usr/bin/fpm install --profile release --prefix /app && mkdir -p /app/db
VOLUME /app/db

CMD ["./bin/forvolution"]
