"""Make a published artifact page into a standalone HTML file with images embedded.

Usage: python -I export_standalone.py PAGE.html OUT.html [--root DIR]

- Replaces src="relative/path.jpg|png|webp|svg" with data: URIs (relative to --root, default the page folder).
- Also replaces image paths written inside <script> strings, e.g. "img/n1_1.jpg".
- If the page has no <!doctype>, wraps it in a full document (charset, viewport, base reset),
  moving <title>/<style>/<link> into <head>.
Google Fonts links are kept; offline, the page falls back to system fonts.
"""
import sys, os, re, base64, mimetypes

MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".svg": "image/svg+xml", ".gif": "image/gif", ".avif": "image/avif"}


def data_uri(path):
    ext = os.path.splitext(path)[1].lower()
    return f"data:{MIME.get(ext, mimetypes.guess_type(path)[0] or 'application/octet-stream')};base64," + base64.b64encode(open(path, "rb").read()).decode()


def main():
    a = sys.argv[1:]; page, out = a[0], a[1]
    root = a[a.index("--root") + 1] if "--root" in a else os.path.dirname(os.path.abspath(page))
    s = open(page, encoding="utf-8").read()
    missing = []

    def rep(m):
        rel = m.group(2)
        if rel.startswith(("data:", "http:", "https:", "//")) or "${" in rel: return m.group(0)
        p = os.path.join(root, rel)
        if os.path.isfile(p): return m.group(1) + data_uri(p) + m.group(3)
        missing.append(rel); return m.group(0)

    s = re.sub(r'((?:src|href)=")([^"]+\.(?:jpe?g|png|webp|svg|gif|avif))(")', rep, s, flags=re.I)
    s = re.sub(r'(["\'])((?:[\w-]+/)+[\w.-]+\.(?:jpe?g|png|webp|svg|gif|avif))(["\'])', rep, s, flags=re.I)
    if not re.match(r"\s*<!doctype", s, re.I):
        head_bits = "".join(re.findall(r"<title>.*?</title>|<link[^>]*>|<style>.*?</style>", s, re.S))
        body = re.sub(r"<title>.*?</title>|<link[^>]*>|<style>.*?</style>", "", s, flags=re.S)
        s = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
             '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
             '<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
             + head_bits + "\n</head>\n<body>\n" + body + "\n</body>\n</html>\n")
    open(out, "w", encoding="utf-8").write(s)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB)" + (f"; missing: {missing[:10]}" if missing else ""))


if __name__ == "__main__":
    main()
