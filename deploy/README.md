# JIRAAnnouncer deployment (mozzarella)

JIRAAnnouncer (announcer.fuelrats.com, announcer-dev.fuelrats.com, announcer.fuelrats.dev) runs on mozzarella as compose project `announcer`, service `fr-announcer`, from an image built on the host from this repo.

Layout of `/home/fuelrats/announcer` (all owned by fuelrats):

| Path | Contents |
|---|---|
| `compose.yml` | copy of `deploy/compose.yml` |
| `.env` | `ANNOUNCER_TAG=<sha7>`, the image tag to run (not secret; see `deploy/env.example`) |
| `data/` | `run.ini` and all state, mounted on `/data` |
| `src/` | clean clone of FuelRats/JIRAAnnouncer, used for builds only |

The container uses host networking: Anope JSON-RPC is on `127.0.0.1:6080`, nginx proxies to `127.0.0.1:2006`, and the GELF handlers use the host's routes. It runs as 1000:1000 with a read-only root, `/tmp` on tmpfs, no capabilities and an init process. There is no systemd unit; `restart: unless-stopped` brings it back after a Docker or host restart.

## Build

On mozzarella:

```
cd /home/fuelrats/announcer/src && git fetch && git checkout --detach origin/master && S=$(git rev-parse --short HEAD) && sudo docker build -t fr-announcer:$S .
```

The build installs the pins from `requirements.txt` (`PIP_CONSTRAINT` also pins the build backend) and fails unless `pip check` passes. To confirm the image matches the pins:

```
sudo docker run --rm --entrypoint pip fr-announcer:$S freeze --all | grep -viE '^(pip|jiraannouncer)[ =@]' | diff - requirements.txt
```

It prints nothing when they match.

## Release

```
cd /home/fuelrats/announcer && sed -i "s/^ANNOUNCER_TAG=.*/ANNOUNCER_TAG=$S/" .env && sudo docker compose up -d
```

`.env` is not bind-mounted into any container, so `sed -i` is safe. If `src/deploy/compose.yml` changed, copy it to `/home/fuelrats/announcer/compose.yml` first (`install -m 644 src/deploy/compose.yml compose.yml`).

Check the result:

```
sudo docker compose ps --format '{{.Service}} {{.Image}} {{.Status}}'
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:2006/
```

## Rollback

Set the previous sha in `.env`, then run `sudo docker compose up -d`:

```
cd /home/fuelrats/announcer && sed -i "s/^ANNOUNCER_TAG=.*/ANNOUNCER_TAG=<previous sha7>/" .env && sudo docker compose up -d
```

A weekly cron (`/etc/cron.d/docker-image-prune`, Sundays 04:00, `docker image prune -af --filter until=168h`) deletes every image that no container uses and that is older than 7 days. If the previous image is gone, rebuild it from its sha first:

```
cd /home/fuelrats/announcer/src && git fetch && git checkout --detach <previous sha7> && sudo docker build -t fr-announcer:<previous sha7> .
```

## State

All state lives in `/home/fuelrats/announcer/data`, owned 1000:1000, which is the container's working dir:

- `run.ini` (mode 600, secrets; never print its values);
- `JIRAAnnouncer.sqlite`;
- `lastmessage.p`, `kennel.p`, `donation_totals.p`;
- `jsondump.log`, `webhook.log`.

The image contains no ini, sqlite or pickle.

## Webhook authentication

How each announcing route checks its sender:

| Route | Check | `run.ini` key | Sender setting |
|---|---|---|---|
| `/stripe` | `Stripe-Signature`; fails closed | `stripe_webhook_secret` (the endpoint's `whsec_` signing secret) | Stripe dashboard, webhook endpoint |
| `/jira` | `?token=`; fails closed | `jira_token` | Jira webhook URL `https://announcer.fuelrats.com/jira?token=<jira_token>` |
| `/statuspage` | `?token=`; fails closed | `statuspage_token` | Statuspage webhook URL `https://announcer.fuelrats.com/statuspage?token=<statuspage_token>` |
| `/api` | `X-Api-Signature` HMAC | `api_secret` | FuelRats API |
| `/github` | `X-Hub-Signature` HMAC, skipped when the key is unset | `github_secret` | repository webhook secret |
| `/discourse` | Discourse signature, skipped when the key is unset | `discourse_secret` | Discourse webhook secret |
| `/client` | `X-Client-Signature` HMAC only when the header is sent; otherwise unauthenticated, posts to `#fuelrats` only | `client_secret` | rescue page |
| `/drill` | none; channel limited to `#drillrats`, `#drillrats2`, `#drillrats3` | | drill form |

The `?token=` value appears in the nginx access log, so treat that log as sensitive. To rotate a token, set the new URL at the sender and the new value in `run.ini` together, then restart the service.

## Logs

```
sudo docker compose -f /home/fuelrats/announcer/compose.yml logs --since 1h fr-announcer
```

The same records also go to Graylog through the GELF handler in `run.ini`.

## Testing

Test only against an instance whose ini points `rpc_proxy`, `rpc_devproxy`, `fr_url` and `api_url` at `deploy/stub.py` and replaces every token. Never POST to a live-config instance: `send()` posts to whatever `rpc_proxy` names, so a test instance with prod values posts to prod IRC.

- `deploy/stub.py --port 2099 --log <file>` stands in for Anope JSON-RPC and the FuelRats API. It logs method, path and JSON body of each request, never headers.
- `SMOKE_SECRET=<value> deploy/smoke.sh BASE_URL METRICS_URL STUB_LOG` checks the home page, a static file and the metrics endpoint; posts a `/client` event; checks that an unsigned `/stripe` event and token-less `/jira` and `/statuspage` calls get 403; posts a signed `/stripe`, a `/jira` and a `/statuspage` event with the token; and checks that the removed routes answer 404. The test ini sets `jira_token`, `statuspage_token` and `stripe_webhook_secret` all to `SMOKE_SECRET`. It needs `curl` and `openssl`. Afterwards, check that `kennel.p` in the test instance's data dir was written.

Example on mozzarella, with a staging instance on `127.0.0.1:2007` and its metrics on port 6800:

```
python3 /home/fuelrats/announcer/src/deploy/stub.py --port 2099 --log /home/fuelrats/announcer/staging/stub.log &
SMOKE_SECRET=localtest sh /home/fuelrats/announcer/src/deploy/smoke.sh http://127.0.0.1:2007 http://127.0.0.1:6800/metrics /home/fuelrats/announcer/staging/stub.log
```
