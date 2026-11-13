from bruteforce.perm import expand


def test_single_digit_charset():
    assert list(expand("?d")) == list("0123456789")


def test_single_lower_charset():
    assert list(expand("?l")) == list("abcdefghijklmnopqrstuvwxyz")


def test_two_charset_combo_count():
    out = list(expand("?l?d"))
    assert len(out) == 26 * 10
    assert "a0" in out
    assert "z9" in out


def test_ordering_is_product_order():
    out = list(expand("?d?d"))
    assert out[0] == "00"
    assert out[1] == "01"
    assert out[-1] == "99"


def test_symbol_charset():
    out = list(expand("?s"))
    assert set(out) == set("!@#$%^&*")
