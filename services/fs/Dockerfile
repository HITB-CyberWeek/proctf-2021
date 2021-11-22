FROM archlinux

RUN pacman-db-upgrade
RUN pacman -Syyu --noconfirm
RUN pacman -S --noconfirm python3 python3-pip
RUN pip install	flask flask_login ujson pycryptodome
RUN pacman -S --noconfirm gunicorn

RUN useradd -M -u 1000 fs

WORKDIR /home/fs
CMD ./start.sh
