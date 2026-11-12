# JIRAAnnouncer: the Pyramid app served by waitress through pserve.
#
# The image holds the code and its pinned dependencies only. run.ini and all
# state (JIRAAnnouncer.sqlite, the *.p pickles, jsondump.log, webhook.log) come
# from the /data mount. /data is also the working dir, so the app's relative
# state paths land there.
#
# Run it with host networking (Anope JSON-RPC listens on 127.0.0.1:6080 and
# nginx proxies to 127.0.0.1:2006) and with an init process (compose
# `init: true`, or `docker run --init`): pserve installs no SIGTERM handler.
# deploy/compose.yml is the service definition; deploy/README.md is the runbook.

# python:3.12-slim, multi-arch index digest as of 2026-11-12
FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
# PIP_CONSTRAINT also reaches the isolated builds of the sdist-only packages
# (pyramid_prometheus, pyramid_scheduler), so they build with the pinned
# setuptools and wheel.
RUN PIP_CONSTRAINT=/app/requirements.txt pip install --no-cache-dir -r requirements.txt

COPY . .
RUN PIP_CONSTRAINT=/app/requirements.txt pip install --no-cache-dir --no-deps . \
    && pip check \
    && python -c "import jiraannouncer, waitress"
RUN rm -rf /app

WORKDIR /data
USER 1000:1000
EXPOSE 2006
CMD ["pserve", "/data/run.ini"]
