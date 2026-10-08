"""Re-verify UI resource sites before building the resource directory.

Usage: python -I check_sources.py ../references/ui-sources.json [--out checked.json]

For each source: site HTTP status, llms.txt (real text vs HTML fallback), GitHub repo
(stars, licence, last push), and repo files that indicate agent skills (SKILL.md),
MCP docs or llms.txt. Uses the `gh` CLI if logged in (higher rate limit), otherwise
the public GitHub API. Commands in the JSON are only kept if they came from the
resource's own docs or repo: re-confirm any command whose evidence is missing.
Status 403 usually means bot protection, not a dead site: report it as "unverified".
"""
import sys, json, subprocess, urllib.request, urllib.error, shutil

UA = {"User-Agent": "Mozilla/5.0 (website-benchmark source check)"}


def http(url, n=300):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20)
        return r.status, r.read(n).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e: return e.code, ""
    except Exception as e: return 0, str(e)[:80]


def gh_json(path):
    if shutil.which("gh"):
        p = subprocess.run(["gh", "api", path], capture_output=True, text=True, encoding="utf-8")
        if p.returncode == 0: return json.loads(p.stdout)
    try:
        return json.loads(urllib.request.urlopen(urllib.request.Request("https://api.github.com/" + path, headers=UA), timeout=20).read())
    except Exception: return None


def main():
    src = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    for s in src:
        st, _ = http(s["url"]); s["site_status"] = st
        if s.get("llms"):
            code, body = http(s["llms"]); s["llms_ok"] = code == 200 and not body.lstrip().lower().startswith("<!doctype")
        if s.get("repo"):
            r = gh_json(f"repos/{s['repo']}")
            if r:
                s["stars"] = r.get("stargazers_count"); s["licence_spdx"] = (r.get("license") or {}).get("spdx_id")
                s["pushed"] = (r.get("pushed_at") or "")[:10]
                t = gh_json(f"repos/{s['repo']}/git/trees/HEAD?recursive=1") or {}
                paths = [x["path"] for x in t.get("tree", [])]
                s["repo_skill_files"] = [p for p in paths if p.endswith("SKILL.md") and not p.startswith(".agents/")][:5]
                s["repo_mcp_files"] = [p for p in paths if "mcp" in p.lower() and "node_modules" not in p][:5]
            else: s["repo_error"] = "not found or rate-limited"
        flag = "OK" if s["site_status"] == 200 else ("UNVERIFIED (bot protection?)" if s["site_status"] == 403 else "DOWN?")
        print(f"{s['name']:<24} site={s['site_status']} {flag} stars={s.get('stars','-')} llms={s.get('llms_ok','-')} "
              f"skills={len(s.get('repo_skill_files',[]))} mcp={len(s.get('repo_mcp_files',[]))}")
    if out: json.dump(src, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
