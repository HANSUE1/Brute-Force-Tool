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
| `--rules` | — | JSON success-detection rules (see `configs/rules.json`). |
| `--threads` | 4 | Concurrent workers. |
| `--rps` | 10 | Per-worker rate limit (requests/sec). |
| `--proxies` | — | Comma-separated proxy URLs, rotated per request. |
| `--output` | `hits.txt` | Where successful candidates are written. |
| `--state` | `session.state` | Checkpoint file; a re-run resumes from it. |

## Success rules (`--rules`)

A candidate is a HIT only when **every** rule present passes:

- `status` — exact HTTP status code
- `regex` — pattern that must appear in the response body
- `not_contains` — substring that must **not** appear
- `body_len` — exact response body length

Tune these per target: pick something that appears on success but not on failure.
