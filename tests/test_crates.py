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
class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k):
        pass


def serve():
    h = functools.partial(_QuietHandler, directory=str(HERE))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/harness.html"


# ---------------------------------------------------------------- page wrapper
class App:
    def __init__(self, browser, url, width=1280, height=900, scheme="light", yt="abort", legacy=True):
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
        self.page.wait_for_selector("#main .unit-card, #main .cuebar")
        if legacy:
            # Older tests start inside Kallax 1, cubby A1, with the whole collection queued in the mini player.
            self.page.evaluate("V.view='unit';V.unit='K1';V.cell='0-0';V.dig=0;render();P.queue=S.records.map(r=>r.id);P.i=0;P.src='Whole collection';renderPlayer();")

    # helpers
    def ev(self, js, arg=None):
        return self.page.evaluate(js, arg) if arg is not None else self.page.evaluate(js)

    def click(self, sel, **kw):
        m = re.fullmatch(r"\.unit-card\[data-u=['\"]?(\w+)['\"]?\]", sel)
        if m and not self.page.locator(f".room .unit-card[data-u='{m.group(1)}']").count():
            # zoomed into a unit: the room cards are replaced by the cue bar, so open the unit directly
            self.page.evaluate(f"A['open-unit']({{u:'{m.group(1)}'}})"); self.page.wait_for_timeout(60); return
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
    check(a.page.locator(f"#main [data-u='{u['id']}']").count() >= 1, "card missing")
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
    card = a.page.locator("#main [data-u=B2]").first
    check(card.count() == 1 and "gig bag" in (card.inner_text() + " " + (card.get_attribute("aria-label") or "")).lower(), "bag card missing")
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
    a.page.reload(); a.page.wait_for_selector("#main .unit-card, #main .cuebar")
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


