# docker-tor-hidden-service

[![Build Status](https://travis-ci.org/cmehay/docker-tor-hidden-service.svg?branch=master)](https://travis-ci.org/cmehay/docker-tor-hidden-service)

## Changelog

* 26 jul 2022
  * Update `onions` tool to v0.7.1:
    * Fix an issue when restarting a container with control port enabled
    * Updated to python 3.10
  * Fix a typo in `docker-compose.vanguards-network.yml`, it works now
  * Update `tor` to `0.4.7.8`

* 23 dec 2021
  * Update `onions` tool to v0.7.0:
    * Drop support of onion v2 adresses as tor network does not accept them anymore
  * Update `tor` to `0.4.6.9`

## Setup

### Setup hosts

From 2019, new conf to handle tor v3 address has been added. Here an example with `docker-compose` v2+:

```yaml
version: "2"

services:
  tor:
    image: goldy/tor-hidden-service:0.3.5.8
    links:
      - hello
      - world
      - again
    environment:

        # hello and again will share the same onion v3 address
        SERVICE1_TOR_SERVICE_HOSTS: 88:hello:80,8000:world:80
        # Optional as tor version 2 is not supported anymore
        SERVICE1_TOR_SERVICE_VERSION: '3'
        # tor v3 address private key base 64 encoded
        SERVICE1_TOR_SERVICE_KEY: |
            PT0gZWQyNTUxOXYxLXNlY3JldDogdHlwZTAgPT0AAACArobDQYyZAWXei4QZwr++
            j96H1X/gq14NwLRZ2O5DXuL0EzYKkdhZSILY85q+kfwZH8z4ceqe7u1F+0pQi/sM

  world:
    image: tutum/hello-world
    hostname: world

  hello:
    image: tutum/hello-world
    hostname: hello
```

This configuration will output:

```
service1: xwjtp3mj427zdp4tljiiivg2l5ijfvmt5lcsfaygtpp6cw254kykvpyd.onion:88, xwjtp3mj427zdp4tljiiivg2l5ijfvmt5lcsfaygtpp6cw254kykvpyd.onion:8000
```

`xwjtp3mj427zdp4tljiiivg2l5ijfvmt5lcsfaygtpp6cw254kykvpyd.onion:88` will hit `again:80`.
`xwjtp3mj427zdp4tljiiivg2l5ijfvmt5lcsfaygtpp6cw254kykvpyd.onion:8000` will hit `wold:80`.


#### Environment variables

##### `{SERVICE}_TOR_SERVICE_HOSTS`

The config patern for this variable is: `{exposed_port}:{hostname}:{port}}`

For example `80:hello:8080` will expose an onion service on port 80 to the port 8080 of hello hostname.

Unix sockets are supported too, `80:unix://path/to/socket.sock` will expose an onion service on port 80 to the socket `/path/to/socket.sock`. See `docker-compose.v2.socket.yml` for an example.

You can concatenate services using comas.

> **WARNING**: Using sockets and ports in the same service group can lead to issues

##### `{SERVICE}_TOR_SERVICE_VERSION`

Optionnal now, can only be `3`. Set the tor address type.

> **WARNING**: Version 2 is not supported anymore by tor network

`2` was giving short addresses `5azvyr7dvvr4cldn.onion` and `3` gives long addresses `xwjtp3mj427zdp4tljiiivg2l5ijfvmt5lcsfaygtpp6cw254kykvpyd.onion`


##### `{SERVICE}_TOR_SERVICE_KEY`

You can set the private key for the current service.

Tor v3 addresses uses ed25519 binary keys. It should be base64 encoded:
```
PT0gZWQyNTUxOXYxLXNlY3JldDogdHlwZTAgPT0AAACArobDQYyZAWXei4QZwr++j96H1X/gq14NwLRZ2O5DXuL0EzYKkdhZSILY85q+kfwZH8z4ceqe7u1F+0pQi/sM
```
##### `TOR_SOCKS_PORT`

Set tor sock5 proxy port for this tor instance. (Use this if you need to connect to tor network with your service)

##### `TOR_EXTRA_OPTIONS`

Add any options in the `torrc` file.

```yaml
services:
  tor:
    environment:
        # Add any option you need
        TOR_EXTRA_OPTIONS: |
          HiddenServiceNonAnonymousMode 1
          HiddenServiceSingleHopMode 1
```


#### Secrets

Secret key can be set through docker `secrets`, see `docker-compose.v3.yml` for example.


### Tools

A command line tool `onions` is available in container to get `.onion` url when container is running.

```sh
# Get services
$ docker exec -ti torhiddenproxy_tor_1 onions
hello: xwjtp3mj427zdp4tljiiivg2l5ijfvmt5lcsfaygtpp6cw254kykvpyd.onion:80
world: ootceq7skq7qpvvwf2tajeboxovalco7z3ka44vxbtfdr2tfvx5ld7ad.onion:80

# Get json
$ docker exec -ti torhiddenproxy_tor_1 onions --json
{"hello": ["xwjtp3mj427zdp4tljiiivg2l5ijfvmt5lcsfaygtpp6cw254kykvpyd.onion:80"], "world": ["ootceq7skq7qpvvwf2tajeboxovalco7z3ka44vxbtfdr2tfvx5ld7ad.onion:80"]}
```

### Auto reload

Changing `/etc/tor/torrc` file triggers a `SIGHUP` signal to `tor` to reload configuration.

To disable this behavior, add `ENTRYPOINT_DISABLE_RELOAD` in environment.

### Versions

Container version will follow tor release versions.

### pyentrypoint

This container uses [`pyentrypoint`](https://github.com/cmehay/pyentrypoint) to generate its setup.

### pytor

This containner uses [`pytor`](https://github.com/cmehay/pytor) to mannages tor cryptography, generate keys and compute onion urls.

## Control port

Use these environment variables to enable control port
* `TOR_CONTROL_PORT`: enable and set control port binding (`ip`, `ip:port` or `unix:/path/to/socket.sock`) (default port is 9051)
* `TOR_CONTROL_PASSWORD`: set control port password (in clear, not hashed)
* `TOR_DATA_DIRECTORY`: set data directory (default `/run/tor/data`)

## Vanguards

For critical hidden services, it's possible to increase security with [`Vanguards`](https://github.com/mikeperry-tor/vanguards) tool.


### Run in the same container

Check out [`docker-compose.vanguards.yml`](docker-compose.vanguards.yml) for example.

Add environment variable `TOR_ENABLE_VANGUARDS` to `true` to start `vanguards` daemon beside `tor` process. `Vanguards` logs will be displayed to stdout using `pyentrypoint` logging, if you need raw output, set `ENTRYPOINT_RAW` to `true` in environment.

In this mode, if `vanguards` exits, sigint is sent to `tor` process to terminate it. If you want to disable this behavior, set `VANGUARD_KILL_TOR_ON_EXIT` to `false` in environment.

### Run in separate containers
Check out[`docker-compose.vanguards-network.yml`](docker-compose.vanguards-network.yml) for an example of increased security setup using docker networks.

#### settings

Use the same environment variable as `tor` to configure `vangards` (see upper).
* `TOR_CONTROL_PORT`
* `TOR_CONTROL_PASSWORD`

##### more settings

Use `VANGUARDS_EXTRA_OPTIONS` environment variable to change any settings.

The following settings cannot me changer with this variable:
 - `control_ip`:
   - use `TOR_CONTROL_PORT`
 - `control_port`:
   - use `TOR_CONTROL_PORT`
 - `control_socket`:
   - use `TOR_CONTROL_PORT`
 - `control_pass`:
   - use `TOR_CONTROL_PASSWORD`
 - `state_file`:
   - use `VANGUARDS_STATE_FILE`
