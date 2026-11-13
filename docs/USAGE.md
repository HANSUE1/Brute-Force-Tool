# Usage

> **Authorized use only.** This tool only runs against targets listed in your
> scope file (`configs/scope.txt`). Only add a target you own or have written
> permission to test.

## Requirements

Python 3.8+ (tested on 3.13). No third-party packages — standard library only.

## Quick start (safe local test)

1. Start the bundled mock target in one terminal:

   ```bash
   python scripts/mock_target.py
   ```

   It serves `http://127.0.0.1:8000/login`, valid credential `admin` / `s3cr3t`.

2. Run the tool against it in another terminal:

   ```bash
   python main.py \
     --target http://127.0.0.1:8000/login \
     --scope configs/scope.txt \
     --username admin \
     --wordlist wordlists/common.txt \
     --rules configs/rules.json
   ```

   You should see `HIT: s3cr3t`, and the hit is appended to `hits.txt`.

## Arguments

| Flag | Default | Meaning |
|------|---------|---------|
| `--target` | (required) | URL to attempt logins against. Must be in scope. |
| `--scope` | (required) | Path to the authorization allowlist. |
| `--username` | `admin` | Username to try passwords for. |
| `--wordlist` | — | File of candidate passwords, one per line. |
| `--mask` | — | Mask like `?l?l?d` (`?l` lower, `?u` upper, `?d` digit, `?s` symbol). Combined with the wordlist if both given. |
| `--data` | — | POST body template for any form. Use `^USER^` / `^PASS^` (and `^TOKEN^` for CSRF) placeholders; they are URL-encoded per attempt. Omit to use the default `username=<user>&password=<pass>`. |
| `--csrf-field` | — | Hidden field holding a CSRF token (e.g. `user_token`). Enables GET-page-first token scraping with session-cookie carry-over. |
| `--csrf-url` | — | Page to GET for the token (defaults to `--target`). |
| `--rules` | — | JSON success-detection rules (see `configs/rules.json`). |
| `--threads` | 4 | Concurrent workers. |
| `--rps` | 10 | Per-worker rate limit (requests/sec). |
| `--proxies` | — | Comma-separated proxy URLs, rotated per request. |
| `--output` | `hits.txt` | Where successful candidates are written. |
| `--state` | `session.state` | Checkpoint file; a re-run resumes from it. |

## Matching any login form (`--data`)

Real forms rarely use the exact field names `username` / `password`. The `--data`
flag lets you match any form's fields with a body template, substituting the
username and password per attempt:

```bash
# Form whose fields are named user / passwd:
python main.py --target http://127.0.0.1:8000/altlogin \
  --scope configs/scope.txt --username admin \
  --wordlist wordlists/common.txt --rules configs/rules.json \
  --data "user=^USER^&passwd=^PASS^"

# A form with an extra fixed field is just more of the template:
#   --data "email=^USER^&pass=^PASS^&remember=1"
```

To find the real field names, open the login page in a browser, right-click the
username/password boxes → Inspect, and read each input's `name="..."` attribute.
The bundled mock target exposes `/altlogin` (fields `user` / `passwd`) so you can
practice this against something other than the default form.

## CSRF-protected forms (`--csrf-field`)

Many login forms embed a hidden anti-CSRF token that changes each page load and
is tied to a session cookie. A blind POST fails (typically 403). With
`--csrf-field`, each attempt instead:

1. **GET**s the page (`--csrf-url`, or `--target` by default),
2. scrapes the hidden field's `value`,
3. keeps the session cookie from that GET,
4. **POST**s the guess with the token (`^TOKEN^` in `--data`) and the cookie.

```bash
python main.py --target http://127.0.0.1:8000/csrf \
  --scope configs/scope.txt --username admin \
  --wordlist wordlists/common.txt --rules configs/rules.json \
  --data "username=^USER^&password=^PASS^&user_token=^TOKEN^" \
  --csrf-field user_token
```

The bundled mock target exposes `/csrf` (hidden field `user_token`, rotated every
request like DVWA's "high" level) so you can practice this safely. Drop
`--csrf-field` and the same run fails — proof the token is really required.

> Note: CSRF mode makes **two** requests per attempt (GET + POST), so it is
> roughly half the speed of a plain POST run.

## Success rules (`--rules`)

A candidate is a HIT only when **every** rule present passes:

- `status` — exact HTTP status code
- `regex` — pattern that must appear in the response body
- `not_contains` — substring that must **not** appear
- `body_len` — exact response body length

Tune these per target: pick something that appears on success but not on failure.
