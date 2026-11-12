#!/usr/bin/env python3
"""Stand-in for Anope JSON-RPC and the FuelRats API when testing JIRAAnnouncer.

Point rpc_proxy, rpc_devproxy, fr_url and api_url of a test ini at this stub.
It appends one JSON line per request to --log: the method, the path and the
JSON body (null when there is none or it is not JSON). Request headers are
never logged, because the app sends its tokens in the Authorization header.

POST answers {"jsonrpc": "2.0", "result": [], "id": 1}; GET answers
{"data": []} (an empty list of open rescues). Standard library only.
"""
import argparse
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

POST_REPLY = {"jsonrpc": "2.0", "result": [], "id": 1}
GET_REPLY = {"data": []}


class StubHandler(BaseHTTPRequestHandler):
    log_path = None
    log_lock = threading.Lock()

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except ValueError:
            return None

    def _record(self, body):
        line = json.dumps({"method": self.command, "path": self.path, "body": body})
        with self.log_lock:
            with open(self.log_path, "a", encoding="utf-8") as log:
                log.write(line + "\n")
                log.flush()

    def _reply(self, payload):
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._record(None)
        self._reply(GET_REPLY)

    def do_POST(self):
        self._record(self._read_json_body())
        self._reply(POST_REPLY)


def main():
    parser = argparse.ArgumentParser(description="JIRAAnnouncer test stub")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2099)
    parser.add_argument("--log", required=True, help="file to append request lines to")
    args = parser.parse_args()

    StubHandler.log_path = args.log
    # Create the log up front so callers can count its lines before the first request.
    open(args.log, "a", encoding="utf-8").close()

    server = ThreadingHTTPServer((args.bind, args.port), StubHandler)
    print(f"stub listening on {args.bind}:{args.port}, logging to {args.log}",
          file=sys.stderr, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
