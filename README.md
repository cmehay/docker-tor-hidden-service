# docker-tor-hidden-service

Create a tor hidden service with a link

```sh
# run a container with a network application
$ docker run -d --name hello_world tutum/hello_world

# and just link it to this container
$ docker run -ti --link hello_world goldy/tor-hidden-service
```

The .onion URLs are displayed to stdout at startup.

To keep onion keys, just mount volume `/var/lib/tor/hidden_service/`

```sh
$ docker run -ti --link something --volume /path/to/keys:/var/lib/tor/hidden_service/ goldy/tor-hidden-service
```

Look at the `docker-compose.yml` file to see how to use it.

### Setup port

By default, ports are the same as linked containers, but a default port can be mapped using `PORT_MAP` environment variable.

__Caution__: Using `PORT_MAP` with multiple ports on single service will cause `tor` to fail.

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


### pyentrypoint

This container is using [`pyentrypoint`](https://github.com/cmehay/pyentrypoint) to generate its setup.

If you need to use the legacy version, please checkout the `legacy` branch or pull `goldy/tor-hidden-service:legacy`.
