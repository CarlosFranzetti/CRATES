"""Crates feature tests (Playwright + system Chromium).

Run:  python3 /home/claude/crates/tests/test_crates.py
Writes results.json and shots/*.png next to this file.
External requests (Google Fonts, YouTube) are aborted so the player
falls back to link mode deterministically; one test makes the YouTube
API hang to exercise the 6 s timeout path instead.
"""
import functools, http.server, json, re, sys, threading, time, traceback
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_harness import build  # noqa: E402

CHROME = "/opt/google/chrome/chrome"
SHOTS = HERE / "shots"; SHOTS.mkdir(exist_ok=True)
NET_ERR = re.compile(r"Failed to load resource|net::ERR_|ERR_FAILED|ERR_ABORTED", re.I)


class Fail(AssertionError):
    pass


def check(cond, msg):
    if not cond:
        raise Fail(msg)


# ---------------------------------------------------------------- server
def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    h.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/harness.html"


# ---------------------------------------------------------------- page wrapper
class App:
    def __init__(self, browser, url, width=1280, height=900, scheme="light", yt="abort"):
        self.ctx = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme)
        self.page = self.ctx.new_page()
        self.url = url
        self.errors, self.console = [], []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        self.page.on("console", lambda m: m.type == "error" and self.console.append(m.text))

        def route(r):
            u = r.request.url
            if u.startswith("http://127.0.0.1"):
                return r.continue_()
            if yt == "hang" and "youtube.com/iframe_api" in u:
                return  # never answer: exercises the 6s timeout path
            return r.abort()
        self.ctx.route("**/*", route)
        wu = "domcontentloaded" if yt == "hang" else "load"
        self.page.goto(url, wait_until=wu)
        self.page.evaluate("localStorage.clear()")
        self.page.reload(wait_until=wu)
        self.page.wait_for_selector("#main .unit-card")

    # helpers
    def ev(self, js, arg=None):
        return self.page.evaluate(js, arg) if arg is not None else self.page.evaluate(js)

    def click(self, sel, **kw):
        self.page.locator(sel).first.click(**kw)

    def counter(self):
        return self.page.locator(".dig > .row span.code").first.inner_text().strip()

    def title(self):
        return self.page.locator(".dig-info h3").first.inner_text().strip()

    def toast(self):
        t = self.page.locator(".toast span").first
        t.wait_for(timeout=3000)
        return t.inner_text().strip()

    def undo(self):
        self.click(".toast button[data-act=undo]")

    def chip_count(self, label):
        txt = self.page.locator(f".chips .chip:has-text('{label}') small").first.inner_text()
        return int(txt)

    def loc(self, rid):
        return self.ev(f"(()=>{{const r=rec('{rid}');return r.loc.u+':'+r.loc.c}})()")

    def unit_counts(self):
        return self.ev("Object.fromEntries(S.units.map(u=>[u.id,inCell(u.id,'all').length]))")

    def wait_link_mode(self, timeout=8000):
        self.page.wait_for_function("P.mode==='link'", timeout=timeout)

    def js_errors(self):
        return self.errors + [c for c in self.console if not NET_ERR.search(c)]

    def close(self):
        self.ctx.close()


# ---------------------------------------------------------------- tests
def t01_boot(a):
    check(a.page.locator(".detail h2").inner_text().strip().lower() == "kallax 1", "K1 detail not open")
    check(a.ev("V.cell") == "0-0", "not on cubby A1")
    check(a.counter() == "1 of 5", f"counter={a.counter()}")
    check(a.page.locator(".list .li").count() == 5, "list != 5")
    check(a.page.locator(".chips .chip[aria-pressed=true]").inner_text().startswith("A1"), "A1 chip not pressed")
    check(a.page.locator("#player").is_visible(), "mini player hidden")
    t0 = time.time(); a.wait_link_mode(); dt = time.time() - t0
    href = a.page.locator("#player a.round.main").get_attribute("href")
    check(href and "youtube.com/watch" in href, f"play button not a YouTube link: {href}")
    check(a.ev("S.units.find(u=>u.id==='K1').rows===2 && S.units.find(u=>u.id==='K1').cols===4"), "K1 not 2x4")
    check(not a.js_errors(), f"console/page errors: {a.js_errors()}")
    return f"link mode after {dt:.1f}s; K1 preset={a.ev('S.units[0].preset')}"


