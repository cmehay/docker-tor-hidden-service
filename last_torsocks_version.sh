#!/bin/sh
git ls-remote --tags https://git.torproject.org/torsocks.git | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1
