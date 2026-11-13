"""Local mock login target for safely exercising the brute-force tool.

Runs a tiny HTTP server on 127.0.0.1:8000 with a single /login endpoint that
accepts form-encoded username/password. It returns 200 + "Welcome" only for the
one correct credential, and 401 + "Invalid credentials" otherwise -- matching
configs/rules.json. This lets you test the tool end-to-end against your OWN
machine without touching any third party.

Usage:
    python scripts/mock_target.py
Then in another terminal:
    python main.py --target http://127.0.0.1:8000/login \
        --scope configs/scope.txt --username admin \
        --wordlist wordlists/common.txt --rules configs/rules.json
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

VALID_USER = "admin"
VALID_PASS = "s3cr3t"


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        form = urllib.parse.parse_qs(body)
        user = form.get("username", [""])[0]
        pw = form.get("password", [""])[0]
        if user == VALID_USER and pw == VALID_PASS:
            self._respond(200, "Welcome to the dashboard")
        else:
            self._respond(401, "Invalid credentials")

    def _respond(self, code, msg):
        data = msg.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass  # quiet


if __name__ == "__main__":
    print("Mock target on http://127.0.0.1:8000/login (valid: admin / s3cr3t)")
    print("Ctrl+C to stop.")
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
