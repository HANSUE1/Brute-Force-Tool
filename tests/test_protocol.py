from bruteforce.protocol import extract_token, HTTPProtocol


def test_extract_name_before_value():
    html = "<input type='hidden' name='user_token' value='abc123'>"
    assert extract_token(html, "user_token") == "abc123"


def test_extract_value_before_name():
    html = '<input type="hidden" value="xyz789" name="user_token" />'
    assert extract_token(html, "user_token") == "xyz789"


def test_extract_missing_field():
    assert extract_token("<p>no token here</p>", "user_token") is None


def test_extract_only_matching_field():
    html = ("<input name='other' value='nope'>"
            "<input name='user_token' value='yes'>")
    assert extract_token(html, "user_token") == "yes"


def test_build_query_default_fields():
    p = HTTPProtocol("http://x")
    assert p._build_query("admin", "s3cr3t") == "username=admin&password=s3cr3t"


def test_build_query_template_and_token():
    p = HTTPProtocol("http://x", data_template="u=^USER^&p=^PASS^&t=^TOKEN^")
    assert p._build_query("a b", "p@ss", token="tok") == "u=a+b&p=p%40ss&t=tok"
