FROM  debian:jessie

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME /var/lib/tor

RUN   apt-get update && apt-get install --no-install-recommends -y \
        tor \
        python3-pip

RUN   pip3 install pyentrypoint==0.2.1

ADD   assets/entrypoint-config.yml /
ADD   assets/display_onions.py /
ADD   assets/torrc /etc/tor/torrc

VOLUME  ["/var/lib/tor/hidden_service/"]

ENTRYPOINT ["pyentrypoint"]

CMD   ["tor"]