def t02_search(a):
    q = a.page.locator("#q")
    q.fill("voodoo")
    first = a.page.locator("#results .result").first
    check("Voodoo Ray" in first.inner_text(), "Voodoo not first result")
    check(first.locator(".loc").inner_text().strip() == "Crater", f"chip={first.locator('.loc').inner_text()}")
    q.press("Enter")
    check(a.page.locator(".detail h2").inner_text().strip().lower() == "crater", "bag view not opened")
    check(a.title() == "Voodoo Ray", f"focused on {a.title()}")
    check(a.page.locator("#q").input_value() == "", "query not cleared")
    q.fill("acid")
    n = a.page.locator("#results .result[data-act=goto-rec]").count()
    check(n >= 2, f"acid results={n}")
    q.press("ArrowDown"); q.press("Enter")
    second_ok = a.title() != ""
    q.fill("zzz")
    check("No match" in a.page.locator("#results").inner_text(), "no-match message missing")
    q.press("Enter")  # must not throw
    q.fill("kallax")
    check(a.page.locator("#results .result[data-act=open-unit]").count() >= 1, "unit hit missing")
    return f"acid -> {n} results; ArrowDown+Enter ok={second_ok}"


def t03_flip(a):
    check(a.counter() == "1 of 5", a.counter())
    check(a.page.locator("[data-act=dig][data-d='-1']").is_disabled(), "prev enabled at 1")
    a.click("[data-act=dig][data-d='1']"); check(a.counter() == "2 of 5", a.counter())
    a.click("[data-act=dig][data-d='-1']"); check(a.counter() == "1 of 5", a.counter())
    a.page.locator("body").click(position={"x": 2, "y": 300})
    a.page.keyboard.press("ArrowRight"); check(a.counter() == "2 of 5", "ArrowRight " + a.counter())
    a.page.keyboard.press("ArrowRight"); a.page.keyboard.press("ArrowLeft"); check(a.counter() == "2 of 5", a.counter())
    a.page.keyboard.press("ArrowLeft"); check(a.counter() == "1 of 5", a.counter())
    for _ in range(6): a.page.keyboard.press("ArrowRight")
    check(a.counter() == "5 of 5", "clamp " + a.counter())
    a.click(".chips .chip[data-c=all]")
    check(a.chip_count("All") == 7 and a.counter() == "1 of 7", f"All={a.chip_count('All')} {a.counter()}")
    a.click(".chips .chip[data-c='0-1']"); check(a.counter() == "1 of 2", a.counter())
    a.click(".chips .chip[data-c='1-0']"); check(a.counter() == "empty", a.counter())
    a.click(".kallax.big .cube[data-c='0-0']"); check(a.counter() == "1 of 5", "cube click " + a.counter())
    # swipe on the stage
    box = a.page.locator("#stage").bounding_box()
    a.page.mouse.move(box["x"] + box["width"] * .7, box["y"] + 60); a.page.mouse.down()
    a.page.mouse.move(box["x"] + box["width"] * .2, box["y"] + 60); a.page.mouse.up()
    check(a.counter() == "2 of 5", "swipe " + a.counter())


def t04_move(a):
    check(a.title() == "No UFO's", a.title())
    a.click(".dig-info [data-act=move]")
    a.click(".sheet button[aria-label='Kallax 1 B3']")
    check(a.toast() == "Moved to K1·B3", a.toast())
    check(a.loc("r9") == "K1:1-2", a.loc("r9"))
    check(a.chip_count("B3") == 1 and a.chip_count("A1") == 4, "chip counts")
    a.click(".chips .chip[data-c='1-2']"); check(a.title() == "No UFO's", "not under B3")
    a.undo()
    check(a.loc("r9") == "K1:0-0" and a.ev("rec('r9').home.c") == "0-0", "undo did not restore loc/home")
    check(a.chip_count("A1") == 5 and a.chip_count("B3") == 0, "undo counts")


