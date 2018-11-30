# docker-tor-hidden-service

## What's New?

* /version is a text file with the current of Tor version generated with each build 
* Weekly builds. The Goldy's original image hadn't been updated in some time. Using the latest version of Tor is always best practice.

Create a tor hidden service with a link

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

## Setup

### Set private key

Private key is settable by environment or by copying file in `hostname/private_key` in docket volume (`hostname` is the link name).

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

Changing `/etc/tor/torrc` file trigger a `SIGHUP` signal to `tor` to reload configuration.

To disable this behavior, add `ENTRYPOINT_DISABLE_RELOAD` in environment.


### pyentrypoint

This container is using [`pyentrypoint`](https://github.com/cmehay/pyentrypoint) to generate its setup.

If you need to use the legacy version, please checkout the `legacy` branch or pull `goldy/tor-hidden-service:legacy`.
