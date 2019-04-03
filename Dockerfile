FROM    alpine:latest
ARG     tor_version

ENV     HOME /var/lib/tor

RUN     apk add --no-cache git libevent-dev openssl-dev gcc make automake ca-certificates autoconf musl-dev coreutils zlib-dev && \
    mkdir -p /usr/local/src/ && \
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
    apk add --no-cache python3 python3-dev && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    apk del git libevent-dev openssl-dev make automake python3-dev autoconf musl-dev coreutils && \
    apk add --no-cache libevent openssl

RUN     mkdir -p /etc/tor/

COPY    assets/onions /usr/local/src/onions
COPY    assets/torrc /var/local/tor/torrc.tpl


RUN     cd /usr/local/src/onions && apk add --no-cache openssl-dev libffi-dev gcc python3-dev libc-dev && \
    python3 setup.py install && \
    apk del libffi-dev gcc python3-dev libc-dev openssl-dev

RUN     mkdir -p ${HOME}/.tor && \
    addgroup -S -g 107 tor && \
    adduser -S -G tor -u 104 -H -h ${HOME} tor

COPY    assets/entrypoint-config.yml /

VOLUME  ["/var/lib/tor/hidden_service/"]

ENTRYPOINT ["pyentrypoint"]

CMD     ["tor"]
