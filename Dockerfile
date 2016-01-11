FROM  debian:jessie

ENV DEBIAN_FRONTEND=noninteractive

RUN   apt-get update && apt-get install -y \
        tor \
        python3 \
        git \
        ca-certificates

ADD   assets/docker-entrypoint.sh /
ADD   assets/tor_config.py /

RUN   chmod +x /docker-entrypoint.sh

RUN   git clone https://github.com/cmehay/python-docker-tool.git /docker --branch=old
RUN   touch /docker/__init__.py

VOLUME  ["/var/lib/tor/hidden_service/"]

ENTRYPOINT ["/docker-entrypoint.sh"]

CMD   ["tor"]
