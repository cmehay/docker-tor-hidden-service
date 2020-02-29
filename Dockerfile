FROM    alpine

ENV     HOME /var/lib/tor

RUN     apk add --no-cache git libevent-dev openssl-dev gcc make automake ca-certificates autoconf musl-dev coreutils zlib zlib-dev && \
        mkdir -p /usr/local/src/ && \
        git clone https://git.torproject.org/tor.git /usr/local/src/tor && \
        cd /usr/local/src/tor && \
        git checkout $(git branch -a | grep 'release' | sort -V | tail -1) && \
        head ReleaseNotes | grep version | awk -F"version" '{print $2}' | grep - | awk '{ print $1 }' > /version && \
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
        pip3 install --upgrade pip setuptools pycrypto && \
        apk del git libevent-dev openssl-dev make automake python3-dev gcc autoconf musl-dev coreutils && \
        apk add --no-cache libevent openssl

RUN     mkdir -p /etc/tor/

ADD     assets/entrypoint-config.yml /
ADD     assets/onions /usr/local/src/onions
ADD     assets/torrc /var/local/tor/torrc.tpl
ADD     assets/v3onions /usr/bin/v3onions

RUN     chmod +x /usr/bin/v3onions
RUN     cd /usr/local/src/onions && python3 setup.py install

RUN     mkdir -p ${HOME}/.tor && \
        addgroup -S -g 107 tor && \
        adduser -S -G tor -u 104 -H -h ${HOME} tor

VOLUME  ["/var/lib/tor/hidden_service/"]

ENTRYPOINT ["pyentrypoint"]

CMD     ["tor"]
