"""Polite offline mirror of one website section (Playwright-rendered).

Usage: python -I mirror.py OUT_DIR --start https://www.example.com/en [--scope /en] [--max-pages N] [--delay 1.0] [--fresh] [--report-only]

--start  first URL to crawl (required on the first run; saved in the state file for resuming)
--scope  path prefix to stay inside (default: the path of --start)
Only run after the user has approved crawling and its limits. Respects robots.txt,
waits --delay seconds between pages, skips tracker requests, resumes from _mirror_state.json.
Requires: pip install playwright requests beautifulsoup4 lxml && python -m playwright install chromium
"""
import csv, hashlib, html, json, mimetypes, os, posixpath, re, sys, time, traceback
import urllib.robotparser
from urllib.parse import urljoin, urlsplit, urlunsplit, unquote, parse_qsl, urlencode

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

_a = sys.argv[1:]
_cfg = os.path.join(os.path.abspath(_a[0]), "_mirror_config.json") if _a else ""
_saved = json.load(open(_cfg, encoding="utf-8")) if _cfg and os.path.exists(_cfg) else {}
START = (_a[_a.index("--start") + 1] if "--start" in _a else _saved.get("start", "")).rstrip("/")
if not START:
    sys.exit("Give --start URL (e.g. --start https://www.example.com/en)")
HOST = urlsplit(START).netloc.lower()
BARE = HOST[4:] if HOST.startswith("www.") else HOST
SCOPE = (_a[_a.index("--scope") + 1] if "--scope" in _a else _saved.get("scope", urlsplit(START).path)).rstrip("/")
DELAY = float(_a[_a.index("--delay") + 1]) if "--delay" in _a else 1.0
if _cfg:
    os.makedirs(os.path.dirname(_cfg), exist_ok=True)
    json.dump({"start": START, "scope": SCOPE}, open(_cfg, "w", encoding="utf-8"))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 offline-mirror"
TRACKERS = ("googletagmanager.com", "google-analytics.com", "analytics.google.com", "doubleclick.net",
            "facebook.net", "facebook.com/tr", "connect.facebook", "hotjar", "clarity.ms", "snap.licdn",
            "tiktok", "openweathermap.org", "googleadservices", "googlesyndication")
IMG_EXT = ("jpg", "jpeg", "png", "gif", "webp", "svg", "avif", "ico", "bmp")
WIN_BAD = re.compile(r'[<>:"\\|?*\x00-\x1f]')

args = sys.argv[1:]
OUT = os.path.abspath(args[0])
MAX_PAGES = int(args[args.index("--max-pages") + 1]) if "--max-pages" in args else 20000
FRESH = "--fresh" in args
REPORT_ONLY = "--report-only" in args
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "_mirror_log.txt"), "a", encoding="utf-8")


def log(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n"); LOG.flush()


# ---------------------------------------------------------------- networking
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "en"})
_last = {}
stats = {"requests": 0}


def throttle(url):
    h = urlsplit(url).netloc.lower()
    wait = _last.get(h, 0) + DELAY - time.time()
    if wait > 0:
        time.sleep(wait)
    _last[h] = time.time()
    stats["requests"] += 1


def fetch(url, **kw):
    throttle(url)
    return S.get(url, timeout=60, **kw)


robots = urllib.robotparser.RobotFileParser()
try:
    if REPORT_ONLY:
        raise RuntimeError("report-only mode: robots.txt not fetched")
    r = fetch(f"https://{HOST}/robots.txt")
    if r.status_code >= 400:
        robots.allow_all = True
        log(f"robots.txt -> HTTP {r.status_code}: no restrictions")
    else:
        robots.parse(r.text.splitlines())
        log("robots.txt parsed:\n" + r.text[:2000])
        cd = robots.crawl_delay(UA)
        if cd and cd > DELAY:
            DELAY = float(cd); log("using crawl-delay", DELAY)
except Exception as e:
    robots.allow_all = True
    log("robots.txt unreachable, assuming allow:", e)


def robots_ok(url):
    return robots.can_fetch(UA, url)


