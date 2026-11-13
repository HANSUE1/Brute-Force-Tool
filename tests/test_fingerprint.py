from bruteforce.fingerprint import is_success


def test_empty_rules_always_true():
    # No rules -> everything looks like success (why --rules matters).
    assert is_success("anything", 500, {}) is True


def test_status_rule():
    assert is_success("x", 200, {"status": 200})
    assert not is_success("x", 401, {"status": 200})


def test_regex_rule():
    assert is_success("Welcome home", 200, {"regex": "Welcome"})
    assert not is_success("nope", 200, {"regex": "Welcome"})


def test_regex_alternation():
    rules = {"regex": "Welcome|dashboard"}
    assert is_success("to the dashboard", 200, rules)


def test_not_contains_rule():
    assert not is_success("Invalid credentials", 200, {"not_contains": "Invalid"})
    assert is_success("all good", 200, {"not_contains": "Invalid"})


def test_body_len_rule():
    assert is_success("abcd", 200, {"body_len": 4})
    assert not is_success("abc", 200, {"body_len": 4})


def test_all_rules_must_pass():
    rules = {"status": 200, "regex": "Welcome", "not_contains": "Invalid"}
    assert is_success("Welcome back", 200, rules)
    assert not is_success("Welcome but Invalid", 200, rules)  # not_contains fails
    assert not is_success("Welcome back", 401, rules)         # status fails