# ------------------------------------------------ new features (N-series)
def _png(w=64, h=48):
    """A tiny valid PNG with no barcode in it."""
    import struct, zlib
    raw = b"".join(b"\x00" + bytes([200, 60, 40]) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def _txt(loc):
    return re.sub(r"\s+", " ", loc.inner_text()).strip()


def _room(a):
    if a.ev("V.view") != "room":
        a.click("#tab-room"); a.page.wait_for_timeout(120)


def _k1(a, cell="0-0"):
    a.ev(f"V.view='unit';V.unit='K1';V.cell='{cell}';V.dig=0;render();")


def _settle(a, ms=80):
    a.page.wait_for_timeout(ms)


def _cell_count(a, key):
    return int(a.page.locator(f".chips .chip[data-c='{key}'] small").inner_text())


def _open_add_record(a):
    a.click("[data-act=open-add]"); a.click(".sheet [data-act=add-record]")
    a.page.wait_for_selector("#ar-form")


def n01_dupes(a):
    _open_add_record(a)
    check(a.page.locator("#ar-submit").inner_text().strip() == "File into K1·A1", "submit label before typing")
    a.page.locator("#ar-artist").fill("Mr Fingers"); a.page.locator("#ar-title").fill("Can You Feel It")
    txt = _txt(a.page.locator("#ar-dupe"))
    check("You already own" in txt, f"#ar-dupe = {txt!r}")
    check("Kallax 1, shelf A1 (Detroit & Chicago)" in txt, f"#ar-dupe location: {txt!r}")
    sub = a.page.locator("#ar-submit").inner_text().strip()
    check(sub == "Add another copy", f"submit reads {sub!r}")
    a.page.locator("#ar-title").fill("Can You Feel It (Remix)")
    check(_txt(a.page.locator("#ar-dupe")) == "", "warning stays after title changed")
    a.page.locator("#ar-title").fill("can you feel it")
    check("You already own" in _txt(a.page.locator("#ar-dupe")), "case-insensitive dupe")
    a.click("#ar-dupe [data-act=goto-rec]")
    check(a.page.locator(".sheet").count() == 0, "Show it left the sheet open")
    check(a.ev("V.unit") == "K1" and a.ev("V.cell") == "0-0", f"Show it -> {a.ev('V.unit')}:{a.ev('V.cell')}")
    check(a.title() == "Can You Feel It", f"Show it focused {a.title()!r}")
    # barcode duplicate
    a.ev("S.records[0].barcode='123456789012'")
    _open_add_record(a)
    a.page.locator("#ar-bc").fill("123456789012"); a.click("#bc-form button[type=submit]")
    out = _txt(a.page.locator("#ar-bcout"))
    check("already own" in out and "No UFO's" in out, f"barcode dupe msg: {out!r}")
    check(a.page.locator("#ar-bcout .cand .pill.own").count() == 3, "candidates should carry 'You own a copy'")
    check("You already own" in _txt(a.page.locator("#ar-dupe")), "dupe banner missing for barcode match")
    return out[:90]


def n02_barcode(a):
    _open_add_record(a)
    a.page.locator("#ar-bc").fill("724384960650"); a.click("#bc-form button[type=submit]")
    cands = a.page.locator("#ar-bcout .cand")
    check(cands.count() == 3, f"candidates={cands.count()}")
    check("Example pressings" in _txt(a.page.locator("#ar-bcout")), "candidates not labelled as examples")
    check(a.page.locator("#ar-bc").input_value() == "724384960650", "barcode field lost after lookup")
    cands.nth(1).locator("[data-act=bc-pick]").click()
    got = {k: a.page.locator(f"#ar-{k}").input_value() for k in ("artist", "title", "label", "year", "catno")}
    want = {"artist": "Example Artist", "title": "Example Track", "label": "Example Records UK", "year": "1993", "catno": "EXT 1"}
    check(got == want, f"Use this filled {got}")
    check(a.toast() == "Pressing filled in", a.toast())
    check(a.page.locator("#ar-bcout .cand").count() == 0, "candidates still shown after pick")
    check(a.ev("addRec.f.barcode") == "724384960650", "barcode not kept on the draft")
    a.page.locator("#ar-bc").fill("12345"); a.click("#bc-form button[type=submit]")
    msg = _txt(a.page.locator("#ar-bcout"))
    check("usually 12 or 13 digits" in msg, f"short barcode msg: {msg!r}")
    check(a.page.locator("#ar-artist").input_value() == "Example Artist", "typed fields lost after short-barcode re-render")
    t0 = time.time()
    a.page.locator("#ar-bcphoto").set_input_files(files=[{"name": "sleeve.png", "mimeType": "image/png", "buffer": _png()}])
    a.page.wait_for_function("document.querySelector('#ar-bcout')?.innerText.includes(\"Couldn't read a barcode\")", timeout=15000)
    dt = time.time() - t0
    bd = a.ev("'BarcodeDetector' in window")
    return f"photo fallback after {dt:.1f}s; BarcodeDetector={bd}"


def n03_discogs_sync(a):
    a.click("[data-act=open-settings]")
    a.click("#set-dsync")
    a.page.wait_for_selector(".sheet [data-act=sync-run]")
    box = _txt(a.page.locator(".sheet .bcbox"))
    check("10 updates waiting" in box, f"settings: {box!r}")
    a.click(".sheet [data-act=close]")
    dl = _txt(a.page.locator(".dig-info .dl"))
    check("Discogs Location:" in dl and "K1·A1 (Detroit & Chicago)" in dl and "Waiting to sync" in dl, f"dl={dl!r}")
    a.click("[data-act=open-settings]"); a.click(".sheet [data-act=sync-run]")
    t = a.toast(); check("10 locations marked as saved" in t, t)
    check("0 updates waiting" in _txt(a.page.locator(".sheet .bcbox")), "queue not emptied")
    a.click(".sheet [data-act=close]")
    pill = a.page.locator(".dig-info .dl .pill").inner_text().strip()
    check(pill == "Saved", f"pill={pill!r}")
    a.click(".dig-info [data-act=move]"); a.click(".sheet button[aria-label='Kallax 1 B3']")
    a.click(".chips .chip[data-c='1-2']")
    check(a.title() == "No UFO's", a.title())
    dl = _txt(a.page.locator(".dig-info .dl"))
    check("K1·B3" in dl and "Waiting to sync" in dl, f"after move dl={dl!r}")
    q = a.ev("S.syncQueue.map(x=>x.r+'='+x.value)")
    check(q == ["r9=K1·B3"], f"queue={q}")
    a.undo()
    check(a.ev("S.syncQueue.length") == 0, "undo did not restore the sync queue")
    return f"queue after move {q}"


def n04_cubby_subtitle(a):
    a.click(".dig-info [data-act=move]"); a.click(".sheet button[aria-label='Kallax 1 B2']")
    a.click(".chips .chip[data-c='1-1']")
    inp = a.page.locator("#cell-name")
    check(inp.input_value() == "" and "Name B2" in (inp.get_attribute("placeholder") or ""), "empty subtitle field")
    inp.fill("House"); inp.press("Enter")
    a.page.wait_for_function("unit('K1').labels['1-1']==='House'", timeout=2000)
    _settle(a)
    chip = _txt(a.page.locator(".chips .chip[data-c='1-1']"))
    check(chip.startswith("B2 House"), f"chip={chip!r}")
    em = a.page.locator(".kallax.big .cube[data-c='1-1'] .lbl em").inner_text().strip()
    check(em == "House", f"cube label em={em!r}")
    check(a.toast() == "B2 is now “House”", a.toast())
    a.page.locator("#q").fill("house")
    hit = a.page.locator("#results .result[data-r=r9]")
    check(hit.count() == 1, "search 'house' did not find the record filed in B2 (matches only via subtitle)")
    check("Kallax 1, shelf B2 (House)" in _txt(hit), f"result={_txt(hit)!r}")
    a.page.locator("#q").fill("")
    inp = a.page.locator("#cell-name"); inp.fill(""); inp.press("Enter")
    a.page.wait_for_function("!('1-1' in unit('K1').labels)", timeout=2000)
    _settle(a)
    check("House" not in _txt(a.page.locator(".chips .chip[data-c='1-1']")), "chip still shows House")
    check(a.page.locator(".kallax.big .cube[data-c='1-1'] .lbl em").count() == 0, "cube still labelled")
    check(a.toast() == "Subtitle removed from B2", a.toast())


def n05_cubby_move(a):
    ids = sorted(a.ev("inCell('K1','0-0').map(r=>r.id)"))
    a.click(".detail [data-act=cubby-move]")
    check(a.page.locator("#cm-label").is_checked(), "keep-subtitle checkbox not checked by default")
    check("Detroit & Chicago" in _txt(a.page.locator(".sheet")), "subtitle not named in sheet")
    a.click(".sheet button[aria-label='Kallax 1 B1']")
    check(sorted(a.ev("inCell('K1','1-0').map(r=>r.id)")) == ids, "not all 5 records moved to B1")
    check(a.ev("inCell('K1','1-0').every(r=>r.home.u==='K1'&&r.home.c==='1-0')"), "homes not updated to B1")
    check(a.ev("unit('K1').labels['1-0']") == "Detroit & Chicago", "subtitle did not move to B1")
    check(a.ev("unit('K1').labels['0-0']") is None, "A1 still has the subtitle")
    check(a.ev("inCell('K1','0-0').length") == 0, "A1 not empty")
    check(a.ev("V.cell") == "1-0", "view did not follow to B1")
    t = a.toast(); check(t == "Moved 5 from K1·A1 to K1·B1", t)
    a.undo()
    check(sorted(a.ev("inCell('K1','0-0').map(r=>r.id)")) == ids, "undo records")
    check(a.ev("inCell('K1','0-0').every(r=>r.home.c==='0-0')"), "undo homes")
    labs = a.ev("JSON.stringify(unit('K1').labels)")
    check(labs == '{"0-0":"Detroit & Chicago","0-1":"Acid"}', f"undo labels {labs}")
    # whole cubby into the bag
    a.click(".chips .chip[data-c='0-0']")
    a.click(".detail [data-act=cubby-move]"); a.click(".sheet .tbag[data-u=B1]")
    nb = a.ev("inCell('B1','all').length")
    check(nb == 8, f"bag has {nb}")
    bad = a.ev(f"{json.dumps(ids)}.map(rec).filter(r=>!(r.loc.u==='B1'&&r.home.u==='K1'&&r.home.c==='0-0'&&r.from&&r.from.u==='K1'&&r.from.c==='0-0')).map(r=>r.id)")
    check(not bad, f"home/from wrong for {bad}")
    check(a.ev("unit('K1').labels['0-0']") == "Detroit & Chicago", "subtitle should stay on A1 (bags have no subtitles)")
    check(a.ev("V.unit") == "B1", "view did not follow to the bag")


def n06_cubby_swap(a):
    a.click(".detail [data-act=cubby-swap]")
    check("Swap the subtitles too" in _txt(a.page.locator(".sheet")) and a.page.locator("#cm-label").is_checked(), "swap checkbox")
    check(a.page.locator(".sheet .tbag").count() == 0, "swap should only offer shelves")
    a.click(".sheet button[aria-label='Kallax 1 A2']")
    check(_cell_count(a, "0-0") == 2 and _cell_count(a, "0-1") == 5, f"A1={_cell_count(a,'0-0')} A2={_cell_count(a,'0-1')}")
    check(a.ev("unit('K1').labels['0-0']") == "Acid" and a.ev("unit('K1').labels['0-1']") == "Detroit & Chicago", "labels not swapped")
    check("Acid" in _txt(a.page.locator(".chips .chip[data-c='0-0']")), "A1 chip label")
    check(a.ev("rec('r8').home.c") == "0-0" and a.ev("rec('r9').home.c") == "0-1", "homes did not follow")
    t = a.toast(); check(t == "Swapped K1·A1 and K1·A2", t)
    a.undo()
    check(_cell_count(a, "0-0") == 5 and _cell_count(a, "0-1") == 2, "undo counts")
    check(a.ev("unit('K1').labels['0-0']") == "Detroit & Chicago" and a.ev("unit('K1').labels['0-1']") == "Acid", "undo labels")
    check(a.ev("rec('r8').home.c") == "0-1" and a.ev("rec('r9').home.c") == "0-0", "undo homes")


def n07_multi_select(a):
    a.click(".chips .chip[data-c=all]")
    a.click("[data-act=toggle-sel]")
    check(a.page.locator(".list input[data-sel]").count() == 7, "checkbox rows")
    a.page.locator("input[data-sel=r9]").click(); _settle(a)
    a.page.locator("input[data-sel=r8]").click(); _settle(a)
    check(a.ev("[...V.sel].sort().join()") == "r8,r9", f"sel={a.ev('[...V.sel].join()')}")
    btn = a.page.locator(".selbar [data-act=sel-move]")
    check(btn.inner_text().strip() == "Move 2…", btn.inner_text())
    btn.click()
    a.click(".sheet .tbag[data-u=C1]")
    check(a.loc("r9") == "C1:0-0" and a.loc("r8") == "C1:0-0", (a.loc("r9"), a.loc("r8")))
    check(a.ev("rec('r9').from.c") == "0-0" and a.ev("rec('r8').from.c") == "0-1", "came-from not set")
    t = a.toast(); check(t == "Moved 2 to Milk crate", t)
    check(a.ev("V.sel") is None, "selection mode not closed")
    a.undo()
    check(a.loc("r9") == "K1:0-0" and a.loc("r8") == "K1:0-1", "undo")
    a.click("[data-act=toggle-sel]"); a.click(".selbar [data-act=sel-all]")
    check(a.ev("V.sel.size") == 7, "select all")


def n08_came_from(a):
    a.click(".unit-card[data-u=B1]")
    rows = a.ev("[...document.querySelectorAll('.list .li')].map(li=>li.querySelector('.t b').textContent+'|'+(li.querySelector('.from')?.textContent||'').replace(/\\s+/g,' ').trim())")
    want = {"Good Life": "from K1·A2", "Voodoo Ray": "from K1·A1", "Around The World": "from K1·A2"}
    got = dict(r.split("|", 1) for r in rows)
    for k, v in want.items():
        check(got.get(k, "").startswith(v), f"{k}: {got.get(k)!r}")
    check("came from" in _txt(a.page.locator(".dig-info")), "dig info lacks 'came from'")
    a.click(".unit-card[data-u=K1]"); a.click(".chips .chip[data-c='0-1']")
    check(a.title() == "Higher State Of Consciousness", a.title())
    a.click(".dig-info [data-act=to-bag]")
    check(a.toast() == "Moved to Crater", a.toast())
    a.click(".unit-card[data-u=B1]")
    row = a.page.locator(".list .li:has-text('Higher State')")
    check(row.count() == 1 and _txt(row.locator(".from")).startswith("from K1·A2"), f"row: {_txt(row) if row.count() else None}")
    return "; ".join(rows)


def n09_set_history(a):
    _room(a); check(a.page.locator(".sec-head [data-act=stale-list] small").inner_text().strip() == "6", "stale count != 6")
    _k1(a)
    a.click(".dig-info [data-act=log-play]")
    a.page.locator("#lp-date").fill("2026-10-01"); a.page.locator("#lp-venue").fill("Test club")
    a.click("#lp-form button[type=submit]")
    plays = _txt(a.page.locator(".dig-info .plays"))
    check("Last played" in plays and "Test club" in plays and "2026" in plays, f"plays={plays!r}")
    check(a.toast() == "Play logged", a.toast())
    _room(a); check(a.page.locator(".sec-head [data-act=stale-list] small").inner_text().strip() == "5", "stale count after logging")
    _k1(a)
    a.undo()
    check("Never logged" in _txt(a.page.locator(".dig-info .plays")), "undo did not remove the play")
    check(a.ev("rec('r9').plays.length") == 0, "play still stored")
    _room(a); a.click(".sec-head [data-act=stale-list]")
    rows = a.page.locator(".sheet .pick .check")
    check(rows.count() == 6, f"stale sheet rows={rows.count()}")
    ids = sorted(a.ev("[...document.querySelectorAll('.sheet .pick [data-act=goto-rec]')].map(b=>b.dataset.r)"))
    check(ids == sorted(["r9", "r2", "r6", "r3", "r5", "r10"]), f"stale ids {ids}")
    check("last played" in _txt(rows.filter(has_text="Strings Of Life")), "r2 should say last played")
    a.click(".sheet [data-act=stale-pl]")
    check(a.ev("V.view") == "playlists" and a.ev("curPl().items.length") == 6, "playlist not made with 6")
    check(a.page.locator("#pl-name").input_value() == "Not played in a year", "playlist name")
    a.click("#tab-room"); a.click(".unit-card[data-u=K1]"); a.click(".chips .chip[data-c='0-1']")
    a.click("[data-act=toggle-stale]")
    check(a.counter() == "empty", a.counter())
    e = _txt(a.page.locator(".dig .empty"))
    check("played in the last year" in e, f"empty state: {e!r}")
    a.click(".chips .chip[data-c='0-0']")
    check(a.counter() == "1 of 4", f"A1 with stale filter: {a.counter()}")


def n10_gigs(a):
    a.click("#tab-gigs")
    check(a.ev("V.gig") == "g2", f"V.gig={a.ev('V.gig')}")
    check(a.page.locator(".gig h2").inner_text().strip().lower() == "halloween warm-up", "g2 not shown")
    check(a.page.locator(".gig .steps li.on").inner_text().strip() == "Plan", "not in planning")
    check(a.page.locator(".gig .check").count() == 5, "5 records in plan")
    a.click(".gig [data-act=gig-next]")
    check(a.ev("curGig().status") == "packing", "not packing")
    prev = {r: a.ev(f"JSON.stringify(rec('{r}').loc)") for r in ("r1", "r2")}
    for r in ("r1", "r2"):
        a.page.locator(f"input[data-gig=pack][data-r={r}]").click(); _settle(a)
    for r in ("r1", "r2"):
        check(a.loc(r) == "B1:0-0", f"{r} not in Crater: {a.loc(r)}")
        fr = a.ev(f"JSON.stringify(rec('{r}').from)")
        check(fr == prev[r], f"{r} came-from {fr} != {prev[r]}")
    nxt = a.page.locator(".gig [data-act=gig-next]")
    check(nxt.inner_text().strip() == "Head out (3 left behind)", nxt.inner_text())
    nxt.click()
    check(a.page.locator(".gig input[data-gig=played]").count() == 2, "out step should list packed records only")
    a.page.locator("input[data-gig=played][data-r=r2]").click(); _settle(a)
    check(a.ev("rec('r2').plays.some(p=>p.d==='2026-10-31'&&p.gig==='g2')"), "play not logged on 2026-10-31")
    nxt = a.page.locator(".gig [data-act=gig-next]")
    check(nxt.inner_text().strip() == "I'm home, unpack", nxt.inner_text())
    nxt.click()
    a.page.locator("input[data-gig=back][data-r=r2]").click(); _settle(a)
    check(a.ev("same(rec('r2').loc, rec('r2').home)"), f"r2 not home: {a.loc('r2')}")
    check(a.loc("r1") == "B1:0-0", "r1 should still be in the bag")
    a.page.locator(".gig [data-act=gig-next]").click()
    body = _txt(a.page.locator(".gig"))
    check("1 not checked back in" in body, f"summary: {body[:200]!r}")
    check(a.page.locator(".gig .pill.own").inner_text().strip() == "Missing", "Missing pill")
    check(a.ev("curGig().status") == "done", "not done")
    # new gig from a playlist
    a.click("[data-act=new-gig]")
    a.page.locator("#ng-name").fill("Test night"); a.page.select_option("#ng-pl", "p1")
    a.click("#ng-form button[type=submit]")
    g = a.ev("curGig()")
    check(g["name"] == "Test night" and len(g["items"]) == 4 and g["status"] == "planning" and g["bag"] == "B1", f"new gig {g}")
    check(a.toast() == "Gig created", a.toast())
    n = a.ev("S.gigs.length")
    a.click(".gig [data-act=gig-del]")
    check(a.page.locator("#gig-confirm .notice").is_visible(), "no in-page confirm")
    check(a.ev("S.gigs.length") == n, "deleted before confirm")
    a.click("[data-act=gig-del-yes]")
    check(a.ev("S.gigs.length") == n - 1 and not a.ev("S.gigs.some(g=>g.name==='Test night')"), "not deleted")


def n11_stickers(a):
    _room(a); a.click(".sec-head [data-act=stickers]")
    st = a.page.locator(".sheet .sticker")
    check(st.count() == 11, f"stickers={st.count()}")
    lens = a.ev("[...document.querySelectorAll('.sheet .sticker svg path')].map(p=>p.getAttribute('d').length)")
    check(len(lens) == 11 and min(lens) > 500, f"QR path lengths {lens}")
    titles = a.ev("[...document.querySelectorAll('.sheet .sticker')].map(s=>s.title)")
    check(any(t.endswith("#K1-A2") for t in titles), f"no #K1-A2 title in {titles[:3]}")
    w = lambda: a.page.locator(".sheet .sticker svg").first.get_attribute("width")
    check(w() == "144", f"1.5in width={w()}")
    a.click(".sheet [data-act=stk-size][data-z='2']"); check(w() == "192", f"2in width={w()}")
    a.click(".sheet [data-act=stk-size][data-z='1']"); check(w() == "96", f"1in width={w()}")
    check(a.page.locator(".sheet [data-act=stk-size][data-z='1']").get_attribute("aria-pressed") == "true", "size chip pressed")
    a.click(".sheet [data-act=stk-cub]")
    check(st.count() == 3, f"no-cubby stickers={st.count()}")
    a.click(".sheet [data-act=stk-cub]"); check(st.count() == 11, "cubbies back")
    a.click(".sheet [data-act=stk-unit][data-u=C1]"); check(st.count() == 10, "unit toggle")
    msgs = {}
    for f in ("html", "svg", "png"):
        a.page.evaluate("document.querySelector('#stk-msg') && (document.querySelector('#stk-msg').innerHTML='')")
        try:
            with a.page.expect_download(timeout=6000) as d:
                a.click(f".sheet [data-act=stk-save][data-f={f}]")
            msgs[f] = "download:" + d.value.suggested_filename
        except Exception as e:
            msgs[f] = "no-download"
        _settle(a, 300)
        msgs[f] += " msg=" + _txt(a.page.locator("#stk-msg"))
    check(not a.js_errors(), f"errors while saving: {a.js_errors()[:2]}")
    a.click(".sheet [data-act=close]")
    _k1(a); a.click(".detail [data-act=stickers][data-u=K1]")
    check(st.count() == 9, f"detail QR chip -> {st.count()} stickers (want K1 + 8 cubbies)")
    return "; ".join(f"{k}: {v}" for k, v in msgs.items())


def n12_deep_links(a):
    a.page.goto("about:blank"); a.page.goto(a.url + "#K1-B2"); a.page.wait_for_selector("#main .unit-card, #main .cuebar")
    check(a.ev("V.unit") == "K1" and a.ev("V.cell") == "1-1", f"boot deep link -> {a.ev('V.unit')}:{a.ev('V.cell')}")
    check(a.page.locator(".chips .chip[data-c='1-1']").get_attribute("aria-pressed") == "true", "B2 chip not pressed")
    a.ev("location.hash='B1'")
    a.page.wait_for_function("V.unit==='B1'", timeout=2000)
    check(a.page.locator(".detail h2").inner_text().strip().lower() == "crater", "bag view not shown")
    a.ev("location.hash='ZZ9'"); _settle(a, 200)
    check(a.ev("V.unit") == "B1", "invalid hash changed the view")
    a.ev("location.hash='k1-a2'"); a.page.wait_for_function("V.unit==='K1'", timeout=2000)
    check(a.ev("V.cell") == "0-1", f"lowercase k1-a2 -> {a.ev('V.cell')}")
    a.ev("location.hash='K1-Z9'"); _settle(a, 200)
    check(a.ev("V.unit") == "K1" and a.ev("V.cell") == "all", f"out-of-range cubby -> {a.ev('V.cell')}")
    a.ev("location.hash='%E0%A4%A'"); _settle(a, 200)  # malformed escape
    check(not a.errors, f"malformed hash threw: {a.errors[:1]}")


def n13_mobile_no_errors(browser, url):
    a = App(browser, url, 390, 844)
    try:
        widths = {}
        def sw(name, sheet=False):
            w = a.ev("document.documentElement.scrollWidth")
            if sheet:
                w = max(w, a.ev("(()=>{const s=document.querySelector('.sheet');return s?390+(s.scrollWidth-s.clientWidth):0})()"))
            widths[name] = w
        a.click("#tab-gigs"); sw("gigs-plan")
        a.click(".gig [data-act=gig-next]"); a.page.locator("input[data-gig=pack][data-r=r1]").click(); _settle(a); sw("gigs-loadout")
        a.click("[data-act=new-gig]"); sw("new-gig", True); a.click(".sheet [data-act=close]")
        a.click("#tab-room"); a.click(".sec-head [data-act=stickers]"); sw("stickers", True)
        a.click(".sheet [data-act=stk-size][data-z='2']"); sw("stickers-2in", True); a.click(".sheet [data-act=close]")
        _open_add_record(a)
        a.page.locator("#ar-artist").fill("Mr Fingers"); a.page.locator("#ar-title").fill("Can You Feel It")
        a.page.locator("#ar-bc").fill("724384960650"); a.click("#bc-form button[type=submit]"); sw("add-record", True)
        a.click(".sheet [data-act=close]")
        a.click(".sec-head [data-act=stale-list]"); sw("stale", True); a.click(".sheet [data-act=close]")
        a.click(".unit-card[data-u=K1]"); a.click(".chips .chip[data-c='0-1']"); sw("cubby-tools")
        a.click(".detail [data-act=cubby-move]"); sw("cubby-move", True); a.click(".sheet [data-act=close]")
        a.click("[data-act=toggle-sel]"); a.page.locator("input[data-sel=r8]").click(); _settle(a); sw("selbar")
        a.click("[data-act=open-settings]"); a.click("#set-dsync"); a.page.wait_for_selector(".sheet [data-act=sync-run]"); sw("settings-sync", True)
        bad = {k: v for k, v in widths.items() if v > 390}
        check(not bad, f"horizontal overflow at 390px: {bad}")
        check(not a.js_errors(), f"console/page errors: {a.js_errors()[:3]}")
        return f"max width {max(widths.values())} over {len(widths)} states"
    finally:
        a.close()


def n14_collection(a):
    a.click("#tab-table")
    check(a.ev("V.view") == "table", "Collection tab did not open")
    rows = lambda: a.page.locator(".ctable tbody tr:has(input[data-tsel])")
    check(rows().count() == 10, f"rows={rows().count()}")
    check(a.page.locator("[data-act=t-back-all]").inner_text().strip() == "Put 3 back home", "Put N back home label")
    a.click("[data-act=t-filt][data-f=bag]")
    check(rows().count() == 3, f"In a bag shows {rows().count()}")
    a.click("[data-act=t-filt][data-f=all]")
    # inline edit + Enter
    t = a.page.locator("input[data-tedit=title][data-r=r9]")
    t.fill("No UFOs (Vocal)"); t.press("Enter")
    check(a.ev("rec('r9').title") == "No UFOs (Vocal)", "title not saved")
    check("edited" in (t.get_attribute("class") or ""), "edited class missing")
    check(a.ev("rec('r9').orig.title") == "No UFO's", "Discogs original overwritten")
    a.page.locator("[data-tedit=rating][data-r=r9]").select_option("4")
    check(a.ev("rec('r9').rating") == 4, "rating select")
    # bag select -> Crater, Put back -> home
    a.page.locator("select[data-tbag=r2]").select_option("B1"); _settle(a)
    check(a.loc("r2") == "B1:0-0" and a.ev("rec('r2').from.c") == "0-0", f"bag select: {a.loc('r2')}")
    check("Strings Of Life is in Crater" == a.toast(), a.toast())
    a.click("[data-act=t-back][data-r=r2]")
    check(a.loc("r2") == "K1:0-0", f"Put back: {a.loc('r2')}")
    check(a.toast() == "Back in K1·A1", a.toast())
    a.page.locator("select[data-tbag=r4]").select_option(""); _settle(a)  # "Take out"
    check(a.loc("r4") == "K1:0-1", f"Take out: {a.loc('r4')}")
    # home spot select
    a.page.locator("select[data-thome=r6]").select_option("K1|1-3"); _settle(a)
    check(a.ev("rec('r6').home.c") == "1-3", "home not changed")
    check(a.toast() == "Home spot is now K1·B4", a.toast())
    a.page.locator("select[data-thome=r5]").select_option("K1|1-0"); _settle(a)  # bagged record: home only
    check(a.ev("rec('r5').home.c") == "1-0" and a.loc("r5") == "B1:0-0", "bagged record home change moved it")
    # sort by year desc
    a.click("[data-act=t-sort][data-k=year]"); a.click("[data-act=t-sort][data-k=year]")
    yrs = [int(v) for v in a.page.locator("input[data-tedit=year]").evaluate_all("els=>els.map(e=>e.value)")]
    check(yrs == sorted(yrs, reverse=True), f"year desc {yrs}")
    check(a.page.locator("[data-act=t-sort][data-k=year]").get_attribute("aria-sort") == "descending", "aria-sort")
    # bulk select 2 -> put back home (r5 and r10 are in Crater)
    a.page.locator("input[data-tsel=r5]").click(); _settle(a)
    a.page.locator("input[data-tsel=r10]").click(); _settle(a)
    check(a.ev("T.sel.size") == 2 and "2 selected" in _txt(a.page.locator(".selbar")), "selbar")
    a.click(".selbar [data-act=t-sel-back]")
    check(a.loc("r5") == "K1:1-0" and a.loc("r10") == "K1:0-1", f"bulk put back {a.loc('r5')} {a.loc('r10')}")
    check(a.toast() == "2 put back home", a.toast())
    a.undo(); check(a.loc("r5") == "B1:0-0", "undo bulk put back")
    # search filter (debounced)
    a.page.locator("#t-q").fill("crater"); a.page.wait_for_timeout(400)
    check(rows().count() == 2, f"filter 'crater' rows={rows().count()}")
    check(a.ev("document.activeElement.id") == "t-q", "filter input lost focus after re-render")
    a.page.locator("#t-q").fill(""); a.page.wait_for_timeout(400)
    with a.page.expect_download(timeout=6000) as d:
        a.click("[data-act=t-csv]")
    check(d.value.suggested_filename == "crates-collection.csv", "csv name")
    return f"years desc {yrs[:4]}…"


def n14b_collection_layout(browser, url):
    out = {}
    for w, h in ((390, 844), (844, 390)):
        a = App(browser, url, w, h)
        try:
            a.click("#tab-table"); _settle(a)
            out[f"{w}x{h}"] = a.ev("document.documentElement.scrollWidth")
            a.page.locator("input[data-tsel=r1]").click(); _settle(a)
            out[f"{w}x{h}-selbar"] = a.ev("document.documentElement.scrollWidth")
            check(not a.js_errors(), f"errors {a.js_errors()[:2]}")
        finally:
            a.close()
    bad = {k: v for k, v in out.items() if v > int(k.split("x")[0])}
    check(not bad, f"horizontal page overflow: {bad}")
    return str(out)


def n15_readme_shots(browser, url):
    made = []
    for label, (w, h) in (("desktop", (1280, 900)), ("mobile", (390, 844))):
        a = App(browser, url, w, h, "light")
        try:
            def shot(name, full=False):
                # full-page captures: put the fixed mini player at the end of the page instead of mid-image
                if full: a.ev("document.body.insertAdjacentHTML('beforeend','<style id=shotfix>.player{position:static!important;margin:24px -16px 0}body{padding-bottom:0!important}</style>')")
                a.page.screenshot(animations="disabled", full_page=full, path=str(SHOTS / f"readme-{name}-{label}.png"))
                if full: a.ev("document.getElementById('shotfix')?.remove()")
                made.append(f"readme-{name}-{label}.png")
            a.wait_link_mode()
            top = lambda: (a.ev("window.scrollTo(0,0)"), a.ev("document.querySelector('.toast')?.remove()"), a.page.mouse.move(0, 0), _settle(a, 150))
            a.click(".chips .chip[data-c='0-1']"); top(); shot("room", True)
            _open_add_record(a)
            a.page.locator("#ar-artist").fill("Mr Fingers"); a.page.locator("#ar-title").fill("Can You Feel It")
            a.page.locator("#ar-bc").fill("724384960650"); a.click("#bc-form button[type=submit]")
            a.ev("document.querySelector('.bcbox').scrollIntoView({block:'start'})"); _settle(a, 350); shot("add-record-dupe")
            a.click(".sheet [data-act=close]")
            _room(a); a.click(".sec-head [data-act=stickers]"); _settle(a, 350); shot("stickers")
            a.click(".sheet [data-act=close]")
            a.click("#tab-gigs"); a.click(".gig [data-act=gig-next]")
            a.page.locator("input[data-gig=pack][data-r=r1]").click(); _settle(a)
            a.page.locator("input[data-gig=pack][data-r=r6]").click(); _settle(a)
            top(); shot("gigs", True)
            a.click("#player .pinfo"); a.page.wait_for_selector("#np-sheet"); _settle(a, 450); shot("player")
            a.page.keyboard.press("Escape")
            a.click("#tab-pl"); top(); shot("playlists", True)
            if label == "mobile":
                a.click("#tab-table"); top(); shot("collection", True)
            check(not a.js_errors(), f"errors: {a.js_errors()[:2]}")
        finally:
            a.close()
    a = App(browser, url, 1440, 900, "light")  # wide desktop: collection + two-column player
    try:
        a.wait_link_mode()
        a.click("#tab-table"); a.ev("document.querySelector('.toast')?.remove()"); a.page.mouse.move(0, 0); _settle(a, 150)
        a.page.screenshot(animations="disabled", path=str(SHOTS / "readme-collection-desktop.png")); made.append("readme-collection-desktop.png")
        a.click("#player .pinfo"); a.page.wait_for_selector("#np-sheet"); _settle(a, 450)
        L = a.page.locator(".np-left").bounding_box(); R = a.page.locator(".np-right").bounding_box()
        check(L and R and L["x"] + L["width"] <= R["x"] + 1, f"player not two-column at 1440x900: left={L} right={R}")
        a.page.screenshot(animations="disabled", path=str(SHOTS / "readme-player-desktop.png"))
        check(not a.js_errors(), f"errors: {a.js_errors()[:2]}")
    finally:
        a.close()
    return f"{len(made)} files (player-desktop at 1440x900)"


# ---- probes for bugs found while writing the N-series
def _add_k7(a):
    a.click("[data-act=open-add]"); a.click(".sheet [data-act=add-furniture]")
    a.click(".sheet .chip[data-g='IKEA Kallax']"); a.click(".sheet .preset[data-k='ikea-kallax-2-2-77-77-cm']")
    a.page.locator("#af-id").fill("K7"); a.click(".sheet #af-form button[type=submit]")
    check(a.ev("V.unit") == "K7", "K7 not added")


def x09_subtitle_on_new_shelf(a):
    _add_k7(a)
    a.click(".chips .chip[data-c='0-0']")
    inp = a.page.locator("#cell-name"); inp.fill("Disco"); inp.press("Enter"); _settle(a, 150)
    check(not a.errors, f"naming a cubby on a just-added shelf threw: {a.errors[:1]}")
    check(a.ev("unit('K7').labels?.['0-0']") == "Disco", "subtitle not saved")


def x10_cubby_move_into_new_shelf(a):
    _add_k7(a)
    a.click(".unit-card[data-u=K1]"); a.click(".chips .chip[data-c='0-0']")
    a.click(".detail [data-act=cubby-move]"); a.click(".sheet button[data-u=K7][data-c='0-0']"); _settle(a, 150)
    nk = a.ev("inCell('K7','0-0').length"); open_ = a.page.locator('.sheet').count() == 1
    check(not a.errors, f"moving a named cubby into a just-added shelf threw: {a.errors[:1]} (records moved: {nk}, sheet still open: {open_})")


def x11_subtitle_toast_names_right_cubby(a):
    a.click(".chips .chip[data-c='1-1']")
    a.page.locator("#cell-name").fill("House")
    a.click(".chips .chip[data-c='0-1']")  # blur commits the subtitle, click switches cubby
    _settle(a, 150)
    check(a.ev("unit('K1').labels['1-1']") == "House", "subtitle not saved on blur")
    t = a.toast()
    check(t == "B2 is now “House”", f"toast after blur-by-click names the wrong cubby: {t!r}")


def x12_hash_cleared_after_nav(a):
    a.page.goto("about:blank"); a.page.goto(a.url + "#K1-B2"); a.page.wait_for_selector("#main .unit-card, #main .cuebar")
    a.click(".unit-card[data-u=B1]")
    a.ev("location.hash='K1-B2'"); _settle(a, 200)
    check(a.ev("V.unit") == "K1", f"re-opening the same sticker link after navigating away does nothing (hash still {a.ev('location.hash')!r})")


def x13_cube_label_overlap(browser, url):
    hits = {}
    for w, h in ((1280, 900), (390, 844)):
        a = App(browser, url, w, h)
        try:
            hits[w] = a.ev("""[...document.querySelectorAll('.kallax.big .cube')].filter(c=>c.querySelector('.cnt')).filter(c=>{
                const l=c.querySelector('.lbl').getBoundingClientRect(), n=c.querySelector('.cnt').getBoundingClientRect();
                return l.right>n.left && l.left<n.right && l.bottom>n.top && l.top<n.bottom }).map(c=>c.querySelector('.lbl').textContent)""")
        finally:
            a.close()
    bad = {k: v for k, v in hits.items() if v}
    check(not bad, f"cubby subtitle overlaps the record count on the big shelf: {bad}")


def x14_table_thumbs(a):
    a.click("#tab-table")
    w = a.ev("(()=>{const t=document.querySelector('.ctable .thumb');return [t.getBoundingClientRect().width,t.querySelector('svg').getBoundingClientRect().width]})()")
    check(w[1] >= w[0] - 1, f"collection cover art draws at {w[1]}px inside a {w[0]}px thumb (.mini-btn svg rule shrinks it)")


TESTS += [
    ("N01 Duplicate warning", n01_dupes), ("N02 Barcode lookup", n02_barcode),
    ("N03 Discogs Location sync", n03_discogs_sync), ("N04 Cubby subtitle", n04_cubby_subtitle),
    ("N05 Whole-cubby move", n05_cubby_move), ("N06 Swap cubbies", n06_cubby_swap),
    ("N07 Multi-select move", n07_multi_select), ("N08 Came-from", n08_came_from),
    ("N09 Set history + stale", n09_set_history), ("N10 Gigs", n10_gigs),
    ("N11 QR stickers", n11_stickers), ("N12 Deep links", n12_deep_links),
    ("N13 390px + no errors on new flows", n13_mobile_no_errors),
    ("N14 Collection table", n14_collection), ("N14b Collection 390px + 844x390", n14b_collection_layout),
    ("N15 README screenshots", n15_readme_shots),
    ("X9 Subtitle on a just-added shelf", x09_subtitle_on_new_shelf),
    ("X10 Named cubby into a just-added shelf", x10_cubby_move_into_new_shelf),
    ("X11 Subtitle toast after blur-by-click", x11_subtitle_toast_names_right_cubby),
    ("X12 Same sticker link twice", x12_hash_cleared_after_nav),
    ("X13 Cube subtitle vs count overlap", x13_cube_label_overlap),
    ("X14 Collection thumbnails full size", x14_table_thumbs),
]
BROWSER_LEVEL |= {n13_mobile_no_errors, n14b_collection_layout, n15_readme_shots, x13_cube_label_overlap}


# ------------------------------------------------ room fit, zoom, drag, undo, previews (R-series)
def _drag(a, src_sel, dst_sel):
    src = a.page.locator(src_sel).first; src.evaluate("e=>e.scrollIntoView({block:'center'})"); a.page.wait_for_timeout(120)
    sb = src.bounding_box(); db = a.page.locator(dst_sel).first.bounding_box()
    check(sb and db, f"drag boxes missing: {src_sel} -> {dst_sel}")
    m = a.page.mouse
    m.move(sb["x"] + sb["width"] * 0.5, sb["y"] + sb["height"] * 0.5); m.down()
    m.move(sb["x"] + sb["width"] * 0.5 + 12, sb["y"] + sb["height"] * 0.5 + 12, steps=3)
    m.move(db["x"] + db["width"] / 2, db["y"] + db["height"] / 2, steps=12); a.page.wait_for_timeout(60)
    m.up(); a.page.wait_for_timeout(150)


def r01_room_fits(browser, url):
    out = []
    for w, h in [(1440, 900), (1280, 800), (390, 844)]:
        a = App(browser, url, w, h, legacy=False)
        try:
            check(a.ev("V.view") == "room", f"boot view {a.ev('V.view')} at {w}x{h}")
            check(a.ev("document.getElementById('player').hidden"), "mini player should stay hidden until something plays")
            sh, ih = a.ev("document.documentElement.scrollHeight"), a.ev("innerHeight")
            check(sh <= ih + 2, f"room scrolls at {w}x{h}: {sh} > {ih}")
            check(a.ev("document.documentElement.scrollWidth") <= w, f"sideways scroll at {w}x{h}")
            n = a.page.locator(".room .unit-card").count(); check(n == 3, f"{n} unit cards")
            for i in range(n):
                b = a.page.locator(".room .unit-card").nth(i).bounding_box()
                check(b["y"] + b["height"] <= ih + 1, f"card {i} below the fold at {w}x{h}")
            check(not a.js_errors(), a.js_errors())
            out.append(f"{w}x{h} ok")
        finally:
            a.close()
    return "; ".join(out)


def r02_zoom(a):
    a.click("[data-act=go-room]"); a.page.wait_for_timeout(100)
    a.click(".room .unit-card[data-u=K1]"); a.page.wait_for_timeout(150)
    check(a.ev("V.view") == "unit" and a.ev("V.unit") == "K1", "click did not zoom into K1")
    check(a.page.locator(".cuebar .cue").count() == 10, "cue bar should list 8 cubbies + 2 bags/crates")
    check(a.page.locator(".room").count() == 0, "room grid still shown while zoomed")
    a.click(".cuebar .cue[data-u=B1]"); a.page.wait_for_timeout(150)
    check(a.ev("V.unit") == "B1", "strip did not switch unit")
    a.click(".detail [data-act=go-room]"); a.page.wait_for_timeout(150)
    check(a.ev("V.view") == "room" and a.page.locator(".room .unit-card").count() == 3, "back to room failed")


def r03_drag(browser, url):
    a = App(browser, url, 1280, 1100)
    try:
        a.click(".chips .chip[data-c='0-0']")
        _drag(a, ".list .li", ".detail .cube[data-drop-c='1-2']")
        check(a.toast() == "Moved to K1·B3", f"toast {a.toast()!r}")
        check(a.ev("inCell('K1','1-2').length") == 1 and a.ev("inCell('K1','0-0').length") == 4, "record not in B3")
        a.page.evaluate("window.scrollTo(0,0)")
        _drag(a, ".list .li", ".cuebar .cue[data-drop-u=B1]")
        nb = a.ev("inCell('B1','all').length"); check(nb == 4, f"bag count {nb}")
        moved = a.ev("S.records.filter(r=>r.loc.u==='B1' && r.from && r.from.c==='0-0').length")
        check(moved >= 2, f"came-from not set on dragged record ({moved})")
        # a plain click on a row still selects it (no accidental drag)
        a.click(".list .li >> nth=1"); check(a.ev("V.dig") == 1, "click after drag did not select")
        check(not a.js_errors(), a.js_errors())
        return "row → cubby and row → bag in strip"
    finally:
        a.close()


def r04_multi_undo(a):
    a.click(".chips .chip[data-c='0-0']")
    for rid, cell in [("r9", "1-0"), ("r2", "1-1"), ("r1", "1-2")]:
        a.ev(f"moveRecord('{rid}', {{u:'K1',c:'{cell}'}})")
    a.page.wait_for_timeout(100)
    badge = a.page.locator("#undo-btn b").inner_text()
    check(badge == "3", f"undo badge {badge!r}")
    check("Moved to K1·B3" in a.page.locator("#undo-btn").get_attribute("title"), "undo title should name the last step")
    a.page.keyboard.press("Control+z"); a.page.wait_for_timeout(80)
    check(a.loc("r1") == "K1:0-0" and a.loc("r2") == "K1:1-1", "first undo should only revert the last move")
    a.click("#undo-btn"); a.page.wait_for_timeout(80)
    a.page.keyboard.press("Control+z"); a.page.wait_for_timeout(80)
    check(a.loc("r9") == "K1:0-0" and a.loc("r2") == "K1:0-0", "three undos should restore all")
    check(a.page.locator("#undo-btn").is_disabled(), "undo button should be disabled when the stack is empty")
    a.click(".dig-info [data-act=edit-rec]"); a.page.locator("#er-title").fill("Changed"); a.click("#er-form button[type=submit]")
    check(a.title() == "Changed", "edit not saved")
    a.click("#undo-btn"); a.page.wait_for_timeout(80)
    check(a.title() != "Changed", "undo should revert a details edit")


def r05_previews(a):
    a.wait_link_mode()
    href = a.page.locator(".list .pv").first.get_attribute("href") or ""
    check("&t=60s" in href, f"link-mode preview href {href!r}")
    a.ev("""(()=>{ window.__seek=null; P.yt={loadVideoById(){},getPlayerState(){return 1},getDuration(){return 300},seekTo(t){window.__seek=t},
        pauseVideo(){},playVideo(){},getCurrentTime(){return 0}}; P.mode='yt'; render(); renderPlayer(); })()""")
    before = a.ev("P.queue.length")
    a.click(".list .pv[data-act=preview] >> nth=1")
    check(a.ev("!!P.preview") and a.ev("P.queue.length") == 1, "preview did not start")
    a.ev("onYTState(1)")
    seek = a.ev("window.__seek"); check(seek and 90 <= seek <= 110, f"preview should start about a third in, seek={seek}")
    check("Preview" in a.page.locator("#player .pinfo").inner_text(), "mini player should say Preview")
    a.click(".list .pv.on")
    check(not a.ev("!!P.preview") and a.ev("P.queue.length") == before, "stopping should restore the queue")


def r06_player_slides_in(browser, url):
    a = App(browser, url, 1280, 900, legacy=False)
    try:
        check(a.ev("document.getElementById('player').hidden"), "player visible before playing")
        a.click("[data-act=play-all]"); a.page.wait_for_timeout(500)
        check(not a.ev("document.getElementById('player').hidden"), "player should appear after Play")
        tr = a.ev("getComputedStyle(document.getElementById('player')).translate")
        check(tr in ("none", "0px", "0px 0px"), f"player should finish sliding in, translate={tr}")
        return "hidden until play, then slides in"
    finally:
        a.close()


def r07_bag_default_names(a):
    for n in (1, 2):
        a.click("[data-act=open-add]"); a.click(".sheet [data-act=add-bag]")
        v = a.page.locator("#ab-name").input_value(); check(v == f"Bag {n}", f"default name {v!r}")
        a.click("#ab-form button[type=submit]"); a.page.wait_for_timeout(100)
    names = a.ev("S.units.filter(u=>u.kind==='bag').map(u=>u.name)")
    check(names[-2:] == ["Bag 1", "Bag 2"], f"bag names {names}")


def r08_looks_and_cuebar(a):
    check(a.ev("document.documentElement.dataset.look") == "shop", "default look should be Shop floor")
    a.click("#look-btn"); check(a.ev("document.documentElement.dataset.look") == "booth", "second look should be Booth")
    bg = a.ev("getComputedStyle(document.body).backgroundColor"); check(bg == "rgb(21, 15, 34)", f"booth background {bg}")
    a.click("#look-btn"); check(a.ev("document.documentElement.dataset.look") is None, "third option should follow the device")
    a.click("#look-btn"); check(a.ev("S.settings.look") == "shop", "cycle back to Shop floor")
    pads = a.page.locator(".cuebar .cue"); check(pads.count() == 10, f"{pads.count()} pads")
    lit = a.page.locator(".cuebar .cue.lit").count(); check(lit == 3, f"{lit} lit pads (A1, A2, Crater)")
    a.click(".cuebar .cue[data-u=K1][data-c='0-1']")
    check(a.ev("V.unit") == "K1" and a.ev("V.cell") == "0-1", "pad should open K1·A2")
    check(a.page.locator(".cuebar .cue[aria-current=true]").get_attribute("data-c") == "0-1", "current pad not marked")
    a.click(".cuebar .cue[data-u=B1]"); check(a.ev("V.unit") == "B1" and a.ev("V.cell") == "all", "bag pad")


TESTS += [
    ("R01 Room fits the screen", r01_room_fits), ("R02 Zoom into a unit", r02_zoom),
    ("R03 Drag and drop", r03_drag), ("R04 Multi-step undo", r04_multi_undo),
    ("R05 Audio previews", r05_previews), ("R06 Player slides in", r06_player_slides_in),
    ("R07 New bags are Bag 1, Bag 2", r07_bag_default_names),
    ("R08 Looks + cue bar", r08_looks_and_cuebar),
]
BROWSER_LEVEL |= {r01_room_fits, r03_drag, r06_player_slides_in}


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