# ---------------------------------------------------------------- url helpers
def norm(url):
    """Normalize an in-scope page URL; return None if out of scope."""
    try:
        p = urlsplit(url)
    except ValueError:
        return None
    if p.scheme not in ("http", "https"):
        return None
    host = p.netloc.lower()
    if host not in (HOST, BARE):
        return None
    path = re.sub(r"/{2,}", "/", p.path or "/")
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    if not (path == SCOPE or path.startswith(SCOPE + "/")):
        return None
    q = urlencode(sorted(parse_qsl(p.query, keep_blank_values=True)))
    return urlunsplit(("https", HOST, path, q, ""))


def safe_seg(s, maxlen=80):
    s = WIN_BAD.sub("_", unquote(s)).strip(" .") or "_"
    if len(s) > maxlen:
        root, ext = os.path.splitext(s)
        s = root[: maxlen - 10 - len(ext)] + "_" + hashlib.md5(s.encode()).hexdigest()[:8] + ext
    return s


def page_local(url, ext=".html"):
    p = urlsplit(url)
    rel = p.path[len(SCOPE):].strip("/")
    segs = [safe_seg(s) for s in rel.split("/") if s] or ["index"]
    if p.query:
        segs[-1] += "__" + hashlib.md5(p.query.encode()).hexdigest()[:10]
    return "/".join(segs) + ext


def asset_local(url, ctype=""):
    p = urlsplit(url)
    segs = [safe_seg(s) for s in p.path.split("/") if s] or ["index"]
    root, ext = os.path.splitext(segs[-1])
    if not ext or len(ext) > 6:
        root = segs[-1]
        ext = mimetypes.guess_extension((ctype or "").split(";")[0].strip()) or ""
        ext = ".jpg" if ext == ".jpe" else ext
    if p.query:
        root += "__" + hashlib.md5(p.query.encode()).hexdigest()[:10]
    segs[-1] = root + ext
    return "/".join(["_assets", safe_seg(p.netloc.lower())] + segs)


def rel_from(from_local, to_local):
    return posixpath.relpath(to_local, posixpath.dirname(from_local) or ".")


def is_tracker(url):
    return any(t in url for t in TRACKERS)


# ---------------------------------------------------------------- state
STATE = os.path.join(OUT, "_mirror_state.json")
pages = {}          # url -> record
assets = {}         # url -> local rel path or None
failures = []       # dicts
queue = [norm(START)]
seen = {norm(START)}
if os.path.exists(STATE) and not FRESH:
    st = json.load(open(STATE, encoding="utf-8"))
    pages, assets, failures, queue, seen = st["pages"], st["assets"], st["failures"], st["queue"], set(st["seen"])
    bad = [u for u, r in pages.items() if r.get("error", "").startswith("HTTP")]
    for u in bad:
        del pages[u]; queue.append(u)
    failures = [f for f in failures if not (f["type"] == "page" and f["url"] in bad)]
    for f in [f for f in failures if f["type"] == "asset"]:
        assets.pop(f["url"], None)
    failures = [f for f in failures if f["type"] != "asset"]
    log(f"requeued {len(bad)} HTTP-error pages for retry")
    rescued = 0
    for u in list(queue):
        loc = page_local(u)
        fp = os.path.join(OUT, *loc.split("/"))
        if u not in pages and os.path.exists(fp) and os.path.getmtime(fp) > os.path.getmtime(STATE) - 600:
            t = re.search(r"<title>(.*?)</title>", open(fp, encoding="utf-8").read(), re.S)
            pages[u] = {"url": u, "final_url": u, "status": 200, "title": (t.group(1).strip() if t else ""),
                        "local_path": loc, "rendered": "yes", "error": ""}
            rescued += 1
    queue[:] = [u for u in queue if u not in pages]
    log(f"recovered {rescued} pages saved after the last checkpoint")
    log(f"resumed: {len(pages)} pages done, {len(queue)} queued, {len(assets)} assets")


def save_state():
    tmp = STATE + ".tmp"
    json.dump({"pages": pages, "assets": assets, "failures": failures, "queue": queue, "seen": sorted(seen)},
              open(tmp, "w", encoding="utf-8"))
    os.replace(tmp, STATE)


