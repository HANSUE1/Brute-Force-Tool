import pytest

from bruteforce.config import parse


def test_required_and_defaults():
    c = parse(["--target", "http://x", "--scope", "scope.txt"])
    assert c.target == "http://x"
    assert c.scope == "scope.txt"
    assert c.username == "admin"
    assert c.threads == 4
    assert c.rps == 10
    assert c.method == "POST"
    assert c.output == "hits.txt"


def test_method_choice_get():
    c = parse(["--target", "x", "--scope", "s", "--method", "GET"])
    assert c.method == "GET"


def test_invalid_method_rejected():
    with pytest.raises(SystemExit):
        parse(["--target", "x", "--scope", "s", "--method", "PUT"])


def test_new_flags_parsed():
    c = parse(["--target", "x", "--scope", "s",
               "--data", "u=^USER^&p=^PASS^",
               "--cookie", "PHPSESSID=abc; security=low",
               "--csrf-field", "user_token",
               "--csrf-url", "http://x/login"])
    assert c.data == "u=^USER^&p=^PASS^"
    assert c.cookie == "PHPSESSID=abc; security=low"
    assert c.csrf_field == "user_token"
    assert c.csrf_url == "http://x/login"


def test_missing_required_fails():
    with pytest.raises(SystemExit):
        parse(["--scope", "s"])  # no --target
