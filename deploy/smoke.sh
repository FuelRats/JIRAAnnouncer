#!/bin/sh
# Smoke test for a JIRAAnnouncer test instance.
#
# Usage: smoke.sh BASE_URL METRICS_URL STUB_LOG
#   BASE_URL     the instance, for example http://127.0.0.1:2007
#   METRICS_URL  its Prometheus endpoint, for example http://127.0.0.1:6800/metrics
#   STUB_LOG     the --log file of the deploy/stub.py that the instance's ini points at
#
# Run it only against an instance whose rpc_proxy, rpc_devproxy, fr_url and
# api_url point at deploy/stub.py: the POST checks make the app send IRC
# messages and write its state files. The /jira check only proves that the
# request was served; the caller checks that kennel.p was written.
#
# It prints one line per check and exits non-zero on the first failure.
# POSIX sh: runs under busybox sh (curlimages/curl image) and dash.

set -u

if [ "$#" -ne 3 ]; then
    echo "usage: $0 BASE_URL METRICS_URL STUB_LOG" >&2
    exit 2
fi
BASE_URL=${1%/}
METRICS_URL=$2
STUB_LOG=$3

CURL_TIMEOUT=30   # seconds per request; the /jira view alone sleeps 2 s
LOG_WAIT=5        # seconds to wait for an expected stub log line

# Fixed string from jiraannouncer/templates/layout.jinja2 (the page title).
HOME_TEXT='Alchemy Scaffold for The Pyramid Web Framework'

STRIPE_EVENT='{"id":"evt_smoke","object":"event","type":"payment_intent.succeeded","data":{"object":{"id":"pi_smoke","object":"payment_intent","amount":500,"currency":"usd","metadata":{}}}}'

# The fields views/jira.py reads on the OV- automation path. issue_event_type_name
# is read by the duplicate check when the previous message was the same event.
JIRA_EVENT='{"webhookEvent":"jira:issue_updated","issue_event_type_name":"issue_generic","user":{"displayName":"Fuel Rats Automation"},"issue":{"key":"OV-1","fields":{}}}'

ok() { echo "ok    $*"; }
fail() { echo "FAIL  $*"; exit 1; }

# served CODE: the app answered and the answer is not a 5xx.
served() {
    case "$1" in
        000|5??) return 1 ;;
    esac
    return 0
}

# log_mark: current line count of the stub log, so a check only reads lines it caused.
log_mark() {
    if [ -f "$STUB_LOG" ]; then
        wc -l < "$STUB_LOG" | tr -d ' '
    else
        echo 0
    fi
}

# log_has MARK TEXT: a POST to /jsonrpc logged after line MARK contains TEXT.
log_has() {
    _tries=0
    while [ "$_tries" -lt "$LOG_WAIT" ]; do
        if tail -n "+$(($1 + 1))" "$STUB_LOG" 2>/dev/null \
            | grep -F '"POST"' | grep -F '"/jsonrpc"' | grep -qF "$2"; then
            return 0
        fi
        _tries=$((_tries + 1))
        sleep 1
    done
    return 1
}

# 1. Home page renders from the templates and the database.
resp=$(curl -s --max-time "$CURL_TIMEOUT" -w '\n%{http_code}' "$BASE_URL/")
code=$(printf '%s\n' "$resp" | tail -n 1)
[ "$code" = 200 ] || fail "GET / returned HTTP $code"
printf '%s\n' "$resp" | grep -qF "$HOME_TEXT" || fail "GET / body lacks '$HOME_TEXT'"
ok "GET / -> 200 with the layout title"

# 2. Package static files are shipped.
code=$(curl -s --max-time "$CURL_TIMEOUT" -o /dev/null -w '%{http_code}' "$BASE_URL/pyramid-static/theme.css")
[ "$code" = 200 ] || fail "GET /pyramid-static/theme.css returned HTTP $code"
ok "GET /pyramid-static/theme.css -> 200"

# 3. pyramid_prometheus exporter answers.
resp=$(curl -s --max-time "$CURL_TIMEOUT" -w '\n%{http_code}' "$METRICS_URL")
code=$(printf '%s\n' "$resp" | tail -n 1)
[ "$code" = 200 ] || fail "GET $METRICS_URL returned HTTP $code"
printf '%s\n' "$resp" | grep -qF '# HELP' || fail "GET $METRICS_URL body lacks '# HELP'"
ok "GET $METRICS_URL -> 200 with '# HELP'"

# 4. /client: a rescue-page arrival reaches send() for #fuelrats.
mark=$(log_mark)
code=$(curl -s --max-time "$CURL_TIMEOUT" -o /dev/null -w '%{http_code}' -X POST "$BASE_URL/client" \
    -H 'Referer: https://clients.fuelrats.com/' -H 'X-Forwarded-For: 192.0.2.10' \
    --data-urlencode cmdrname=Jameson --data-urlencode system=Sol --data-urlencode platform=PC \
    --data-urlencode EO2=NO --data-urlencode odyssey=Odyssey)
served "$code" || fail "POST /client returned HTTP $code"
text='say #fuelrats Incoming Client: Jameson - System: Sol'
log_has "$mark" "$text" || fail "POST /client -> $code, but the stub log has no POST /jsonrpc with '$text'"
ok "POST /client -> $code, stub got '$text'"

# 5. /stripe: a succeeded payment intent is announced (and counted in donation_totals.p).
mark=$(log_mark)
code=$(curl -s --max-time "$CURL_TIMEOUT" -o /dev/null -w '%{http_code}' -X POST "$BASE_URL/stripe" \
    -H 'Content-Type: application/json' --data-raw "$STRIPE_EVENT")
served "$code" || fail "POST /stripe returned HTTP $code"
text='A donation of'
log_has "$mark" "$text" || fail "POST /stripe -> $code, but the stub log has no POST /jsonrpc with '$text'"
ok "POST /stripe -> $code, stub got '$text'"

# 6. /jira: the OV- automation path writes kennel.p.
code=$(curl -s --max-time "$CURL_TIMEOUT" -o /dev/null -w '%{http_code}' -X POST "$BASE_URL/jira" \
    -H 'Content-Type: application/json' --data-raw "$JIRA_EVENT")
served "$code" || fail "POST /jira returned HTTP $code"
ok "POST /jira -> $code (the caller checks kennel.p)"

echo "smoke: all 6 checks passed"