def t05_bag(a):
    a.click(".dig-info [data-act=to-bag]")
    check(a.toast() == "Moved to Crater", a.toast())
    check(a.loc("r9") == "B1:0-0", a.loc("r9"))
    a.page.locator("#q").fill("No UFO"); a.page.locator("#q").press("Enter")
    check(a.page.locator(".detail h2").inner_text().strip().lower() == "crater", "not in bag view")
    back = a.page.locator(".dig-info [data-act=go-home]")
    check(back.inner_text().strip() == "Back to K1·A1", back.inner_text())
    back.click()
    check(a.toast() == "Back in K1·A1" and a.loc("r9") == "K1:0-0", (a.toast(), a.loc("r9")))


def t06_scan(a):
    a.click(".unit-card[data-u=B1]")
    before = a.unit_counts(); snap = a.ev("JSON.stringify(S.records.map(r=>r.loc))")
    a.click(".detail [data-act=scan-bag]"); a.click(".sheet [data-act=scan-sim]")
    found = a.page.locator(".sheet h2:has-text('Found')").inner_text()
    a.click(".sheet [data-act=scan-review]")
    btn = a.page.locator(".sheet [data-act=scan-apply]"); n = int(re.search(r"Update (\d+)", btn.inner_text()).group(1))
    diff_rows = a.page.locator(".diff .d").count()
    check(n == diff_rows, f"button says {n}, diff shows {diff_rows}")
    btn.click()
    after = a.unit_counts()
    check(sum(after.values()) == 10 and a.ev("S.records.length") == 10, f"total changed {after}")
    check(after != before, "nothing moved")
    t = a.toast(); check(f"{n} moved" in t, t)
    a.undo()
    check(a.ev("JSON.stringify(S.records.map(r=>r.loc))") == snap, "undo did not restore locations")
    a.click(".detail [data-act=empty-bag]")
    c = a.unit_counts()
    check(c["B1"] == 0 and c["K1"] == 10, f"unpack {c}")
    check(a.loc("r5") == "K1:0-0" and a.loc("r4") == "K1:0-1", "home slots wrong")
    return f"{found}; {n} moves; counts {before} -> {after}"


def t07_furniture(a):
    a.click("[data-act=open-add]"); a.click(".sheet [data-act=add-furniture]")
    a.click(".sheet .chip[data-g='IKEA Kallax']")
    a.click(".sheet .preset[data-k='ikea-kallax-2-2-77-77-cm']")
    check(a.page.locator("#af-rows").input_value() == "2" and a.page.locator("#af-cols").input_value() == "2", "rows/cols not prefilled 2x2")
    a.page.locator("#af-name").fill("Kallax 2")
    sw = a.page.locator(".sheet .sw[data-act=af-finish]").nth(1); fname = sw.get_attribute("data-n"); sw.click()
    check(a.page.locator(f".sheet .sw[data-n='{fname}']").get_attribute("aria-pressed") == "true", "finish not selected")
    a.page.locator("#af-rows").fill("3"); a.page.locator("#af-rows").dispatch_event("change")
    a.page.locator("#af-cols").fill("5"); a.page.locator("#af-cols").dispatch_event("change")
    check(a.page.locator(".sheet .preview .cube").count() == 15, f"preview cubes={a.page.locator('.sheet .preview .cube').count()}")
    a.page.locator(".sheet input[data-custom=af]").fill("#ff00aa")
    check(a.ev("draft.finish.name") == "Custom" and a.ev("draft.finish.hex").lower() == "#ff00aa", "custom color not applied")
    check(a.page.locator(".sheet label.sw.custom").get_attribute("aria-pressed") == "true", "custom swatch not pressed")
    check(a.page.locator("#af-name").input_value() == "Kallax 2", "name lost on re-render")
    new_id = a.page.locator("#af-id").input_value()
    a.click(".sheet #af-form button[type=submit]")
    u = a.ev("S.units[S.units.length-1]")
    check(a.page.locator(f".unit-card[data-u='{u['id']}']").count() == 1, "card missing")
    check(u["rows"] == 3 and u["cols"] == 5 and u["finish"]["hex"].lower() == "#ff00aa", f"unit={u}")
    check(a.page.locator(".detail .kallax.big .cube").count() == 15, "detail grid not 3x5")
    check(a.page.locator(".detail .chips .chip[data-c='2-4']").inner_text().startswith("C5"), "C5 label missing")
    # duplicate id
    a.click("[data-act=open-add]"); a.click(".sheet [data-act=add-furniture]")
    a.page.locator("#af-id").fill("k1")
    n = a.ev("S.units.length"); a.click(".sheet #af-form button[type=submit]")
    t = a.toast(); check(t == "ID K1 is taken. Pick another.", t)
    check(a.ev("S.units.length") == n, "duplicate added")
    check(new_id.startswith("K"), f"default ID for a Kallax preset is {new_id!r}, expected K2")
    return f"new unit {u['id']} 3x5 custom #ff00aa"


