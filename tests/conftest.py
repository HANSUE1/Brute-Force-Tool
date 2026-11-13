"""Shared fixtures and helpers for the test suite.

The end-to-end tests run the real mock target (scripts/mock_target.py) on an
EPHEMERAL port in a background thread, so they never touch port 8000 and never
leave a server lingering -- the recurring Windows headache when testing by hand.
"""
import sys
import types
import threading
from http.server import HTTPServer
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"

# Make the `bruteforce` package and the mock_target module importable.
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SCRIPTS))

# Handy paths to the real config/wordlist files, so tests exercise them too.
WORDLIST = str(REPO_ROOT / "wordlists" / "common.txt")
RULES = str(REPO_ROOT / "configs" / "rules.json")
RULES_DVWA = str(REPO_ROOT / "configs" / "rules_dvwa.json")


@pytest.fixture
def mock_server():
    """Start the mock target on a random free port; yield its base URL."""
    import mock_target
    mock_target.SESSIONS.clear()  # isolate CSRF/session state between tests
    srv = HTTPServer(("127.0.0.1", 0), mock_target.Handler)
    port = srv.server_address[1]
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        srv.shutdown()
        thread.join(timeout=2)
        srv.server_close()


def make_cfg(tmp_path, **overrides):
    """Build a Config-like namespace with sane defaults for Engine tests."""
    cfg = types.SimpleNamespace(
        target="", scope="", username="admin",
        wordlist=WORDLIST, mask="", rules=RULES, data="",
        csrf_field="", csrf_url="", method="POST", cookie="",
        proxies="", threads=4, rps=1000,
        output=str(tmp_path / "hits.txt"),
        state=str(tmp_path / "session.state"),
    )
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


def read_hits(cfg):
    p = Path(cfg.output)
    return p.read_text().split() if p.exists() else []
