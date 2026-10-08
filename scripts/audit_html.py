"""SEO, accessibility and asset audit for a crawled folder or a list of URLs.

Usage:
  python -I audit_html.py folder PATH [--json out.json]
  python -I audit_html.py urls URL [URL ...] [--json out.json]

Reports: duplicate/missing titles, missing meta descriptions, images without alt,
H1 distribution, Open Graph / hreflang / JSON-LD presence, analytics tags
(flags dead Universal Analytics), front-end libraries and versions, lazy loading,
and (folder mode) the heaviest images and format mix.
Standard library only.
"""
import sys, os, re, json, glob, collections, urllib.request

LIBS = [("bootstrap", r"bootstrap@?([\d.]+)"), ("jquery", r"jquery[-.@]?([\d.]+)"), ("swiper", r"swiper@?([\d.]+)"),
        ("tailwind", r"tailwind(?:css)?@?([\d.]+)"), ("react", r"react(?:-dom)?@?([\d.]+)"), ("vue", r"vue@?([\d.]+)"),
        ("next.js", r"/_next/()"), ("wordpress", r"wp-content()"), ("drupal", r"/sites/default/files()"),
        ("aem", r"/etc\.clientlibs/()"), ("webflow", r"webflow()"), ("font-awesome", r"font-?awesome[^\"']*?([\d.]+)?")]
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".svg", ".jfif")


def audit_pages(pages):
    """pages: list of (name, html)"""
    titles = collections.Counter()
    r = dict(pages=len(pages), no_meta_desc=0, imgs=0, imgs_no_alt=0, lazy_imgs=0, h1=collections.Counter(),
             og=0, hreflang=0, jsonld=0, canonical=0, analytics=collections.Counter(), libs=collections.Counter(),
             lang_attrs=collections.Counter(), rtl_pages=0)
    for name, s in pages:
        t = re.search(r"<title[^>]*>(.*?)</title>", s, re.S | re.I)
        titles[(t.group(1).strip() if t else "(missing)")] += 1
        if not re.search(r'<meta[^>]+name=["\']description["\']', s, re.I): r["no_meta_desc"] += 1
        for m in re.finditer(r"<img\b[^>]*>", s, re.I):
            r["imgs"] += 1
            a = re.search(r'alt=["\']([^"\']*)["\']', m.group(0))
            if not a or not a.group(1).strip(): r["imgs_no_alt"] += 1
            if 'loading="lazy"' in m.group(0): r["lazy_imgs"] += 1
        r["h1"][len(re.findall(r"<h1\b", s, re.I))] += 1
        r["og"] += bool(re.search(r'property=["\']og:', s))
        r["hreflang"] += bool(re.search(r"hreflang=", s))
        r["jsonld"] += bool(re.search(r"application/ld\+json", s))
        r["canonical"] += bool(re.search(r'rel=["\']canonical', s))
        for tag in re.findall(r"\b(UA-\d+-\d+|G-[A-Z0-9]{6,}|GTM-[A-Z0-9]+)", s): r["analytics"][tag] += 1
        for lib, pat in LIBS:
            m = re.search(pat, s, re.I)
            if m: r["libs"][f"{lib} {m.group(1) or ''}".strip()] += 1
        h = re.search(r"<html[^>]*>", s, re.I)
        if h:
            lg = re.search(r'lang=["\']([^"\']+)', h.group(0)); r["lang_attrs"][lg.group(1) if lg else "(none)"] += 1
            r["rtl_pages"] += 'dir="rtl"' in h.group(0).lower()
    r["unique_titles"] = len(titles)
    r["top_titles"] = titles.most_common(5)
    r["h1"] = dict(r["h1"]); r["analytics"] = dict(r["analytics"]); r["libs"] = dict(r["libs"].most_common(15))
    r["lang_attrs"] = dict(r["lang_attrs"])
    r["flags"] = []
    if r["unique_titles"] < max(1, r["pages"] // 2): r["flags"].append(f"Only {r['unique_titles']} unique titles across {r['pages']} pages")
    if r["no_meta_desc"]: r["flags"].append(f"{r['no_meta_desc']} pages without meta description")
    if r["imgs"] and r["imgs_no_alt"] / r["imgs"] > .2: r["flags"].append(f"{r['imgs_no_alt']}/{r['imgs']} images missing alt ({100*r['imgs_no_alt']//r['imgs']}%)")
    if any(k.startswith("UA-") for k in r["analytics"]): r["flags"].append("Universal Analytics (UA-) tag found: Google stopped processing UA data in July 2023")
    for k in ("og", "hreflang", "jsonld"):
        if r[k] == 0: r["flags"].append(f"No {k} on any page")
    bad_h1 = sum(v for k, v in r["h1"].items() if k != 1)
    if bad_h1: r["flags"].append(f"{bad_h1} pages do not have exactly one H1")
    return r


def folder_assets(root):
    sizes, fmt = [], collections.Counter()
    for f in glob.glob(os.path.join(root, "**", "*"), recursive=True):
        if f.lower().endswith(IMG_EXT) and os.path.isfile(f):
            sz = os.path.getsize(f); sizes.append((sz, os.path.relpath(f, root))); fmt[os.path.splitext(f)[1].lower()] += 1
    sizes.sort(reverse=True)
    return dict(image_count=len(sizes), image_mb=round(sum(s for s, _ in sizes) / 1e6, 1), formats=dict(fmt),
                heaviest=[(round(s / 1e6, 2), p) for s, p in sizes[:12]])


def main():
    a = sys.argv[1:]
    out = a[a.index("--json") + 1] if "--json" in a else None
    if "--json" in a: i = a.index("--json"); a = a[:i] + a[i + 2:]
    mode, rest = a[0], a[1:]
    if mode == "folder":
        root = rest[0]
        files = [f for f in glob.glob(os.path.join(root, "**", "*.html"), recursive=True) if "_assets" not in f]
        pages = [(os.path.relpath(f, root), open(f, encoding="utf-8", errors="ignore").read()) for f in files]
        res = audit_pages(pages); res["assets"] = folder_assets(root)
    else:
        pages = []
        for u in rest:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (website-benchmark audit)"})
            try: pages.append((u, urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")))
            except Exception as e: print("fetch failed", u, e, file=sys.stderr)
        res = audit_pages(pages)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    if out: json.dump(res, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
