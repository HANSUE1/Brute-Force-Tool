"""Local mock login target for safely exercising the brute-force tool.

Runs a tiny HTTP server on 127.0.0.1:8000 with three endpoints, all guarding the
same credential (admin / s3cr3t) so you can practice different attack shapes:

  /login     plain form, fields username / password   (default behaviour)
  /altlogin  same, but fields are named user / passwd  (practice --data)
  /csrf      CSRF-protected: you must GET a per-session token first and send it
             back with the session cookie                (practice --csrf-field)

Each returns 200 + "Welcome" only for the correct credential, and an error
(401 "Invalid credentials", or 403 "CSRF token mismatch") otherwise -- matching
configs/rules.json. Everything is local; no third party is touched.

Usage:
    python scripts/mock_target.py
Then in another terminal, e.g.:
    python main.py --target http://127.0.0.1:8000/login \
        --scope configs/scope.txt --username admin \
        --wordlist wordlists/common.txt --rules configs/rules.json
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import uuid

VALID_USER = "admin"
VALID_PASS = "s3cr3t"

# In-memory session store: session id -> current valid CSRF token.
# The server is single-threaded, so no locking is needed.
SESSIONS = {}


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

CSRF_FORM = """<!doctype html>
<html><head><title>CSRF Login</title></head><body>
<h2>CSRF-protected Login</h2>
<form method="POST" action="/csrf">
  <input type="hidden" name="user_token" value="{token}">
  <label>Username <input name="username"></label><br>
  <label>Password <input name="password" type="password"></label><br>
  <button type="submit">Log in</button>
</form>
<p>Each page load issues a fresh user_token tied to your session cookie.</p>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.rstrip("/") == "/csrf":
            sid = self._sid() or uuid.uuid4().hex
            token = uuid.uuid4().hex
            SESSIONS[sid] = token
            self._respond(200, CSRF_FORM.format(token=token), "text/html",
                          {"Set-Cookie": f"sid={sid}; Path=/"})
        else:
            self._respond(200, LOGIN_FORM, "text/html")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        form = urllib.parse.parse_qs(body)
        path = self.path.rstrip("/")

        if path == "/csrf":
            sid = self._sid()
            sent = form.get("user_token", [""])[0]
            if not sid or sent != SESSIONS.get(sid):
                self._respond(403, "CSRF token mismatch")
                return
            SESSIONS[sid] = uuid.uuid4().hex  # rotate token (like DVWA "high")
            user = form.get("username", [""])[0]
            pw = form.get("password", [""])[0]
        elif path == "/altlogin":
            # DIFFERENT field names (user / passwd) to practice --data.
            user = form.get("user", [""])[0]
            pw = form.get("passwd", [""])[0]
        else:
            user = form.get("username", [""])[0]
            pw = form.get("password", [""])[0]

        if user == VALID_USER and pw == VALID_PASS:
            self._respond(200, "Welcome to the dashboard")
        else:
            self._respond(401, "Invalid credentials")

    def _sid(self):
        for part in self.headers.get("Cookie", "").split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                if k == "sid":
                    return v
        return None

    def _respond(self, code, msg, content_type="text/plain", extra_headers=None):
        data = msg.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass  # quiet


if __name__ == "__main__":
    print("Mock target on http://127.0.0.1:8000  (valid: admin / s3cr3t)")
    print("  /login  /altlogin  /csrf")
    print("Ctrl+C to stop.")
    server = HTTPServer(("127.0.0.1", 8000), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping mock target.")
        server.server_close()
