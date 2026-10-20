"""Wrap crates.html (page content only) in a full document for testing.

If the source still has the boot-order bug (state init calls seed()/fpreset
before the `const` helpers exist -> TDZ ReferenceError), the harness copy
moves the two init lines below `const finishesFor` so the rest of the suite
can run. crates.html itself is never modified. Set CRATES_NO_PATCH=1 to test
the file exactly as written.
"""
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "crates.html"
OUT = HERE / "harness.html"
PATCHED = False


def _patch_tdz(body):
    lines = body.split("\n")
    init = [i for i, l in enumerate(lines) if l.startswith("let S;") or (l.startswith("if(!S ||") and "seed()" in l)]
    fin = next((i for i, l in enumerate(lines) if l.startswith("const finishesFor")), None)
    if len(init) != 2 or fin is None or init[-1] > fin:
        return body, False
    moved = [lines[i] for i in init]
    for i in reversed(init):
        del lines[i]
    fin = next(i for i, l in enumerate(lines) if l.startswith("const finishesFor"))
    lines[fin + 1:fin + 1] = moved
    return "\n".join(lines), True


def build():
    global PATCHED
    body = SRC.read_text(encoding="utf-8")
    if not os.environ.get("CRATES_NO_PATCH"):
        body, PATCHED = _patch_tdz(body)
    OUT.write_text(
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'
        + body + "</body></html>",
        encoding="utf-8",
    )
    return OUT


if __name__ == "__main__":
    print(build(), "patched TDZ" if PATCHED else "unpatched")
