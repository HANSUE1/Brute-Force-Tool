import hashlib

import pytest

from bruteforce.auth import authorize, verify_scope_hash


def _scope(tmp_path, text):
    f = tmp_path / "scope.txt"
    f.write_text(text)
    return str(f)


def test_in_scope_allowed(tmp_path):
    s = _scope(tmp_path, "http://a\nhttp://b\n")
    authorize("http://a", s)  # must not raise


def test_out_of_scope_denied(tmp_path):
    s = _scope(tmp_path, "http://a\n")
    with pytest.raises(SystemExit):
        authorize("http://evil.example", s)


def test_comments_and_blanks_ignored(tmp_path):
    s = _scope(tmp_path, "# a comment\n\nhttp://a\n")
    authorize("http://a", s)
    with pytest.raises(SystemExit):
        authorize("# a comment", s)  # the comment line is not a target


def test_scope_hash_match(tmp_path):
    f = tmp_path / "scope.txt"
    f.write_bytes(b"targets")
    verify_scope_hash(str(f), hashlib.sha256(b"targets").hexdigest())


def test_scope_hash_mismatch(tmp_path):
    f = tmp_path / "scope.txt"
    f.write_bytes(b"targets")
    with pytest.raises(ValueError):
        verify_scope_hash(str(f), "deadbeef")
