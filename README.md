# docker-tor-hidden-service

Create a tor hidden service with a link

```
# run a container with an network application
$ docker run -d --name hello_world tutum/hello_world

# and just link it to this container
$ docker run -ti --link hello_world goldy/tor-hidden-service
```

The .onion url is displayed to stdout at startup.

To keep onion keys, just mount volume `/var/lib/tor/hidden_service/`

```
$ docker run -ti --link something --volume /path/to/keys:/var/lib/tor/hidden_service/ goldy/tor-hidden-service
```

Look at the `docker-compose.yml` file to see own to use it.

### pyentrypoint

This container is using [`pyentrypoint`](https://github.com/cmehay/pyentrypoint) to generate its setup.

If you need to use the legacy version, please checkout to the `legacy` branch or pull `goldy/tor-hidden-service:legacy`.
