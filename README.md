# docker-tor-hidden-service

[![Build Status](https://travis-ci.org/cmehay/docker-tor-hidden-service.svg?branch=master)](https://travis-ci.org/cmehay/docker-tor-hidden-service)

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
        # Set mapping ports
        SERVICE1_TOR_SERVICE_HOSTS: 80:hello:80,800:hello:80,8888:hello:80
        # Set private key
        SERVICE1_TOR_SERVICE_KEY: |
            -----BEGIN RSA PRIVATE KEY-----
            MIICXQIBAAKBgQDR8TdQF9fDlGhy1SMgfhMBi9TaFeD12/FK27TZE/tYGhxXvs1C
            NmFJy1hjVxspF5unmUsCk0yEsvEdcAdp17Vynz6W41VdinETU9yXHlUJ6NyI32AH
            dnFnHEcsllSEqD1hPAAvMUWwSMJaNmBEFtl8DUMS9tPX5fWGX4w5Xx8dZwIDAQAB
            AoGBAMb20jMHxaZHWg2qTRYYJa8LdHgS0BZxkWYefnBUbZn7dOz7mM+tddpX6raK
            8OSqyQu3Tc1tB9GjPLtnVr9KfVwhUVM7YXC/wOZo+u72bv9+4OMrEK/R8xy30XWj
            GePXEu95yArE4NucYphxBLWMMu2E4RodjyJpczsl0Lohcn4BAkEA+XPaEKnNA3AL
            1DXRpSpaa0ukGUY/zM7HNUFMW3UP00nxNCpWLSBmrQ56Suy7iSy91oa6HWkDD/4C
            k0HslnMW5wJBANdz4ehByMJZmJu/b5y8wnFSqep2jmJ1InMvd18BfVoBTQJwGMAr
            +qwSwNXXK2YYl9VJmCPCfgN0o7h1AEzvdYECQAM5UxUqDKNBvHVmqKn4zShb1ugY
            t1RfS8XNbT41WhoB96MT9P8qTwlniX8UZiwUrvNp1Ffy9n4raz8Z+APNwvsCQQC9
            AuaOsReEmMFu8VTjNh2G+TQjgvqKmaQtVNjuOgpUKYv7tYehH3P7/T+62dcy7CRX
            cwbLaFbQhUUUD2DCHdkBAkB6CbB+qhu67oE4nnBCXllI9EXktXgFyXv/cScNvM9Y
            FDzzNAAfVc5Nmbmx28Nw+0w6pnpe/3m0Tudbq3nHdHfQ
            -----END RSA PRIVATE KEY-----

        # hello and again will share the same onion v3 address
        SERVICE2_TOR_SERVICE_HOSTS: 88:again:80,8000:world:80
        SERVICE2_TOR_SERVICE_VERSION: '3'
        # tor v3 address private key base 64 encoded
        SERVICE2_TOR_SERVICE_KEY: |
            PT0gZWQyNTUxOXYxLXNlY3JldDogdHlwZTAgPT0AAACArobDQYyZAWXei4QZwr++
            j96H1X/gq14NwLRZ2O5DXuL0EzYKkdhZSILY85q+kfwZH8z4ceqe7u1F+0pQi/sM

  hello:
    image: tutum/hello-world
    hostname: hello

  world:
    image: tutum/hello-world
    hostname: world

  again:
    image: tutum/hello-world
    hostname: again
```

This configuration will output:

```
service2: xwjtp3mj427zdp4tljiiivg2l5ijfvmt5lcsfaygtpp6cw254kykvpyd.onion:88, xwjtp3mj427zdp4tljiiivg2l5ijfvmt5lcsfaygtpp6cw254kykvpyd.onion:8000
service1: 5azvyr7dvvr4cldn.onion:80, 5azvyr7dvvr4cldn.onion:800, 5azvyr7dvvr4cldn.onion:8888
```

`xwjtp3mj427zdp4tljiiivg2l5ijfvmt5lcsfaygtpp6cw254kykvpyd.onion:88` will hit `again:80`.
`xwjtp3mj427zdp4tljiiivg2l5ijfvmt5lcsfaygtpp6cw254kykvpyd.onion:8000` will hit `wold:80`.

`5azvyr7dvvr4cldn.onion:80` will hit `hello:80`.
`5azvyr7dvvr4cldn.onion:800` will hit `hello:80` too.
`5azvyr7dvvr4cldn.onion:8888` will hit `hello:80` again.

#### Environment variables

##### `{SERVICE}_TOR_SERVICE_HOSTS`

The config patern for this variable is: `{exposed_port}:{hostname}:{port}}`

For example `80:hello:8080` will expose an onion service on port 80 to the port 8080 of hello hostname.

Unix sockets are supported too, `80:unix://path/to/socket.sock` will expose an onion service on port 80 to the socket `/path/to/socket.sock`. See `docker-compose.v2.socket.yml` for an example.

You can concatenate services using comas.

> **WARNING**: Using sockets and ports in the same service group can lead to issues

##### `{SERVICE}_TOR_SERVICE_VERSION`

Can be `2` or `3`. Set the tor address type.

`2` gives short addresses `5azvyr7dvvr4cldn.onion` and `3` long addresses `xwjtp3mj427zdp4tljiiivg2l5ijfvmt5lcsfaygtpp6cw254kykvpyd.onion`


##### `{SERVICE}_TOR_SERVICE_KEY`

You can set the private key for the current service.

Tor v2 addresses uses RSA PEM keys like:
```
-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQDR8TdQF9fDlGhy1SMgfhMBi9TaFeD12/FK27TZE/tYGhxXvs1C
NmFJy1hjVxspF5unmUsCk0yEsvEdcAdp17Vynz6W41VdinETU9yXHlUJ6NyI32AH
dnFnHEcsllSEqD1hPAAvMUWwSMJaNmBEFtl8DUMS9tPX5fWGX4w5Xx8dZwIDAQAB
AoGBAMb20jMHxaZHWg2qTRYYJa8LdHgS0BZxkWYefnBUbZn7dOz7mM+tddpX6raK
8OSqyQu3Tc1tB9GjPLtnVr9KfVwhUVM7YXC/wOZo+u72bv9+4OMrEK/R8xy30XWj
GePXEu95yArE4NucYphxBLWMMu2E4RodjyJpczsl0Lohcn4BAkEA+XPaEKnNA3AL
1DXRpSpaa0ukGUY/zM7HNUFMW3UP00nxNCpWLSBmrQ56Suy7iSy91oa6HWkDD/4C
k0HslnMW5wJBANdz4ehByMJZmJu/b5y8wnFSqep2jmJ1InMvd18BfVoBTQJwGMAr
+qwSwNXXK2YYl9VJmCPCfgN0o7h1AEzvdYECQAM5UxUqDKNBvHVmqKn4zShb1ugY
t1RfS8XNbT41WhoB96MT9P8qTwlniX8UZiwUrvNp1Ffy9n4raz8Z+APNwvsCQQC9
AuaOsReEmMFu8VTjNh2G+TQjgvqKmaQtVNjuOgpUKYv7tYehH3P7/T+62dcy7CRX
cwbLaFbQhUUUD2DCHdkBAkB6CbB+qhu67oE4nnBCXllI9EXktXgFyXv/cScNvM9Y
FDzzNAAfVc5Nmbmx28Nw+0w6pnpe/3m0Tudbq3nHdHfQ
-----END RSA PRIVATE KEY-----
```

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
hello: vegm3d7q64gutl75.onion:80
world: b2sflntvdne63amj.onion:80

# Get json
$ docker exec -ti torhiddenproxy_tor_1 onions --json
{"hello": ["b2sflntvdne63amj.onion:80"], "world": ["vegm3d7q64gutl75.onion:80"]}
```

### Auto reload

Changing `/etc/tor/torrc` file triggers a `SIGHUP` signal to `tor` to reload configuration.

To disable this behavior, add `ENTRYPOINT_DISABLE_RELOAD` in environment.

### Versions

Container version will follow tor release versions.

### pyentrypoint

This container uses [`pyentrypoint`](https://github.com/cmehay/pyentrypoint) to generate its setup.

If you need to use the legacy version, please checkout the `legacy` branch or pull `goldy/tor-hidden-service:legacy`.

### pytor

This containner uses [`pytor`](https://github.com/cmehay/pytor) to mannages tor cryptography, generate keys and compute onion urls.

## Control port

Use these environment variables to enable control port
* `TOR_CONTROL_PORT`: enable and set control port binding (`ip`, `ip:port` or `unix:/path/to/socket.sock`) (default port is 9051)
* `TOR_CONTROL_PASSWORD`: set control port password (in clear, not hashed)
* `TOR_DATA_DIRECTORY`: set data directory (default `/run/tor/data`)

## Vanguards

For critical hidden services, it's possible to increase security with [`Vanguards`](https://github.com/mikeperry-tor/vanguards) tool.

#### Settings

It's not possible yet to custom all the settings using environment variable, but it's possible to mount configuration file to `/etc/tor/vanguards.conf` to custom `vanguards` settings.

### Run in the same container

Check out [`docker-compose.vanguards.yml`](docker-compose.vanguads.yml) for example.

Add environment variable `TOR_ENABLE_VANGUARDS` to `true` to start `vanguards` daemon beside `tor` process. `Vanguards` logs will be displayed to stdout using `pyentrypoint` logging, if you need raw output, set `ENTRYPOINT_RAW` to `true` in environment.

In this mode, if `vanguards` exits, sigint is sent to `tor` process to terminate it. If you want to disable this behavior, set `VANGUARD_KILL_TOR_ON_EXIT` to `false` in environment.

### Run in separate containers
Check out[`docker-compose.vanguards-network.yml`](docker-compose.vanguards-network.yml) for an example of increased security setup using docker networks.

#### settings

Use the same environment variable as `tor` to configure `vangards` (see upper).
* `TOR_CONTROL_PORT`
* `TOR_CONTROL_PASSWORD`

# Legacy deprecated doc

> **WARNING**: ALL THE DOC BELLOW IS LEGACY, IT'S STILL WORKING BUT IT'S NOT RECOMMENDED ANYMORE AND COULD BE DROPPED IN FUTURE RELEASES.

### Create a tor hidden service with a link

```sh
# run a container with a network application
$ docker run -d --name hello_world tutum/hello-world

# and just link it to this container
$ docker run -ti --link hello_world goldy/tor-hidden-service
```

The .onion URLs are displayed to stdout at startup.

To keep onion keys, just mount volume `/var/lib/tor/hidden_service/`

```sh
$ docker run -ti --link something --volume /path/to/keys:/var/lib/tor/hidden_service/ goldy/tor-hidden-service
```

Look at the `docker-compose.yml` file to see how to use it.

### Set private key

Private key is settable by environment or by copying file in `hostname/private_key` in docker volume (`hostname` is the link name).

It's easier to pass key in environment with `docker-compose`.

```yaml
    links:
      - hello
      - world
    environment:
        # Set private key
        HELLO_KEY: |
            -----BEGIN RSA PRIVATE KEY-----
            MIICXQIBAAKBgQDR8TdQF9fDlGhy1SMgfhMBi9TaFeD12/FK27TZE/tYGhxXvs1C
            NmFJy1hjVxspF5unmUsCk0yEsvEdcAdp17Vynz6W41VdinETU9yXHlUJ6NyI32AH
            dnFnHEcsllSEqD1hPAAvMUWwSMJaNmBEFtl8DUMS9tPX5fWGX4w5Xx8dZwIDAQAB
            AoGBAMb20jMHxaZHWg2qTRYYJa8LdHgS0BZxkWYefnBUbZn7dOz7mM+tddpX6raK
            8OSqyQu3Tc1tB9GjPLtnVr9KfVwhUVM7YXC/wOZo+u72bv9+4OMrEK/R8xy30XWj
            GePXEu95yArE4NucYphxBLWMMu2E4RodjyJpczsl0Lohcn4BAkEA+XPaEKnNA3AL
            1DXRpSpaa0ukGUY/zM7HNUFMW3UP00nxNCpWLSBmrQ56Suy7iSy91oa6HWkDD/4C
            k0HslnMW5wJBANdz4ehByMJZmJu/b5y8wnFSqep2jmJ1InMvd18BfVoBTQJwGMAr
            +qwSwNXXK2YYl9VJmCPCfgN0o7h1AEzvdYECQAM5UxUqDKNBvHVmqKn4zShb1ugY
            t1RfS8XNbT41WhoB96MT9P8qTwlniX8UZiwUrvNp1Ffy9n4raz8Z+APNwvsCQQC9
            AuaOsReEmMFu8VTjNh2G+TQjgvqKmaQtVNjuOgpUKYv7tYehH3P7/T+62dcy7CRX
            cwbLaFbQhUUUD2DCHdkBAkB6CbB+qhu67oE4nnBCXllI9EXktXgFyXv/cScNvM9Y
            FDzzNAAfVc5Nmbmx28Nw+0w6pnpe/3m0Tudbq3nHdHfQ
            -----END RSA PRIVATE KEY-----

```

Options are set using the following pattern: `LINKNAME_KEY`

### Setup port


__Caution__: Using `PORT_MAP` with multiple ports on single service will cause `tor` to fail.

Use link setting in environment with the following pattern: `LINKNAME_PORTS`.

Like docker, first port is exposed port and the second one is service internal port.

```yaml
links:
  - hello
  - world
  - hey
environment:
    # Set mapping ports
    HELLO_PORTS: 80:80

    # Multiple ports can be coma separated
    WORLD_PORTS: 8000:80,8888:80,22:22

    # Socket mapping is supported
    HEY_PORTS: 80:unix:/var/run/socket.sock

```

__DEPRECATED:__
By default, ports are the same as linked containers, but a default port can be mapped using `PORT_MAP` environment variable.

#### Socket

To increase security, it's possible to setup your service through socket between containers and turn off network in your app container. See `docker-compose.v2.sock.yml` for an example.

__Warning__: Due to a bug in `tor` configuration parser, it's not possible to mix network link and socket link in the same `tor` configuration.

### Group services

Multiple services can be hosted behind the same onion address.

```yaml
links:
  - hello
  - world
  - hey
environment:
    # Set mapping ports
    HELLO_PORTS: 80:80

    # Multiple ports can be coma separated
    WORLD_PORTS: 8000:80,8888:80,22:22

    # Socket mapping is supported
    HEY_PORTS: 80:unix:/var/run/socket.sock

    # hello and world will share the same onion address
    # Service name can be any string as long there is not special char
    HELLO_SERVICE_NAME: foo
    WORLD_SERVICE_NAME: foo

```

__Warning__: Be carefull to not use the same exposed ports for grouped services.

### Compose v2 support

Links setting are required when using docker-compose v2. See `docker-compose.v2.yml` for example.

### Copose v3 support and secrets

Links setting are required when using docker-compose v3. See `docker-compose.v3.yml` for example.
