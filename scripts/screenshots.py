"""Screenshots for the benchmark (Playwright + Pillow).

Usage:
  python -I screenshots.py pages OUT_DIR name=URL [name=URL ...] [--mobile] [--desktop-only]
      Full-page captures at 1440x900 (and 390x844 unless --desktop-only). Scrolls first so lazy images load.
  python -I screenshots.py components OUT_DIR jobs.json
      jobs.json: [{"key": "n1_1", "url": "...", "anchor": "optional heading text"}]
      Opens each page, tries "Reject all"/"Decline" cookie buttons (never Accept), presses Escape for popups,
      scrolls the anchor heading to the top and takes a 1280x800 viewport shot. Never clicks CAPTCHAs:
      pages showing a human-check are reported as "blocked".
  python -I screenshots.py split IMAGE [--step 1800]
      Cuts a tall full-page capture into readable chunks (IMAGE_p0.jpg, _p1 ...).
  python -I screenshots.py crop IMAGE x0 y0 x1 y1 OUT [--width 1200]
  python -I screenshots.py sheet OUT.jpg IMG [IMG ...]
      Labelled contact sheet (3 columns) for quick visual review.

Requires: pip install playwright pillow && python -m playwright install chromium
"""
import sys, os, json, asyncio

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
DECLINE = ["Reject all", "Reject All", "Decline all", "Decline", "Reject", "Only necessary", "Necessary only"]
HUMAN_CHECK = ["verify you are human", "i'm not a robot", "checking your browser", "are you a robot"]


def pages(out, items, desktop_only=False):
    from playwright.sync_api import sync_playwright
    os.makedirs(out, exist_ok=True)
    vps = [({"width": 1440, "height": 900}, "d")] + ([] if desktop_only else [({"width": 390, "height": 844}, "m")])
    with sync_playwright() as p:
        b = p.chromium.launch()
        for vp, tag in vps:
            ctx = b.new_context(viewport=vp, is_mobile=(tag == "m"), user_agent=UA)
            for it in items:
                name, url = it.split("=", 1)
                pg = ctx.new_page()
                try:
                    pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(5000)
                    h = pg.evaluate("document.body.scrollHeight")
                    for y in range(0, h, 800): pg.evaluate(f"scrollTo(0,{y})"); pg.wait_for_timeout(200)
                    pg.evaluate("scrollTo(0,0)"); pg.wait_for_timeout(800)
                    pg.screenshot(path=f"{out}/{name}_{tag}.jpg", full_page=True, type="jpeg", quality=60)
                    print("ok", name, tag, h)
                except Exception as e:
                    print("fail", name, tag, str(e)[:120])
                pg.close()
            ctx.close()
        b.close()


async def _component(b, sem, out, job):
    async with sem:
        ctx = await b.new_context(viewport={"width": 1280, "height": 800}, user_agent=UA)
        pg = await ctx.new_page(); status = "ok"
        try:
            await pg.goto(job["url"], wait_until="domcontentloaded", timeout=45000); await pg.wait_for_timeout(4500)
            body = (await pg.inner_text("body"))[:4000].lower()
            if any(h in body for h in HUMAN_CHECK):
                status = "blocked (human check: ask the user to open it)"
            else:
                for t in DECLINE:
                    try:
                        btn = pg.get_by_role("button", name=t, exact=True)
                        if await btn.count(): await btn.first.click(timeout=1500); break
                    except Exception: pass
                await pg.keyboard.press("Escape"); await pg.wait_for_timeout(400)
                if job.get("anchor"):
                    loc = pg.locator("h1,h2,h3,h4,h5,h6").filter(has_text=job["anchor"])
                    if not await loc.count(): loc = pg.get_by_text(job["anchor"], exact=False)
                    if await loc.count():
                        await loc.first.scroll_into_view_if_needed(timeout=5000)
                        await pg.evaluate("window.scrollBy(0,-40)"); await pg.wait_for_timeout(3000)
                    else: status = "anchor not found (shot shows top of page)"
                await pg.screenshot(path=f"{out}/{job['key']}.jpg", type="jpeg", quality=62)
        except Exception as e:
            status = "fail " + str(e)[:100]
        await ctx.close(); print(job["key"], status, job["url"], flush=True)


async def components(out, jobs):
    from playwright.async_api import async_playwright
    os.makedirs(out, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(); sem = asyncio.Semaphore(5)
        await asyncio.gather(*[_component(b, sem, out, j) for j in jobs]); await b.close()


def split(img, step=1800):
    from PIL import Image
    im = Image.open(img); w, h = im.size; base = os.path.splitext(img)[0]
    for i, y in enumerate(range(0, h, step)):
        im.crop((0, y, w, min(h, y + step))).save(f"{base}_p{i}.jpg", quality=62); print(f"{base}_p{i}.jpg")


def crop(img, box, out, width=1200):
    from PIL import Image
    im = Image.open(img).crop(box)
    if im.width > width: im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    im.convert("RGB").save(out, quality=72, optimize=True); print(out)


def sheet(out, imgs, W=480, H=300):
    from PIL import Image, ImageDraw
    rows = (len(imgs) + 2) // 3; sh = Image.new("RGB", (W * 3, H * rows), "white"); d = ImageDraw.Draw(sh)
    for i, f in enumerate(imgs):
        x, y = (i % 3) * W, (i // 3) * H
        try: sh.paste(Image.open(f).convert("RGB").resize((W, H)), (x, y))
        except Exception: pass
        d.rectangle((x, y, x + 150, y + 20), fill="black"); d.text((x + 4, y + 4), os.path.basename(f)[:24], fill="yellow")
    sh.save(out, quality=70); print(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(1)
    if a[0] == "pages": pages(a[1], [x for x in a[2:] if "=" in x], desktop_only="--desktop-only" in a)
    elif a[0] == "components": asyncio.run(components(a[1], json.load(open(a[2], encoding="utf-8"))))
    elif a[0] == "split": split(a[1], int(a[a.index("--step") + 1]) if "--step" in a else 1800)
    elif a[0] == "crop": crop(a[1], tuple(map(int, a[2:6])), a[6], int(a[a.index("--width") + 1]) if "--width" in a else 1200)
    elif a[0] == "sheet": sheet(a[1], a[2:])
    else: print(__doc__)