def t08_bag_add(a):
    a.click("[data-act=open-add]"); a.click(".sheet [data-act=add-bag]")
    total = a.page.locator(".sheet .preset").count()
    counts = a.ev("(()=>{const c={};BAGS.forEach(b=>c[b.brand]=(c[b.brand]||0)+1);return c})()")
    for brand in ("UDG", "Magma"):
        a.click(f".sheet .chip[data-b='{brand}']")
        got = a.page.locator(".sheet .preset").count()
        check(got == counts[brand], f"{brand} filter shows {got}, expected {counts[brand]}")
        check(all(brand in t for t in a.page.locator(".sheet .preset b").all_inner_texts()), f"{brand} filter leaks")
    a.click(".sheet .chip[data-b='All']"); check(a.page.locator(".sheet .preset").count() == total, "All filter")
    a.click(".sheet .chip[data-b='UDG']"); a.click(".sheet .preset >> nth=0")
    a.page.locator("#ab-name").fill("Gig Bag")
    sw = a.page.locator(".sheet .sw[data-act=ab-finish]").last; cname = sw.get_attribute("data-n"); sw.click()
    check(a.page.locator("#ab-name").input_value() == "Gig Bag", "name lost after color pick")
    a.page.locator(".sheet input[data-custom=ab]").fill("#22aa44")
    check(a.ev("draft.finish.hex").lower() == "#22aa44", "custom bag color")
    a.click(".sheet #ab-form button[type=submit]")
    card = a.page.locator(".unit-card[data-u=B2]")
    check(card.count() == 1 and "gig bag" in card.inner_text().lower(), "bag card missing")
    check(a.ev("unit('B2').finish.hex").lower() == "#22aa44", "bag color not saved")
    return f"{total} bags, UDG={counts['UDG']} Magma={counts['Magma']}; last named color {cname!r}"


def t09_add_record(a):
    a.click("[data-act=open-add]"); a.click(".sheet [data-act=add-record]")
    a.click(".sheet button[aria-label='Kallax 1 B2']")
    a.page.locator("#ar-artist").fill("Larry Heard"); a.page.locator("#ar-title").fill("Washing Machine")
    a.click("#ar-form button[type=submit]")
    check(a.ev("V.unit") == "K1" and a.ev("V.cell") == "1-1", "not on K1 B2")
    check(a.title() == "Washing Machine", a.title())
    check(a.counter() == "1 of 1", a.counter())
    a.page.locator("#q").fill("washing")
    r = a.page.locator("#results .result").first
    check("Washing Machine" in r.inner_text() and r.locator(".loc").inner_text().strip() == "K1·B2", r.inner_text())


