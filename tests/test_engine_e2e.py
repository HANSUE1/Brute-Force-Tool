"""End-to-end tests: run the real Engine against the live mock target.

Each test asserts the tool finds (or correctly fails to find) the password
's3cr3t' through a different form shape, exercising the full request path.
"""
from bruteforce.engine import Engine
from conftest import make_cfg, read_hits, RULES_DVWA


def test_plain_login(mock_server, tmp_path):
    cfg = make_cfg(tmp_path, target=mock_server + "/login")
    Engine(cfg).run()
    assert "s3cr3t" in read_hits(cfg)


def test_altlogin_needs_data_template(mock_server, tmp_path):
    # Right field names via --data -> hit.
    cfg = make_cfg(tmp_path, target=mock_server + "/altlogin",
                   data="user=^USER^&passwd=^PASS^")
    Engine(cfg).run()
    assert "s3cr3t" in read_hits(cfg)


def test_altlogin_default_fields_miss(mock_server, tmp_path):
    # Default username/password fields don't match user/passwd -> no hit.
    cfg = make_cfg(tmp_path, target=mock_server + "/altlogin")
    Engine(cfg).run()
    assert read_hits(cfg) == []


def test_csrf_with_token(mock_server, tmp_path):
    cfg = make_cfg(tmp_path, target=mock_server + "/csrf",
                   data="username=^USER^&password=^PASS^&user_token=^TOKEN^",
                   csrf_field="user_token")
    Engine(cfg).run()
    assert "s3cr3t" in read_hits(cfg)


def test_csrf_without_token_fails(mock_server, tmp_path):
    cfg = make_cfg(tmp_path, target=mock_server + "/csrf")
    Engine(cfg).run()
    assert read_hits(cfg) == []


def test_dvwa_low(mock_server, tmp_path):
    cfg = make_cfg(tmp_path, target=mock_server + "/dvwa", method="GET",
                   cookie="dvwa_session=abc; security=low",
                   data="username=^USER^&password=^PASS^&Login=Login",
                   rules=RULES_DVWA)
    Engine(cfg).run()
    assert "s3cr3t" in read_hits(cfg)


def test_dvwa_high_rotating_token(mock_server, tmp_path):
    cfg = make_cfg(tmp_path, target=mock_server + "/dvwa", method="GET",
                   cookie="dvwa_session=abc; security=high",
                   data="username=^USER^&password=^PASS^&user_token=^TOKEN^&Login=Login",
                   csrf_field="user_token", threads=1, rules=RULES_DVWA)
    Engine(cfg).run()
    assert "s3cr3t" in read_hits(cfg)


def test_dvwa_without_cookie_denied(mock_server, tmp_path):
    cfg = make_cfg(tmp_path, target=mock_server + "/dvwa", method="GET",
                   data="username=^USER^&password=^PASS^&Login=Login",
                   rules=RULES_DVWA)
    Engine(cfg).run()
    assert read_hits(cfg) == []


def test_resume_from_checkpoint(mock_server, tmp_path):
    # First full run finds the password and records a completed count.
    cfg = make_cfg(tmp_path, target=mock_server + "/login")
    Engine(cfg).run()
    from bruteforce.state import load
    st = load(cfg.state)
    assert st["completed"] >= 1
    # A second run resumes past the checkpoint (no candidates left) -> no crash,
    # and no duplicate work beyond what remains.
    Engine(cfg).run()
    assert load(cfg.state)["completed"] >= st["completed"]
