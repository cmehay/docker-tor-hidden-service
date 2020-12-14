#!/bin/bash
git ls-remote --tags https://git.torproject.org/tor.git | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1