def t10_edit(a):
    a.click(".dig-info [data-act=edit-rec]")
    a.page.locator("#er-title").fill("No UFOs (Vocal)")
    a.page.locator("#er-bpm").fill("128")
    a.page.locator("#er-tags").fill("peak, detroit")
    a.click("#er-stars button[data-n='4']")
    a.click("[data-act=er-addkv]")
    a.page.locator("[data-kv='0'][data-p=k]").fill("Bought at"); a.page.locator("[data-kv='0'][data-p=v]").fill("Halcyon")
    a.click("#er-form button[type=submit]")
    check(a.title().startswith("No UFOs (Vocal)"), a.title())
    check(a.page.locator(".dig-info h3 .edited").count() == 1, "edited dot missing")
    facts = a.page.locator(".dig-info .facts").inner_text()
    check("128 BPM" in facts and "★★★★" in facts, facts)
    check(a.page.locator(".dig-info .tagchip").count() == 2, "tags")
    check(a.ev("rec('r9').custom.length===1 && rec('r9').custom[0].v==='Halcyon'"), "custom field")
    a.click(".dig-info [data-act=edit-rec]")
    a.click("[data-act=revert][data-k=title]")
    check(a.page.locator("#er-title").input_value() == "No UFO's", "revert field value")
    a.click("#er-form button[type=submit]")
    check(a.title() == "No UFO's" and a.page.locator(".dig-info h3 .edited").count() == 0, a.title())
    check(a.ev("rec('r9').bpm") == "128", "BPM lost on revert")


def t11_playlists(a):
    a.click("#tab-pl")
    nm = a.page.locator("#pl-name"); check(nm.input_value() == "Warm-up", nm.input_value())
    items = lambda: a.ev("curPl().items.join(',')")
    check(items() == "r1,r4,r7,r8", items())
    nm.fill("Warm-up Set"); nm.press("Tab")
    check(a.ev("S.playlists[0].name") == "Warm-up Set", "rename")
    a.click(".item[data-idx='0'] [data-act=pl-down]"); check(items() == "r4,r1,r7,r8", items())
    a.click(".item[data-idx='1'] [data-act=pl-up]"); check(items() == "r1,r4,r7,r8", items())
    a.click(".item[data-idx='0'] [data-act=pl-rm]"); check(items() == "r4,r7,r8", items())
    a.undo(); check(items() == "r1,r4,r7,r8", "undo remove " + items())
    a.click("[data-act=pl-add]")
    a.click(".sheet [data-pk=r5]"); a.click(".sheet [data-pk=r2]")
    check(a.page.locator("#pk-done").inner_text() == "Add 2 records", a.page.locator("#pk-done").inner_text())
    a.click("#pk-done"); check(items() == "r1,r4,r7,r8,r5,r2", items())
    a.click("[data-act=pl-sort][data-s=loc]")
    order = a.ev("curPl().items.map(id=>rec(id).loc.u+':'+rec(id).loc.c)")
    uidx = {"K1": 0, "B1": 1, "C1": 2}
    check(order == sorted(order, key=lambda s: (uidx[s.split(':')[0]], s.split(':')[1])), f"pull order {order}")
    a.click("[data-act=pl-dup]")
    check(a.ev("S.playlists.length") == 3 and a.ev("curPl().name") == "Warm-up Set copy", "duplicate")
    a.click("[data-act=pl-del]"); check(a.page.locator("#pl-confirm .notice").is_visible(), "no confirm")
    a.click("[data-act=pl-del-yes]")
    check(a.ev("S.playlists.length") == 2 and "copy" not in a.ev("S.playlists.map(p=>p.name).join()"), "delete")
    a.click(".plcard[data-p=p1]")
    a.click("[data-act=pl-pack]"); a.click(".sheet [data-act=pack-to][data-u=B1]")
    t = a.toast()
    check(a.ev("curPl().items.every(id=>rec(id).loc.u==='B1')"), "not all packed")
    check(sum(a.unit_counts().values()) == 10, "total changed")
    return t


