FROM    python:3.8-alpine
ARG     tor_version

ENV     HOME /var/lib/tor
ENV     POETRY_VIRTUALENVS_CREATE=false

RUN     apk add --no-cache git bind-tools libevent-dev openssl-dev gnupg gcc make automake ca-certificates autoconf musl-dev coreutils libffi-dev zlib-dev && \
    mkdir -p /usr/local/src/ /var/lib/tor/ && \
    git clone https://git.torproject.org/tor.git /usr/local/src/tor && \
    cd /usr/local/src/tor && \
    git checkout tor-$tor_version && \
    ./autogen.sh && \
    ./configure \
    --disable-asciidoc \
    --sysconfdir=/etc \
    --disable-unittests && \
    make && make install && \
    cd .. && \
    rm -rf tor && \
    pip3 install --upgrade pip poetry && \
    apk del git libevent-dev openssl-dev gnupg make automake autoconf musl-dev coreutils libffi-dev && \
    apk add --no-cache libevent openssl

RUN     mkdir -p /etc/tor/

COPY    pyproject.toml /usr/local/src/onions/

RUN     cd /usr/local/src/onions && apk add --no-cache openssl-dev libffi-dev gcc libc-dev && \
    poetry install --no-dev --no-root && \
    apk del libffi-dev gcc libc-dev openssl-dev

COPY    onions /usr/local/src/onions/onions
COPY    poetry.lock /usr/local/src/onions/
RUN     cd /usr/local/src/onions && poetry install --no-dev

RUN     mkdir -p ${HOME}/.tor && \
    addgroup -S -g 107 tor && \
    adduser -S -G tor -u 104 -H -h ${HOME} tor

COPY    assets/entrypoint-config.yml /
COPY    assets/torrc /var/local/tor/torrc.tpl
COPY    assets/vanguards.conf.tpl /var/local/tor/vanguards.conf.tpl

ENV     VANGUARDS_CONFIG /etc/tor/vanguards.conf

VOLUME  ["/var/lib/tor/hidden_service/"]

ENTRYPOINT ["pyentrypoint"]

CMD     ["tor"]
