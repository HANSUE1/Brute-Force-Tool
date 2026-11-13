import asyncio, random, re, http.cookiejar
import urllib.request, urllib.parse, urllib.error

UAS = ["Mozilla/5.0", "curl/8.0", "BruteForce/1.0"]


def extract_token(html, field):
    """Pull the value of a hidden <input name="FIELD" value="..."> from HTML.
    Tolerates attribute order (name before or after value) and quote style."""
    # Find the <input ...> tag that carries name="field", then read its value.
    tag = re.search(
        r"<input\b[^>]*\bname=['\"]%s['\"][^>]*>" % re.escape(field),
        html, re.IGNORECASE)
    if not tag:
        return None
    val = re.search(r"\bvalue=['\"]([^'\"]*)['\"]", tag.group(0), re.IGNORECASE)
    return val.group(1) if val else None


class HTTPProtocol:
    def __init__(self, url, proxies=None, success_rules=None, data_template=None,
                 csrf_field=None, csrf_url=None):
        self.url = url
        self.proxies = proxies or []
        self.rules = success_rules or {}
        self.data_template = data_template or ""
        self.csrf_field = csrf_field or ""
        self.csrf_url = csrf_url or ""

    def _build_body(self, user, password, token=None):
        if self.data_template:
            body = (self.data_template
                    .replace("^USER^", urllib.parse.quote_plus(user))
                    .replace("^PASS^", urllib.parse.quote_plus(password)))
            if token is not None:
                body = body.replace("^TOKEN^", urllib.parse.quote_plus(token))
            return body.encode()
        params = {"username": user, "password": password}
        if token is not None and self.csrf_field:
            params[self.csrf_field] = token
        return urllib.parse.urlencode(params).encode()

    def _opener(self):
        # A fresh cookie jar per attempt so the GET's session cookie rides along
        # to the POST, and concurrent attempts never share a session/token.
        handlers = [urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())]
        if self.proxies:
            proxy = random.choice(self.proxies)
            handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
        return urllib.request.build_opener(*handlers)

    async def try_password(self, user, password):
        loop = asyncio.get_event_loop()
        ua = random.choice(UAS)
        opener = self._opener()

        token = None
        if self.csrf_field:
            get_url = self.csrf_url or self.url
            get_req = urllib.request.Request(get_url, headers={"User-Agent": ua})
            try:
                page = await loop.run_in_executor(
                    None, lambda: opener.open(get_req, timeout=10).read().decode(errors="ignore"))
            except Exception as e:
                return False, f"csrf-get failed: {e}"
            token = extract_token(page, self.csrf_field)
            if token is None:
                return False, f"csrf token '{self.csrf_field}' not found on page"

        data = self._build_body(user, password, token)
        req = urllib.request.Request(self.url, data=data, headers={
            "User-Agent": ua,
            "Content-Type": "application/x-www-form-urlencoded",
        })
        try:
            resp = await loop.run_in_executor(None, lambda: opener.open(req, timeout=10))
            body = resp.read().decode(errors="ignore")
            status = resp.getcode()
        except urllib.error.HTTPError as e:
            # 4xx/5xx: keep the body so success rules can inspect error pages.
            body = e.read().decode(errors="ignore")
            status = e.code
        except Exception as e:
            return False, str(e)
        from .fingerprint import is_success
        ok = is_success(body, status, self.rules)
        return ok, body