def t12_player(a):
    a.wait_link_mode()
    a.click("#player .pinfo")
    sh = a.page.locator("#np-sheet"); sh.wait_for()
    h3 = lambda: a.page.locator(".np-meta h3").inner_text().strip()
    check(h3() == "No UFO's", h3())
    a.click(".np-tabs [data-t=links]"); check(a.page.locator(".links .link").count() == 4, "links count")
    a.click(".np-tabs [data-t=chain]"); check(a.page.locator(".chain li").count() == 5, "chain count")
    a.click("[data-act=dry-run]")
    a.page.wait_for_selector(".chain li.on", timeout=2000)
    a.page.wait_for_selector(".chain li.done", timeout=4000)
    check(a.page.locator(".log").count() == 1, "no log")
    a.page.wait_for_function("P.dry===null", timeout=8000)
    a.click(".np-tabs [data-t=queue]"); check(a.page.locator(".pl .pli").count() == 10, "queue")
    a.click(".np-ctrl [data-act=p-next]"); check(h3() == "Strings Of Life", h3())
    a.click(".np-ctrl [data-act=p-prev]"); check(h3() == "No UFO's", h3())
    a.click(".np-ctrl [data-act=p-prev]"); check(h3() == "Around The World", "wrap " + h3())
    a.page.keyboard.press("Escape"); check(a.page.locator("#np-sheet").count() == 0, "Escape did not close")
    a.click("#player [data-act=p-next]")
    check("No UFO's" in a.page.locator("#player .pinfo b").inner_text(), "mini next")


def t13_settings(a):
    a.click("[data-act=open-settings]")
    a.click(".sheet [data-a=brass]"); check(a.ev("document.body.dataset.accent") == "brass", "brass")
    check(a.page.locator(".sheet [data-a=brass]").get_attribute("aria-pressed") == "true", "pressed")
    a.click(".sheet [data-a=cyan]"); check(a.ev("document.body.dataset.accent") == "cyan", "cyan")
    a.click(".sheet [data-act=close]")
    a.click(".dig-info [data-act=move]"); a.click(".sheet button[aria-label='Kallax 1 B4']")
    a.ev("S.records.push({...rec('r1'),id:'zz',loc:{u:'K1',c:'0-0'}})")
    a.click("[data-act=open-settings]"); a.click(".sheet [data-act=reset]")
    check(a.page.locator("#reset-confirm .notice").is_visible(), "no in-page confirm")
    check(a.ev("S.records.length") == 11, "reset ran before confirm")
    a.click("[data-act=reset-yes]")
    check(a.ev("S.records.length") == 10 and a.loc("r9") == "K1:0-0", "not restored")
    check(a.toast() == "Demo collection restored", a.toast())
    check(a.counter() == "1 of 5", a.counter())


def t14_layout(browser, url):
    out = []
    for scheme in ("light", "dark"):
        for w, h in ((390, 844), (1280, 900)):
            a = App(browser, url, w, h, scheme)
            try:
                a.wait_link_mode()
                a.page.screenshot(animations="disabled", path=str(SHOTS / f"{w}-{scheme}-unit.png"), full_page=True)
                if w == 390:
                    states = {}
                    def sw(name):
                        states[name] = a.ev("document.documentElement.scrollWidth")
                    sw("unit")
                    a.click(".chips .chip[data-c=all]"); sw("unit-all")
                    a.click(".dig-info [data-act=move]"); sw("move-sheet"); a.click(".sheet [data-act=close]")
                    a.page.locator("#q").fill("acid"); sw("search"); a.page.locator("#q").fill("")
                    a.click("[data-act=open-add]"); a.click(".sheet [data-act=add-furniture]"); sw("add-furniture")
                    if scheme == "light": a.page.screenshot(animations="disabled", path=str(SHOTS / "390-light-add-furniture.png"))
                    a.click(".sheet [data-act=close]")
                    a.click("#tab-pl"); sw("playlists")
                    if scheme == "light": a.page.screenshot(animations="disabled", path=str(SHOTS / "390-light-playlists.png"), full_page=True)
                    a.click("#tab-room"); sw("room")
                    a.click("#player .pinfo"); sw("player")
                    a.page.screenshot(animations="disabled", path=str(SHOTS / f"390-{scheme}-player.png"))
                    bad = {k: v for k, v in states.items() if v > 390}
                    out.append((scheme, states, bad))
                elif scheme == "dark":
                    a.click("#player .pinfo"); a.page.screenshot(animations="disabled", path=str(SHOTS / "1280-dark-player.png"))
            finally:
                a.close()
    bad = [(s, b) for s, _, b in out if b]
    check(not bad, f"horizontal overflow at 390px: {bad}")
    return "; ".join(f"{s}: max scrollWidth {max(st.values())}" for s, st, _ in out)


