from bruteforce.state import load, save


def test_roundtrip(tmp_path):
    p = str(tmp_path / "session.state")
    save(p, {"target": "http://x", "completed": 5, "total": 10})
    assert load(p) == {"target": "http://x", "completed": 5, "total": 10}


def test_load_missing_returns_empty(tmp_path):
    assert load(str(tmp_path / "does_not_exist.state")) == {}
