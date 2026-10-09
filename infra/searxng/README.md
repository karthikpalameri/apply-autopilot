# Local SearXNG

A private, local SearXNG instance for web research. It is bound to `127.0.0.1:8080` and is not intended to be exposed publicly.

## Start

1. Start Docker Desktop:

   ```sh
   open -a Docker
   ```

2. Start SearXNG:

   ```sh
   cd infra/searxng
   docker compose up -d
   ```

3. Open <http://127.0.0.1:8080>.

## Everyday commands

Run these from `infra/searxng`:

```sh
docker compose ps
docker compose logs -f core
docker compose stop       # pause, keep data
docker compose start      # resume
docker compose down       # remove containers, keep named volumes
docker compose pull && docker compose up -d  # update images
```

`core-config/settings.yml` is generated on first start and ignored by Git because it contains the instance secret. Do not expose this instance to the internet without configuring authentication, rate limiting, and a reverse proxy.

## References

- <https://docs.searxng.org/admin/installation-docker.html>
- <https://docs.searxng.org/admin/settings/>
- <https://docs.docker.com/desktop/setup/install/mac-install/>