def t15_persist(a):
    a.click(".dig-info [data-act=move]"); a.click(".sheet button[aria-label='Kallax 1 B3']")
    a.click("#tab-pl"); a.page.locator("#pl-name").fill("Kept"); a.page.locator("#pl-name").press("Tab")
    a.page.reload(); a.page.wait_for_selector("#main .unit-card")
    check(a.loc("r9") == "K1:1-2", "move not persisted: " + a.loc("r9"))
    check(a.ev("S.playlists[0].name") == "Kept", "rename not persisted")
    check(a.ev("localStorage.getItem('crates-demo-v3')!==null"), "no v3 key")


# ------------------------------------------------ extra probes (bug hunting)
def x01_empty_cell_arrow_then_undo(a):
    a.click(".unit-card[data-u=B1]")
    a.click(".detail [data-act=empty-bag]")
    a.page.locator("body").click(position={"x": 2, "y": 300})
    a.page.keyboard.press("ArrowRight")
    vdig = a.ev("V.dig")
    a.undo()
    check(not a.errors, f"V.dig={vdig} then Undo -> {a.errors[:1]}")
    check(a.counter() == "1 of 3", "UI after undo: " + a.counter())


def x02_record_filed_into_bag_unpacks(a):
    a.click("[data-act=open-add]"); a.click(".sheet [data-act=add-record]")
    a.click(".sheet .tbag[data-u=B1]")
    a.page.locator("#ar-artist").fill("Larry Heard"); a.page.locator("#ar-title").fill("Washing Machine")
    a.click("#ar-form button[type=submit]")
    a.click(".detail [data-act=empty-bag]")
    left = a.ev("inCell('B1','all').map(r=>r.title)")
    # Design: a record filed straight into a bag has no home shelf, so it stays and the toast says so.
    check(left == ['Washing Machine'] and 'no home shelf' in a.toast(), f"left={left} toast={a.toast()}")


def x03_delete_home_unit_orphans(a):
    a.click("[data-act=open-add]"); a.click(".sheet [data-act=add-furniture]")
    a.page.locator("#af-id").fill("K9"); a.click(".sheet #af-form button[type=submit]")
    a.click("[data-act=go-room]"); a.click(".unit-card[data-u=K1]"); a.click(".chips .chip[data-c='0-0']")
    a.click(".dig-info [data-act=move]"); a.click(".sheet button[aria-label^='K9 A1']")
    a.click(".unit-card[data-u=K9]"); a.click(".dig-info [data-act=to-bag]")
    a.click(".detail [data-act=edit-unit]")
    check(a.page.locator(".sheet [data-act=del-unit]").is_enabled(), "remove disabled (ok)")
    a.click(".sheet [data-act=del-unit]"); a.click("[data-act=del-unit-yes]")
    a.click(".unit-card[data-u=B1]"); a.click(".detail [data-act=empty-bag]")
    total = sum(a.unit_counts().values())
    a.page.locator("#q").fill("No UFO"); a.page.locator("#q").press("Enter")
    check(total == 10 and not a.errors, f"after removing K9 and unpacking: {total}/10 records visible, r9 at {a.loc('r9')}; search Enter -> {a.errors[:1]}")


def x04_add_record_slot_change_keeps_typing(a):
    a.click("[data-act=open-add]"); a.click(".sheet [data-act=add-record]")
    a.page.locator("#ar-artist").fill("Larry Heard")
    a.click(".sheet button[aria-label='Kallax 1 B2']")
    v = a.page.locator("#ar-artist").input_value()
    check(v == "Larry Heard", f"artist field after picking slot = {v!r}")


def x05_revert_keeps_unsaved(a):
    a.click(".dig-info [data-act=edit-rec]")
    a.page.locator("#er-title").fill("X"); a.click("#er-form button[type=submit]")
    a.click(".dig-info [data-act=edit-rec]")
    a.page.locator("#er-bpm").fill("140")
    a.click("[data-act=revert][data-k=title]")
    v = a.page.locator("#er-bpm").input_value()
    check(v == "140", f"unsaved BPM after 'Undo edit' on title = {v!r}")


