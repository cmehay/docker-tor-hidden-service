#!/bin/bash

set -e

if [ "${1:0:1}" == '-' ]; then
  set -- tor $@
fi

if [ "$1" == "tor" ]; then
  # Set config
  python3 ./tor_config.py

  # set rights on keys
  chown -R debian-tor:debian-tor /var/lib/tor/hidden_service/
  chmod -R 700 /var/lib/tor/hidden_service/

  # Switch user

  set -- su debian-tor -s /bin/sh -c "$@"
fi

exec "$@"
