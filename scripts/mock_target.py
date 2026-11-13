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


LOGIN_FORM = """<!doctype html>
<html><head><title>Mock Login</title></head><body>
<h2>Mock Login</h2>
<form method="POST" action="/login">
  <label>Username <input name="username"></label><br>
  <label>Password <input name="password" type="password"></label><br>
  <button type="submit">Log in</button>
</form>
<p>Practice target. Valid credential: admin / s3cr3t</p>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._respond(200, LOGIN_FORM, "text/html")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        form = urllib.parse.parse_qs(body)
        if self.path.rstrip("/") == "/altlogin":
            # Same credential, but DIFFERENT field names (user / passwd) to
            # demonstrate the --data template handling arbitrary form fields.
            user = form.get("user", [""])[0]
            pw = form.get("passwd", [""])[0]
        else:
            user = form.get("username", [""])[0]
            pw = form.get("password", [""])[0]
        if user == VALID_USER and pw == VALID_PASS:
            self._respond(200, "Welcome to the dashboard")
        else:
            self._respond(401, "Invalid credentials")

    def _respond(self, code, msg, content_type="text/plain"):
        data = msg.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass  # quiet


if __name__ == "__main__":
    print("Mock target on http://127.0.0.1:8000/login (valid: admin / s3cr3t)")
    print("Ctrl+C to stop.")
    server = HTTPServer(("127.0.0.1", 8000), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping mock target.")
        server.server_close()