def fail(kind, url, err, ref=""):
    failures.append({"type": kind, "url": url, "error": str(err)[:300], "referrer": ref})
    log(f"  FAIL [{kind}] {url} :: {str(err)[:160]}")


def write_bytes(local, data):
    path = os.path.join(OUT, *local.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return path


# ---------------------------------------------------------------- assets
CSS_URL = re.compile(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""", re.I)
CSS_IMPORT = re.compile(r"""@import\s+(['"])([^'"]+)\1""", re.I)


def get_asset(url, ref="", depth=0):
    """Download an asset once; returns local rel path or None."""
    url = url.split("#")[0]
    if url in assets:
        return assets[url]
    if is_tracker(url) or not url.startswith(("http://", "https://")):
        assets[url] = None
        return None
    if urlsplit(url).netloc.lower() in (HOST, BARE) and not robots_ok(url):
        fail("asset-robots", url, "disallowed by robots.txt", ref); assets[url] = None; return None
    assets[url] = None  # guard against CSS import cycles
    try:
        r = fetch(url)
        if r.status_code >= 400:
            raise Exception(f"HTTP {r.status_code}")
        ctype = r.headers.get("Content-Type", "")
        local = asset_local(url, ctype)
        data = r.content
        if "css" in ctype or local.endswith(".css"):
            data = rewrite_css(r.text, url, local, depth).encode("utf-8")
        write_bytes(local, data)
        assets[url] = local
        return local
    except Exception as e:
        fail("asset", url, e, ref)
        return None


def rewrite_css(text, css_url, css_local, depth=0):
    def sub_url(m):
        raw = m.group(2).strip()
        if raw.startswith(("data:", "#", "about:")):
            return m.group(0)
        loc = get_asset(urljoin(css_url, html.unescape(raw)), css_url, depth + 1) if depth < 4 else None
        return f'url("{rel_from(css_local, loc)}")' if loc else f'url("{urljoin(css_url, raw)}")'

    def sub_imp(m):
        loc = get_asset(urljoin(css_url, m.group(2)), css_url, depth + 1) if depth < 4 else None
        return f'@import "{rel_from(css_local, loc)}"' if loc else f'@import "{urljoin(css_url, m.group(2))}"'

    text = CSS_IMPORT.sub(sub_imp, text)
    return CSS_URL.sub(sub_url, text)


# ---------------------------------------------------------------- html rewriting
_JS_HOST = re.escape(BARE).replace("/", r"\/")
_JS_SCOPE = SCOPE.replace("/", r"\/")
SHIM = (r"""<script data-mirror-shim>(function(){var d=%d,pre=d?Array(d+1).join('../'):'./';
function map(h){if(!h)return null;var m=h.match(/^(?:https?:\/\/(?:www\.)?""" + _JS_HOST.replace("%", "%%") + r""")?""" + _JS_SCOPE.replace("%", "%%") + r"""(\/[^?#]*)?(?:\?[^#]*)?(#.*)?$/i);if(!m)return null;
var p=(m[1]||'').replace(/^\/+|\/+$/g,'');return pre+(p?p:'index')+'.html'+(m[2]||'');}
document.addEventListener('click',function(e){var a=e.target&&e.target.closest?e.target.closest('a[href]'):null;if(!a)return;
var l=map(a.getAttribute('href'));if(l){e.preventDefault();if(a.target==='_blank')window.open(l);else location.href=l;}},true);})();</script>""")


def is_pdf(u):
    return urlsplit(u).path.lower().endswith(".pdf")


def rewrite_html(dom, page_url, local, discovered):
    soup = BeautifulSoup(dom, "lxml")
    for b in soup.find_all("base"):
        b.decompose()

    def res(u):
        return urljoin(page_url, html.unescape(u.strip()))

    def asset_rel(u):
        if not u or u.strip().startswith(("data:", "blob:", "javascript:", "#", "mailto:", "tel:")):
            return None
        loc = get_asset(res(u), page_url)
        return rel_from(local, loc) if loc else None

    def link_target(u):
        if not u or u.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
            return u
        absu = res(u)
        frag = urlsplit(absu).fragment
        n = norm(absu)
        if n:
            discovered.add(n)
            return rel_from(local, page_local(n)) + (("#" + frag) if frag else "")
        if is_pdf(absu):
            loc = get_asset(absu, page_url)
            if loc:
                return rel_from(local, loc)
        return absu

    for a in soup.find_all(["a", "area"], href=True):
        a["href"] = link_target(a["href"])
    for f in soup.find_all("form", action=True):
        f["action"] = res(f["action"])
    for s in soup.find_all("script", src=True):
        r = asset_rel(s["src"])
        s["src"] = r or res(s["src"])
    for l in soup.find_all("link", href=True):
        rel = " ".join(l.get("rel", [])).lower()
        if any(k in rel for k in ("stylesheet", "icon", "preload", "apple-touch")):
            r = asset_rel(l["href"])
            l["href"] = r or res(l["href"])
        elif "canonical" in rel or "alternate" in rel:
            l["href"] = res(l["href"])
    for t in soup.find_all(["script", "link"]):
        for at in ("integrity", "crossorigin"):
            if t.has_attr(at):
                del t[at]
    for t in soup.find_all(["img", "source", "video", "audio", "iframe", "embed", "track", "input"]):
        for at in ("src", "data-src", "data-lazy", "data-original", "poster", "data-bg", "data-background"):
            if t.has_attr(at) and t.name != "iframe":
                r = asset_rel(t[at])
                if r:
                    t[at] = r
        for at in ("srcset", "data-srcset"):
            if t.has_attr(at):
                parts = []
                for item in t[at].split(","):
                    bits = item.strip().split()
                    if not bits:
                        continue
                    r = asset_rel(bits[0])
                    parts.append(" ".join([r or res(bits[0])] + bits[1:]))
                t[at] = ", ".join(parts)
        if t.name == "iframe" and t.has_attr("src"):
            t["src"] = res(t["src"])
    # catch-all: any attribute that is an image URL, inline style url(), <style> blocks
    for t in soup.find_all(True):
        for at, v in list(t.attrs.items()):
            if not isinstance(v, str):
                continue
            if at == "style" and "url(" in v:
                t[at] = CSS_URL.sub(lambda m: f"url('{asset_rel(m.group(2)) or res(m.group(2))}')"
                                    if not m.group(2).startswith("data:") else m.group(0), v)
            elif at.startswith("data-") and re.match(r"^(https?://|/)[^\s]+\.(%s)(\?\S*)?$" % "|".join(IMG_EXT), v, re.I):
                r = asset_rel(v)
                if r:
                    t[at] = r
    for st in soup.find_all("style"):
        if st.string and "url(" in st.string:
            st.string = CSS_URL.sub(lambda m: m.group(0) if m.group(2).startswith("data:")
                                    else f"url('{asset_rel(m.group(2)) or res(m.group(2))}')", st.string)

    depth = local.count("/")
    head = soup.head or soup
    if not soup.find("meta", charset=True):
        m = soup.new_tag("meta", charset="utf-8"); head.insert(0, m)
    head.insert(1, BeautifulSoup(SHIM % depth, "lxml").find("script"))
    head.insert(1, soup.new_tag("meta", attrs={"name": "mirror-source", "content": page_url}))
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    hd = next((h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2"]) if h.get_text(strip=True)), "")
    return str(soup), title, hd[:150]


UID_RE = re.compile(r'"uid"\s*:\s*"([0-9a-f]{24})"')
DETAIL_RE = re.compile(r"^%s/([^/]+)/([0-9a-f]{24})$" % re.escape(SCOPE))
RAW_URL_RE = re.compile(r"""(?:https?://(?:www\.)?""" + re.escape(BARE) + r""")?(""" + re.escape(SCOPE) + r"""(?:/[A-Za-z0-9_\-./%]*)?)(?=["'\s<>?#)])""")


def discover_from_raw(raw, page_url, rendered_links):
    """Extra URLs from the server HTML: literal paths + inline JSON uid lists."""
    out = set()
    text = html.unescape(raw)
    for m in RAW_URL_RE.finditer(text):
        path = m.group(1)
        if re.search(r"\.(js|css|png|jpe?g|gif|svg|webp|woff2?|ttf|ico)$", path, re.I):
            continue
        n = norm(urljoin(page_url, path))
        if n:
            out.add(n)
    segs = {DETAIL_RE.match(urlsplit(u).path).group(1) for u in rendered_links if DETAIL_RE.match(urlsplit(u).path)}
    if segs:
        uids = set(UID_RE.findall(text))
        for seg in segs:
            for uid in uids:
                out.add(norm(f"https://{HOST}{SCOPE}/{seg}/{uid}"))
    return out


# ---------------------------------------------------------------- crawl
retries = {}
streak = {"n": 0, "last_ok": None}


def check_throttled():
    """After repeated page errors, probe the start page; back off if the site is refusing us."""
    global DELAY
    try:
        code = fetch(streak["last_ok"] or norm(START)).status_code
    except Exception as e:
        code = str(e)
    if code == 200:
        log("  canary OK -> errors look genuine")
        return
    DELAY = min(DELAY + 0.5, 3.0)
    log(f"  canary got {code}: site is throttling; pausing 90s, delay now {DELAY}s")
    time.sleep(90)


def crawl():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(user_agent=UA, viewport={"width": 1366, "height": 900}, locale="en-US")
        cur = {}

        def handler(route):
            req = route.request
            url, rt = req.url, req.resource_type
            try:
                if is_tracker(url):
                    return route.abort()
                if rt == "document":
                    if req.frame != cur["page"].main_frame or url.split("#")[0] != cur["url"]:
                        return route.abort()
                    r = fetch(url)
                    cur["status"], cur["final"], cur["raw"] = r.status_code, r.url, r.text
                    cur["ctype"] = r.headers.get("Content-Type", "")
                    cur["bytes"] = r.content
                    hdrs = {"content-type": r.headers.get("Content-Type", "text/html")}
                    return route.fulfill(status=r.status_code, headers=hdrs, body=r.content)
                if rt in ("script", "stylesheet"):
                    if "/_assets/" in url:   # relative refs inside already-rewritten CSS
                        return route.abort()
                    loc = get_asset(url, cur["url"])
                    if not loc:
                        return route.abort()
                    return route.fulfill(status=200, path=os.path.join(OUT, *loc.split("/")),
                                         content_type="text/css" if rt == "stylesheet" else "application/javascript")
                if rt in ("xhr", "fetch") and urlsplit(url).netloc.lower() in (HOST, BARE):
                    r = fetch(url)
                    return route.fulfill(status=r.status_code, body=r.content,
                                         headers={"content-type": r.headers.get("Content-Type", "")})
                return route.abort()   # images/fonts/media downloaded from the DOM instead
            except Exception as e:
                try:
                    route.abort()
                except Exception:
                    pass
                log("  route error", url, e)

        ctx.route("**/*", handler)
        page = ctx.new_page()
        cur["page"] = page
        n = 0
        while queue and len(pages) < MAX_PAGES:
            url = queue.pop(0)
            if url in pages:
                continue
            n += 1
            local = page_local(url)
            rec = {"url": url, "final_url": "", "status": "", "title": "", "local_path": "", "rendered": "", "error": ""}
            if not robots_ok(url):
                rec["error"] = "disallowed by robots.txt"; pages[url] = rec; fail("page-robots", url, rec["error"]); continue
            cur.update(url=url, status=None, final=None, raw="", ctype="", bytes=b"")
            log(f"[{len(pages)+1} done, {len(queue)} queued] {url}")
            try:
                try:
                    page.goto(url, wait_until="load", timeout=180000)
                    try:
                        page.wait_for_load_state("networkidle", timeout=8000)
                    except Exception:
                        pass
                    page.wait_for_timeout(800)
                except Exception as e:
                    if cur["status"] is None:
                        raise
                    log("  goto warning:", str(e)[:120])
                rec["status"], rec["final_url"] = cur["status"], cur["final"]
                fin = norm(cur["final"] or url)
                if cur["final"] and not fin:
                    rec["error"] = f"redirected out of scope -> {cur['final']}"
                    pages[url] = rec; fail("page-redirect", url, rec["error"]); continue
                if fin and fin != url:
                    seen.add(fin)
                if cur["status"] >= 400:
                    raise Exception(f"HTTP {cur['status']}")
                if "html" not in cur["ctype"]:
                    # non-HTML document in scope (e.g. a PDF)
                    loc = page_local(url, os.path.splitext(urlsplit(url).path)[1] or
                                     (mimetypes.guess_extension(cur["ctype"].split(";")[0]) or ".bin"))
                    write_bytes(loc, cur["bytes"])
                    rec.update(local_path=loc, title=os.path.basename(loc), rendered="no")
                    pages[url] = rec; continue
                dom = page.content()
                links = set()
                for h in page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)"):
                    nn = norm(h.split("#")[0])
                    if nn:
                        links.add(nn)
                found = set(links) | discover_from_raw(cur["raw"], url, links)
                out_html, title, heading = rewrite_html(dom, cur["final"] or url, local, found)
                write_bytes(local, out_html.encode("utf-8"))
                rec.update(title=title, heading=heading, local_path=local, rendered="yes")
                new = 0
                for u in sorted(found):
                    if u and u not in seen:
                        seen.add(u); queue.append(u); new += 1
                log(f"  ok {cur['status']} '{title[:60]}' -> {local} (+{new} new)")
            except Exception as e:
                err = str(e)[:300]
                streak["n"] += 1
                if streak["n"] >= 3:
                    streak["n"] = 0
                    check_throttled()
                if err.startswith("HTTP") and retries.get(url, 0) < 3:
                    retries[url] = retries.get(url, 0) + 1
                    queue.append(url)
                    log(f"  HTTP error {err}; will retry later (attempt {retries[url]})")
                    continue
                rec["error"] = err
                fail("page", url, e)
            else:
                streak["n"] = 0
                if rec.get("local_path", "").endswith(".html") and "/" in rec["local_path"]:
                    streak["last_ok"] = url
            pages[url] = rec
            if n % 20 == 0:
                save_state()
        save_state()
        browser.close()


def page_name(local):
    """Human label: breadcrumb trail + item name (e.g. 'Shops > Foot Locker')."""
    try:
        s = BeautifulSoup(open(os.path.join(OUT, *local.split("/")), encoding="utf-8").read(), "lxml")
        for t in s.select("nav, header, footer, .menu-dropdown, .mobile-menu, script, style, noscript"):
            t.decompose()
        x = [t for t in s.body.stripped_strings][:6] if s.body else []
        if x[:1] == ["/"]:
            x = x[1:]
        return " > ".join(x[:2])[:150]
    except Exception:
        return ""


def write_reports():
    with open(os.path.join(OUT, "pages.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["url", "title", "page_name", "local_path", "http_status", "final_url", "rendered_with_playwright", "error"])
        for r in sorted(pages.values(), key=lambda r: r["url"]):
            w.writerow([r["url"], r["title"], page_name(r["local_path"]) if r["local_path"].endswith(".html") else "", r["local_path"].replace("/", "\\") if r["local_path"] else "",
                        r["status"], r["final_url"], r["rendered"], r["error"]])
    with open(os.path.join(OUT, "failures.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["type", "url", "error", "referrer"])
        for x in failures:
            w.writerow([x["type"], x["url"], x["error"], x["referrer"]])
    ok = sum(1 for r in pages.values() if r["local_path"])
    na = sum(1 for v in assets.values() if v)
    with open(os.path.join(OUT, "remaining_queue.txt"), "w", encoding="utf-8") as f:
        f.write(chr(10).join(queue))
    log(f"{'REPORT' if REPORT_ONLY else 'DONE'} pages ok={ok}/{len(pages)} assets ok={na}/{len(assets)} failures={len(failures)} "
        f"queue_left={len(queue)} requests={stats['requests']}")


if __name__ == "__main__":
    try:
        if not REPORT_ONLY:
            crawl()
    except KeyboardInterrupt:
        log("interrupted; saving state")
    except Exception:
        log("CRASH\n" + traceback.format_exc())
    finally:
        save_state()
        write_reports()
