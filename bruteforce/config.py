import argparse

class Config:
    pass

def parse(args):
    p = argparse.ArgumentParser()
    p.add_argument("--target", required=True)
    p.add_argument("--scope", required=True)
    p.add_argument("--username", default="admin")
    p.add_argument("--wordlist", default="")
    p.add_argument("--mask", default="")
    p.add_argument("--rules", default="")
    p.add_argument("--data", default="",
                   help="POST body template, e.g. 'user=^USER^&pass=^PASS^'. "
                        "^USER^/^PASS^ are replaced (URL-encoded) per attempt. "
                        "If omitted, defaults to username=<user>&password=<pass>.")
    p.add_argument("--csrf-field", default="",
                   help="Hidden form field holding a CSRF/anti-forgery token "
                        "(e.g. 'user_token'). When set, each attempt first GETs "
                        "the page, scrapes this field's value, carries the session "
                        "cookie, and includes the token in the POST (use ^TOKEN^ in "
                        "--data, or it is appended automatically).")
    p.add_argument("--csrf-url", default="",
                   help="Page to GET for the CSRF token (defaults to --target).")
    p.add_argument("--method", default="POST", choices=["POST", "GET"],
                   help="How credentials are submitted. GET puts them in the "
                        "query string (e.g. DVWA's brute-force page); POST in the "
                        "request body (default).")
    p.add_argument("--cookie", default="",
                   help="Cookie header sent with every request, e.g. "
                        "'PHPSESSID=abc123; security=low'. Needed for login forms "
                        "behind an authenticated area.")
    p.add_argument("--threads", type=int, default=4)
    p.add_argument("--rps", type=int, default=10)
    p.add_argument("--proxies", default="")
    p.add_argument("--output", default="hits.txt")
    p.add_argument("--state", default="session.state")
    ns = p.parse_args(args)
    c = Config()
    for k,v in vars(ns).items():
        setattr(c, k, v)
    return c