def x06_picker_duplicates(a):
    a.click("#tab-pl"); a.click("[data-act=pl-add]")
    check(a.page.locator(".sheet [data-pk=r1]").is_disabled(), "r1 (already in playlist) should be disabled")
    a.click(".sheet [data-pk=r2]"); a.click("#pk-done")
    n = a.ev("curPl().items.filter(x=>x==='r1').length")
    check(n == 1 and a.ev("curPl().items.includes('r2')"), f"r1 appears {n}x in playlist")


def x07_yt_hang_timeout(browser, url):
    a = App(browser, url, yt="hang")
    try:
        t0 = time.time(); a.wait_link_mode(9000); dt = time.time() - t0
        check(dt < 8, f"took {dt:.1f}s")
        return f"link mode after {dt:.1f}s with hanging iframe_api"
    finally:
        a.close()


def x08_eu_custom_color(a):
    a.click(".detail [data-act=edit-unit]")
    a.page.locator(".sheet input[data-custom=eu]").fill("#123456")
    check(a.ev("unit('K1').finish.hex").lower() == "#123456", "Look & name custom color")


# ---------------------------------------------------------------- runner
TESTS = [
    ("01 Boot", t01_boot), ("02 Search", t02_search), ("03 Flip-through", t03_flip),
    ("04 Move one record", t04_move), ("05 Put in bag / Back home", t05_bag), ("06 Bag scan + unpack", t06_scan),
    ("07 Add furniture", t07_furniture), ("08 Add bag", t08_bag_add), ("09 Add record", t09_add_record),
    ("10 Edit details", t10_edit), ("11 Playlists", t11_playlists), ("12 Player", t12_player),
    ("13 Settings", t13_settings), ("14 Layout + screenshots", t14_layout), ("15 Persistence", t15_persist),
    ("X1 Empty cell arrow, then Undo", x01_empty_cell_arrow_then_undo),
    ("X2 Homeless bag record stays on unpack", x02_record_filed_into_bag_unpacks),
    ("X3 Removing a unit that is a home", x03_delete_home_unit_orphans),
    ("X4 Add record keeps typing on slot change", x04_add_record_slot_change_keeps_typing),
    ("X5 Undo edit keeps unsaved fields", x05_revert_keeps_unsaved),
    ("X6 Picker blocks duplicates", x06_picker_duplicates),
    ("X7 YouTube API hang -> link mode", x07_yt_hang_timeout),
    ("X8 Look & name custom color", x08_eu_custom_color),
]
BROWSER_LEVEL = {t14_layout, x07_yt_hang_timeout}


def main():
    only = sys.argv[1:]
    build()
    srv, url = serve()
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--no-proxy-server", "--disable-background-networking"])
        for name, fn in TESTS:
            if only and not any(o.lower() in name.lower() for o in only):
                continue
            t0 = time.time(); a = None
            try:
                if fn in BROWSER_LEVEL:
                    note = fn(browser, url); errs = []
                else:
                    a = App(browser, url); note = fn(a); errs = a.js_errors()
                status = "PASS" if not errs else "FAIL"
                if errs: note = f"{note or ''} JS errors: {errs[:2]}"
            except Fail as e:
                status, note, errs = "FAIL", str(e), (a.js_errors() if a else [])
            except Exception as e:
                status, note, errs = "ERROR", f"{type(e).__name__}: {str(e).splitlines()[0][:300]}", (a.js_errors() if a else [])
                traceback.print_exc()
            finally:
                if a: a.close()
            results.append({"test": name, "status": status, "note": note or "", "js_errors": errs[:3], "secs": round(time.time() - t0, 1)})
            print(f"[{status}] {name} ({results[-1]['secs']}s) {note or ''}")
        browser.close()
    srv.shutdown()
    (HERE / "results.json").write_text(json.dumps(results, indent=2))
    p = sum(r["status"] == "PASS" for r in results)
    print(f"\n{p}/{len(results)} passed")


if __name__ == "__main__":
    main()
