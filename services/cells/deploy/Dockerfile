FROM archlinux

RUN pacman-db-upgrade
RUN pacman -Syyu --noconfirm
RUN pacman -S --noconfirm python3 python-flask
RUN pacman -S --noconfirm gunicorn

RUN useradd cells

EXPOSE 5000/tcp
WORKDIR /home/service
CMD ["sh","-c","chmod +x cells.elf; chmod 0777 data; chmod a+r static; chmod a+r templates; ./start.sh"]
