# Interaction spec: Map and Columns views

Goal: Crates should feel like an Apple app. Feedback is instant, motion has mass and can be interrupted, gestures behave the same everywhere, nothing janks. This spec covers the Map view (pannable, zoomable room canvas plus a cubby sheet), the Columns view (spots, records, detail), motion tokens, density, and a review checklist. Written 2026-10-20 for the single-file prototype `crates.html`, which already uses `cubic-bezier(.2,.8,.2,1)`, reduced-motion guards, a view transition named `unit-zoom`, and `navigator.vibrate?.(12)`; section 4 tokens replace those literals.

Confidence markers: unmarked items were checked against a cited source. **[verify]** means from memory, a community source, or untested on a device, so test before relying on it. No code below was run in a browser; the JS blocks were only syntax-checked with `node --check`.

Sources used:
- Apple HIG: [Motion](https://developer.apple.com/design/human-interface-guidelines/motion), [Sheets](https://developer.apple.com/design/human-interface-guidelines/sheets), [Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility), [Layout](https://developer.apple.com/design/human-interface-guidelines/layout), [Playing haptics](https://developer.apple.com/design/human-interface-guidelines/playing-haptics)
- MDN: [touch-action](https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action), [setPointerCapture](https://developer.mozilla.org/en-US/docs/Web/API/Element/setPointerCapture), [wheel event](https://developer.mozilla.org/en-US/docs/Web/API/Element/wheel_event), [overscroll-behavior](https://developer.mozilla.org/en-US/docs/Web/CSS/overscroll-behavior), [@starting-style](https://developer.mozilla.org/en-US/docs/Web/CSS/@starting-style), [View Transitions](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API/Using), [linear()](https://developer.mozilla.org/en-US/docs/Web/CSS/easing-function/linear), [Vibration API](https://developer.mozilla.org/en-US/docs/Web/API/Vibration_API)

## 0. Principles (from the HIG, applied)
1. Direct manipulation tracks the finger 1:1 with no easing; springs and easing apply only after release (Motion: feedback "follows people's gestures"; Reduce Motion: "tracking animations directly with people's gestures").
2. Every animation is interruptible: a new touch cancels it and takes over with the live position and velocity (Motion: "Let people cancel motion").
3. No animation on high-frequency actions such as row selection (Motion). Every gesture has an on-screen alternative (Accessibility): zoom buttons, grabber, Back button.
4. Motion and haptics supplement visuals, never replace them, and both are optional settings.
5. One gesture vocabulary: vertical drag moves sheets, left-edge drag goes back, pinch zooms only the canvas, tap selects, double-tap zooms in.


## 1. Pan and pinch-zoom canvas (Map view)
### 1.1 Model
- One state object `T = {x, y, k}`. Screen point = world point * k + (x, y). World units are CSS px at k = 1.
- `#world` has `transform-origin: 0 0` and is painted with `translate3d(x,y,0) scale(k)` inside the clipping viewport `#vp`, at most once per frame (rAF), with no layout reads in move handlers. Animate only `transform` and `opacity`.
- Scale limits: `minK = fitK * 0.6`, `maxK = 6`. Hard limits for wheel and buttons, rubber-banded for pinch (log space), springing back on release.
- Pan limits: at least 25 percent of the room's bounding box must stay inside the viewport. Beyond that, rubber-band while dragging and spring back on release.
- Rubber band function: `f(x, d) = (1 - 1/(x*0.55/d + 1)) * d` where d is the viewport dimension. This is the widely reproduced UIScrollView-feel formula. **[verify]** It is community reverse-engineering, not an Apple document; the 0.55 constant is tunable. Glide decay is `0.998^dt` per ms (UIScrollView `.normal`; **[verify]**, from WWDC "Designing Fluid Interfaces" and secondary write-ups).

### 1.2 Touch and browser behaviour
- `#vp { touch-action: none; user-select: none; -webkit-touch-callout: none; overscroll-behavior: none; }`. MDN: `touch-action` is read when a gesture starts, so it must be in CSS, not set in a handler. It intersects with ancestors up to the first scroller, so one declaration on `#vp` is enough.
- Only the canvas gets `touch-action: none`. MDN warns it blocks low-vision zoom, so keep it off the page, the sheet and the columns, and ship on-screen +, minus and fit buttons.
- Do not call `setPointerCapture` on pointerdown. Capture retargets the later `click` to the capturing element, which breaks tapping a cubby. Capture only once movement passes the slop (8 px touch, 3 px mouse). Pointer Events are used, so a `pointercancel` means the browser claimed the gesture; treat it like pointerup without a tap.
- Tap is decided in pointerup (moved < slop, held < 250 ms), not from `click`. The first tap acts immediately; do not delay it waiting for a possible double-tap.
- Desktop trackpad pinch arrives as `wheel` with `ctrlKey: true` (MDN confirms zoom wheel events set `ctrlKey`). The listener must be `{passive: false}` or `preventDefault` does nothing and the whole page zooms. A real mouse wheel with Ctrl held sends large integer steps (about 100), a pinch sends small fractional ones, so clamp `deltaY` to +-25. **[verify]** the clamp feel.
- Safari on macOS reports trackpad pinch as non-standard `gesturestart/gesturechange` (with `e.scale`), not ctrl-wheel. Add handlers that `preventDefault` and call `zoomAt`. **[verify]** on current Safari; the events are WebKit-only.
- Plain wheel or two-finger scroll pans (multiply deltas by 16 when `deltaMode === 1`).
- Blurry text: set `will-change: transform` on `#world` only during a gesture or glide, so the browser re-rasterises at the settled scale. Prefer SVG for the room drawing.

### 1.3 Gestures
| Input | Result |
|---|---|
| One finger or mouse drag | Pan 1:1; on release, glide using the last 100 ms of velocity. |
| Two fingers | Pan by midpoint delta, scale by distance ratio about the midpoint (absolute from gesture start). Lifting one finger continues as a pan with no jump. |
| Double-tap (300 ms, < 24 px) or `dblclick` | On a unit: fit that unit at 80 percent of the viewport. Already there, or on empty space: fit room. |
| Keys | Arrows pan 80 px, `+`/`-` zoom 1.25x, `0` fits room, `Enter` opens the focused cubby's sheet. |

Semantic zoom thresholds (class on `#vp`, no animation): k < 0.6 shows unit codes only; 0.6 to 1.5 adds cubby codes (`B2`); above 1.5 adds record counts and the top cover. Cubbies smaller than 32 screen px are not tappable targets: the first tap flies to the unit instead of opening a sheet (keeps the 44 pt rule honest).

When a sheet is open, fly so the selected cubby sits centred in the area above the sheet (`bottomInset = visible sheet height`), as Apple Maps does.

### 1.4 Code skeleton
```js
const rub = (x, d, c = .55) => (1 - 1 / (x * c / d + 1)) * d;          // rubber band
const band = (v, lo, hi, d) => v < lo ? lo - rub(lo - v, d) : v > hi ? hi + rub(v - hi, d) : v;

// Velocity-preserving, cancellable spring. x, v in units and units/ms; w rad/ms (0.016 ~ 400 ms settle); z damping ratio.
function spring(x, to, v, tick, done, { w = .016, z = 1 } = {}) {
  let t0 = performance.now(), id = 0, dead = false;
  const f = t => {
    if (dead) return;
    const dt = Math.min(t - t0, 32); t0 = t;
    for (let i = 0; i < 4; i++) { v += (-w * w * (x - to) - 2 * z * w * v) * dt / 4; x += v * dt / 4; }
    const rest = Math.abs(x - to) < .25 && Math.abs(v) < .005;
    tick(rest ? to : x, v);
    rest ? done?.() : (id = requestAnimationFrame(f));
  };
  id = requestAnimationFrame(f);
  return () => { dead = true; cancelAnimationFrame(id); };
}

function makeCanvas(vp, world, { bounds, minK, maxK, reduce = false }) {
  const T = { x: 0, y: 0, k: 1 }, P = new Map(), SLOP = 8, now = () => performance.now();
  let G = null, S = [], stop = () => {}, raf = 0, lastTap = null;
  const R = () => vp.getBoundingClientRect(), clampK = k => Math.min(maxK, Math.max(minK, k));
  const draw = () => raf ||= requestAnimationFrame(() => { raf = 0; world.style.transform = `translate3d(${T.x}px,${T.y}px,0) scale(${T.k})`; });
  const range = k => { const { width: w, height: h } = R(), b = bounds();   // keep >= 25% of the room visible
    return { x: [w * .25 - b.x1 * k, w * .75 - b.x0 * k], y: [h * .25 - b.y1 * k, h * .75 - b.y0 * k] }; };
  function zoomAt(fx, fy, k) {                       // keep the world point under (fx,fy) fixed
    const r = R(), px = fx - r.left, py = fy - r.top, wx = (px - T.x) / T.k, wy = (py - T.y) / T.k;
    T.k = k; T.x = px - wx * k; T.y = py - wy * k; draw();
  }
  function flyTo(rect, { pad = .8, bottomInset = 0 } = {}) {  // rect in world units; spring on centre + log k
    stop(); const r = R(), h = r.height - bottomInset;
    const k1 = clampK(Math.min(r.width / rect.w, h / rect.h) * pad);
    const a = { x: (r.width / 2 - T.x) / T.k, y: (h / 2 - T.y) / T.k, l: Math.log(T.k) };
    const b = { x: rect.x + rect.w / 2, y: rect.y + rect.h / 2, l: Math.log(k1) };
    const set = s => { T.k = Math.exp(a.l + (b.l - a.l) * s);
      T.x = r.width / 2 - (a.x + (b.x - a.x) * s) * T.k; T.y = h / 2 - (a.y + (b.y - a.y) * s) * T.k; draw(); };
    reduce ? set(1) : (stop = spring(0, 1, 0, set, null, { w: .014, z: 1 }));
  }
  function release() {                               // 1) settle scale, 2) glide with edge spring-back
    const s = S.filter(p => now() - p.t < 100), a = s[0], b = s.at(-1), dt0 = a && b ? b.t - a.t : 0;
    const V = { x: dt0 ? (b.x - a.x) / dt0 : 0, y: dt0 ? (b.y - a.y) / dt0 : 0 };
    if (clampK(T.k) !== T.k) stop = spring(Math.log(T.k), Math.log(clampK(T.k)), 0, l => zoomAt(G.mx, G.my, Math.exp(l)), null, { w: .02 });
    let t0 = now(), id = 0; stop = (prev => () => { prev(); cancelAnimationFrame(id); })(stop);
    const step = t => {
      const dt = Math.min(t - t0, 32); t0 = t; const r = range(T.k); let alive = false;
      for (const p of ['x', 'y']) {
        const [lo, hi] = r[p], edge = T[p] < lo ? lo : T[p] > hi ? hi : null;
        V[p] = edge === null ? V[p] * Math.pow(reduce ? .99 : .998, dt) : V[p] + (-.0004 * (T[p] - edge) - .05 * V[p]) * dt;
        T[p] += V[p] * dt; alive ||= Math.abs(V[p]) > .01 || edge !== null;
      }
      draw(); if (alive) id = requestAnimationFrame(step);
    };
    id = requestAnimationFrame(step);
  }
  vp.addEventListener('pointerdown', e => {
    if (e.pointerType === 'mouse' && e.button) return;
    stop(); P.set(e.pointerId, { x: e.clientX, y: e.clientY, x0: e.clientX, y0: e.clientY, t: now() }); S = [];
    const [a, b] = [...P.values()];
    G = P.size === 2 ? { pinch: true, d0: Math.hypot(a.x - b.x, a.y - b.y), k0: T.k, mx: (a.x + b.x) / 2, my: (a.y + b.y) / 2, moved: true } : { moved: false };
  });
  vp.addEventListener('pointermove', e => {
    const p = P.get(e.pointerId); if (!p) return;
    const dx = e.clientX - p.x, dy = e.clientY - p.y; p.x = e.clientX; p.y = e.clientY;
    if (G.pinch && P.size === 2) {                   // pan by midpoint delta, then scale about the midpoint
      const [a, b] = [...P.values()], mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      T.x += mx - G.mx; T.y += my - G.my; G.mx = mx; G.my = my;
      zoomAt(mx, my, Math.exp(band(Math.log(G.k0 * Math.hypot(a.x - b.x, a.y - b.y) / G.d0), Math.log(minK), Math.log(maxK), 1)));
    } else if (P.size === 1) {
      if (!G.moved) { if (Math.hypot(p.x - p.x0, p.y - p.y0) < SLOP) return; G.moved = true; vp.setPointerCapture(e.pointerId); }
      const r = R(), g = range(T.k);
      T.x = band(T.x + dx, ...g.x, r.width); T.y = band(T.y + dy, ...g.y, r.height);
      S.push({ x: e.clientX, y: e.clientY, t: now() }); if (S.length > 12) S.shift(); draw();
    }
  });
  const up = e => {
    const p = P.get(e.pointerId); P.delete(e.pointerId); if (!p || !G) return;
    if (P.size === 1) { const q = [...P.values()][0]; q.x0 = q.x; q.y0 = q.y; G = { moved: true }; S = []; return; }  // pinch -> pan, no jump
    if (P.size) return;
    if (!G.moved && e.type === 'pointerup' && now() - p.t < 250) {                                                   // tap, fires at once
      const dbl = lastTap && now() - lastTap.t < 300 && Math.hypot(e.clientX - lastTap.x, e.clientY - lastTap.y) < 24;
      lastTap = dbl ? null : { t: now(), x: e.clientX, y: e.clientY };
      vp.dispatchEvent(new CustomEvent(dbl ? 'canvas-dbltap' : 'canvas-tap', { detail: { x: e.clientX, y: e.clientY } }));
    } else release();
  };
  vp.addEventListener('pointerup', up); vp.addEventListener('pointercancel', up);
  vp.addEventListener('wheel', e => {
    e.preventDefault(); stop();
    if (e.ctrlKey || e.metaKey) zoomAt(e.clientX, e.clientY, clampK(T.k * Math.exp(-Math.max(-25, Math.min(25, e.deltaY)) * .01)));
    else { const m = e.deltaMode === 1 ? 16 : 1; T.x -= e.deltaX * m; T.y -= e.deltaY * m; draw(); }
  }, { passive: false });
  return { T, flyTo, zoomAt, fit: () => flyTo(bounds(), { pad: .92 }) };
}
```
Notes: the `canvas-tap` listener hit-tests with `document.elementFromPoint(x, y)?.closest('[data-cubby]')`. With `reduce` on, pan and pinch still track the finger, glide is shorter, and `flyTo` jumps. Left unhandled in the skeleton: wheel hard-clamping of pan, the `gesture*` Safari handlers, and key handling.

## 2. Bottom sheet with snap points (Map view, phone)
### 2.1 Behaviour
- Detents (HIG: "large" and "medium" plus custom): **peek** (grabber, title, record count, about 96 px + bottom safe area), **half** (about 50 percent of the viewport), **full** (viewport minus top safe area minus 8 px). Sheets "automatically support large"; medium and custom heights are opt-in (Sheets).
- Non-modal at peek and half: the canvas behind stays interactive (HIG: "nonmodal sheet" lets people affect the parent view). The sheet root has `pointer-events: none`; only the sheet panel takes events. Full snap may dim the canvas.
- Include a grabber. It is a real `<button aria-label="Resize sheet">`; tap cycles peek, half, full (HIG: grabber "can tap it to cycle through the detents", works with VoiceOver).
- Swipe down from peek dismisses (clears selection). Also provide a Close button (Done/Close at trailing edge). Do not auto-dismiss on a timer.
- Desktop (min-width 900px): same markup becomes a non-modal right side panel, `width: clamp(340px, 32vw, 420px)`, no drag, slides in on the X axis. Esc closes it and returns focus to the cubby.

### 2.2 Gesture rules (drag versus scroll handoff)
| Sheet state | Touch starts on | Drag up | Drag down |
|---|---|---|---|
| Peek or half | header, grabber, or list | Sheet moves up (list does not scroll) | Sheet moves down |
| Full | header or grabber | (clamped) | Sheet moves down |
| Full | list, `scrollTop > 0` | List scrolls | List scrolls |
| Full | list, `scrollTop === 0` | List scrolls (no-op) | Sheet moves down |

Once a drag is handed to the sheet it stays with the sheet until finger lift. This mirrors iOS closely enough.

Implementation constraint: `touch-action` cannot change mid-gesture (MDN). If the list is `touch-action: pan-y`, the browser claims vertical drags and fires `pointercancel`. So the header and grabber use Pointer Events with `touch-action: none`, and the **list uses Touch Events** with a non-passive `touchmove` that calls `preventDefault()` only while the sheet should win. This is the one place where Touch Events beat Pointer Events. **[verify]**: after a prevented `touchmove` some browsers will not start native scrolling later in the same gesture, so a single drag can go sheet then list on iOS native, but on the web the user may need to lift. Acceptable.

Alternative to evaluate: build the sheet as a vertical scroll-snap container (`scroll-snap-type: y mandatory`, a transparent spacer with snap stops) so handoff and momentum are native. Cost: no velocity-continuous springs, rubber banding differs per browser, and `scrollsnapchange` is not universal. **[verify]** support before choosing.

### 2.3 Velocity-based snapping
- Track the last 100 ms of pointer samples, `v` in px/ms (positive down).
- Project: `y_proj = y + v * 180`. (UIScrollView-style full projection is `v * 0.998/(1-0.998)` = about 500 ms of travel, which over-shoots for sheets; 180 ms is a starting value to tune.)
- Snap to the nearest detent to `y_proj`. If `|v| > 0.5` px/ms, never snap back to the starting detent. If starting at peek and `v > 0.8` and the drag moved down, dismiss.
- Settle with `spring(y, target, v, ...)` using `z = 0.9` and `w = 0.016` so the release velocity carries through. Cancel the spring on any new touch and continue from the live position.
- Past full and past peek use the same `band()` rubber band.

### 2.4 CSS
```css
.sheet-root { position: fixed; inset: 0; pointer-events: none; z-index: 40; }
.sheet {
  position: absolute; inset: auto 0 0 0;
  height: calc(100dvh - env(safe-area-inset-top, 0px) - 8px);
  padding-bottom: env(safe-area-inset-bottom, 0px);        /* content clears the home indicator */
  background: var(--surface); border-radius: 14px 14px 0 0;
  transform: translate3d(0, var(--y, 0px), 0);              /* JS writes --y in px while dragging */
  transition: transform var(--dur-sheet) var(--spring-smooth);  /* used for tap-to-cycle and enter only */
  pointer-events: auto; overscroll-behavior: contain;
  @starting-style { transform: translate3d(0, 100%, 0); }   /* enter from below the screen */
}
.sheet.dragging { transition: none; }                       /* JS-driven frames, incl. the spring settle */
.sheet .head, .sheet .grab { touch-action: none; }
.sheet .list { overflow: auto; overscroll-behavior: contain; touch-action: pan-y; }
.sheet:not(.is-full) .list { overflow: hidden; }            /* list scrolls only at the full detent */
@media (min-width: 900px) {                                  /* desktop side panel */
  .sheet { inset: 0 0 0 auto; height: auto; width: clamp(340px, 32vw, 420px); border-radius: 0;
    transform: translate3d(var(--x, 0px), 0, 0); @starting-style { transform: translate3d(24px, 0, 0); opacity: 0; } }
}
@media (prefers-reduced-motion: reduce) {                    /* HIG: replace x/y movement with fades */
  .sheet { transition: opacity .15s linear; @starting-style { transform: none; opacity: 0; } }
}
```
`@starting-style` is Baseline 2024 (MDN). For an `[hidden]` toggle exit animation add `transition-behavior: allow-discrete` and `display` to the transition list; exits run at about 60 percent of the enter duration. If the sheet is inserted by JS, force the style flush (`getComputedStyle(el).transform`) before removing the `hidden` attribute as a fallback for older engines.
Measure snaps in JS from a probe: `H = sheet.offsetHeight`, `peek = head.offsetHeight + safeBottom`, `snaps = [0, H - 0.5*innerHeight, H - peek]`. Re-measure on `resize`, `visualViewport` resize and orientation change, then re-snap without animation.

### 2.5 Skeleton (state and handlers only)
```js
function makeSheet(el, head, list, snaps /* () => [full, half, peek] as translateY px */, { onSnap } = {}) {
  let y = snaps()[2], d = null, S = [], stop = null;
  const set = v => { y = v; el.style.setProperty('--y', v + 'px'); };
  const down = cy => { stop?.(); el.classList.add('dragging'); d = { y0: y, cy, live: false }; S = [{ y: cy, t: performance.now() }]; };
  const atFull = () => y <= snaps()[0] + 1;
  const wants = dy => !atFull() || (list.scrollTop <= 0 && dy > 0);       // handoff rule
  function drag(cy) {
    const [full, , peek] = snaps(); S.push({ y: cy, t: performance.now() }); if (S.length > 10) S.shift();
    set(band(d.y0 + cy - d.cy, full, peek, innerHeight));
  }
  const nearest = (a, x) => a.reduce((m, c) => Math.abs(c - x) < Math.abs(m - x) ? c : m);
  function end() {
    if (!d) return; const { y0 } = d; d = null;
    const s = S.filter(p => performance.now() - p.t < 100), a = s[0], b = s.at(-1), v = a && b && b.t > a.t ? (b.y - a.y) / (b.t - a.t) : 0;
    const sn = snaps(); let to = nearest(sn, y + v * 180);                 // project 180 ms ahead
    if (Math.abs(v) > .5 && to === nearest(sn, y0)) to = sn[Math.max(0, Math.min(2, sn.indexOf(to) + Math.sign(v)))];  // a flick moves one detent
    stop = spring(y, to, v, set, () => { el.classList.remove('dragging'); el.classList.toggle('is-full', to === sn[0]); onSnap?.(to); }, { w: .016, z: .9 });
  }
  head.addEventListener('pointerdown', e => { down(e.clientY); head.setPointerCapture(e.pointerId); });
  head.addEventListener('pointermove', e => d && drag(e.clientY));
  head.addEventListener('pointerup', end); head.addEventListener('pointercancel', end);
  list.addEventListener('touchstart', e => down(e.touches[0].clientY), { passive: true });
  list.addEventListener('touchmove', e => {
    if (!d) return; const cy = e.touches[0].clientY;
    if (d.live || wants(cy - d.cy)) { d.live = true; if (e.cancelable) e.preventDefault(); drag(cy); }
  }, { passive: false });
  list.addEventListener('touchend', end); list.addEventListener('touchcancel', end);
}
```
Not in the skeleton: a tap on the head (no movement) must run the grabber cycle instead of `end()`, and the dismiss rule from 2.3.

## 3. Columns view: push and pop on phone
### 3.1 Structure
- Desktop and tablet: three columns side by side (spots, records, detail), selection in column N replaces column N+1 in place, no animation beyond the selection highlight.
- Phone (max-width 700px): one column visible. Selecting a spot **pushes** the records column; selecting a record pushes detail. A nav bar shows a Back chevron with the previous title, the current title (large title collapses on scroll), and trailing actions.

### 3.2 History
```js
history.scrollRestoration = 'manual';
let stack = [{ id: 'spots' }];                       // entries: {id, spot?, rec?, top}; top = saved scrollTop
function push(col) {
  stack.at(-1).top = scroller.scrollTop;
  history.replaceState({ stack }, '');               // persist top into the entry we are leaving
  stack = [...stack, col];
  history.pushState({ stack }, '', hashFor(col));    // e.g. #/spots/K1-B2/records/42
  navigate('push');
}
addEventListener('popstate', e => {                  // Back, forward, or edge swipe
  const next = e.state?.stack ?? stack.slice(0, 1);  // no state = entry page or a deep link
  const dir = next.length < stack.length ? 'pop' : 'push';
  stack = next; navigate(dir);
});
const back = () => (history.state?.stack?.length > 1 ? history.back() : replaceWithParent());   // deep-link safe
```
- Max two pushes (records, detail). Switching spots inside the records column uses `replaceState`.
- Deep link to a record: build `cols` from the URL, `replaceState({d: cols.length-1})`, and make Back go to the parent by `replaceState`, since there is no earlier same-site entry. Never leave the app on first Back unless the user is already at the root.
- The Map sheet at half or full also pushes `{sheet: cubby}` so browser Back closes it before leaving the view. Peek does not push.

### 3.3 View Transitions
Same-document transitions (`document.startViewTransition`, MDN). Wrap the DOM swap; MDN notes names must be unique among rendered elements or the transition is skipped.
```js
const reduce = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
function navigate(dir) {
  const update = () => { renderColumns(); scroller.scrollTop = cols.at(-1).scrollTop ?? 0; focusHeading(); };
  if (!document.startViewTransition || reduce() || suppressNext) { suppressNext = false; return update(); }
  document.documentElement.dataset.nav = dir;                         // CSS hook; works everywhere VT works
  const vt = document.startViewTransition(update);
  vt.finished.finally(() => delete document.documentElement.dataset.nav);
}
```
```css
.navbar  { view-transition-name: navbar; }          /* title cross-fades, bar itself stays put */
.col-stack { view-transition-name: col-stack; }
::view-transition-group(*)             { animation-duration: var(--dur-push); animation-timing-function: var(--ease-push); }
html[data-nav=push]::view-transition-old(col-stack) { animation-name: to-left-dim; }
html[data-nav=push]::view-transition-new(col-stack) { animation-name: from-right; }
html[data-nav=pop]::view-transition-old(col-stack)  { animation-name: to-right; }
html[data-nav=pop]::view-transition-new(col-stack)  { animation-name: from-left-undim; }
@keyframes from-right { from { transform: translate3d(100%,0,0); box-shadow: -8px 0 24px rgb(0 0 0/.2); } }
@keyframes to-left-dim { to { transform: translate3d(-30%,0,0); filter: brightness(.85); } }
@keyframes to-right { to { transform: translate3d(100%,0,0); } }
@keyframes from-left-undim { from { transform: translate3d(-30%,0,0); filter: brightness(.85); } }
@media (prefers-reduced-motion: reduce) { ::view-transition-group(*), ::view-transition-old(*), ::view-transition-new(*) { animation: none !important; } }
```
- Reduce Motion: no slide; cross-fade only at 150 ms (HIG: replace x/y transitions with fades). The block above disables it entirely; use `animation: fade .15s` instead if a visible cue is wanted.
- `document.startViewTransition({ update, types: ['push'] })` plus `:active-view-transition-type(push)` is the cleaner API but is newer. **[verify]** support in Safari and Firefox before using; the dataset hook above is the safe path.
- While a VT runs the page does not take input. **[verify]** Keep the duration at or under 350 ms and test rapid tapping.

### 3.4 Back gesture
- iOS Safari already has a system edge-swipe back that fires `popstate` after its own animation. Running a second pop transition double-animates. Heuristic: if a `popstate` arrives within 150 ms of a `touchend` that began at x < 24 px, set `suppressNext = true`. **[verify]** on device; there is no documented same-document signal (the `hasUAVisualTransition` flag is for cross-document `pageswap`).
- View Transitions cannot be scrubbed by a finger. For a real interactive swipe-back (phase 2), keep the previous column mounted in a horizontal track: `track.style.transform = translateX(...)`, drag from x < 20 px, parallax the under-column by 30 percent, release with the section 2.3 velocity projection (commit if projected > 50 percent of width), settle with `spring()`, and on commit call `history.back()` with `suppressNext = true`. Off-screen columns get `inert` and `aria-hidden`. This track approach also makes push and pop interruptible, which VT is not, so it is the better long-term design; ship VT first.
- **Focus:** - After push or pop, focus the new column's `<h1 tabindex="-1">` (the prototype's `focusTitle` already does this for views). On pop, restore focus to the row that opened the column.

## 4. Motion tokens
Apple's current default is a spring, not a Bezier. SwiftUI `.smooth`, `.snappy`, `.bouncy` map roughly to damping ratio 1, 0.85 and 0.7 (bounce 0, 0.15, 0.3). **[verify]** the exact mapping; the CSS values below were generated from that assumption.

```css
:root {
  /* durations (ms) */
  --dur-press-in: 0ms;  --dur-press-out: 180ms;  --dur-fade: 150ms;   --dur-small: 200ms;
  --dur-push: 350ms;    --dur-sheet: 480ms;      --dur-fly: 520ms;    --dur-exit: 260ms;
  /* standard curves */
  --ease-out:  cubic-bezier(.2, .8, .2, 1);        /* matches the prototype's existing curve */
  --ease-in:   cubic-bezier(.4, 0, 1, 1);          /* exits only */
  --ease-push: cubic-bezier(.32, .72, 0, 1);       /* iOS-like sheet/push curve; also used by Vaul. [verify] origin */
  /* springs as linear(), generated from a damped spring step response, settles at 0.4% error */
  --spring-smooth: linear(0, 0.042, 0.135, 0.25, 0.366, 0.475, 0.572, 0.655, 0.725, 0.782, 0.829, 0.866, 0.896, 0.92, 0.938, 0.952, 0.963, 0.972, 0.979, 0.984, 0.988, 0.991, 0.993, 0.995, 1);
  --spring-snappy: linear(0, 0.038, 0.127, 0.241, 0.363, 0.48, 0.587, 0.679, 0.758, 0.821, 0.872, 0.912, 0.942, 0.964, 0.979, 0.99, 0.998, 1.002, 1.005, 1.006, 1.006, 1.006, 1.005, 1.005, 1);
  --spring-bouncy: linear(0, 0.038, 0.131, 0.255, 0.389, 0.522, 0.643, 0.749, 0.836, 0.906, 0.959, 0.996, 1.022, 1.037, 1.044, 1.046, 1.044, 1.039, 1.034, 1.027, 1.021, 1.016, 1.011, 1.007, 1);
}
@media (prefers-reduced-motion: reduce) { :root { --spring-snappy: var(--spring-smooth); --spring-bouncy: var(--spring-smooth); --dur-push: 150ms; --dur-sheet: 150ms; --dur-fly: 0ms; } }
```
`linear()` is Baseline widely available (MDN). Pair each spring with the duration shown, e.g. `transition: transform var(--dur-sheet) var(--spring-smooth)`.

| Interaction | Mechanism | Duration / params | Notes |
|---|---|---|---|
| Press highlight (row, cell, button) | `:active` background | In 0 ms, out 180 ms ease-out | Highlight on touch-down, not on release. Disable text-selection flash. |
| Button press scale | transform | in 80 ms, out `--spring-snappy` 260 ms | Scale 0.97, only for primary and icon buttons, not list rows. |
| Sheet snap after release | JS `spring` | w 0.016, z 0.9, carries velocity | Interruptible. |
| Sheet enter / tap-to-cycle | CSS | `--dur-sheet` `--spring-smooth` | |
| Sheet exit / dismiss | CSS | `--dur-exit` `--ease-in` | Exits are about 60 percent of enter. |
| Push / pop | View Transition | `--dur-push` `--ease-push` | Old column moves 30 percent. |
| Fly to unit / fit room | JS `spring` on centre and log k | w 0.014, z 1 | Interpolate centre and log scale, never x/y/k independently, or the zoom drifts sideways. |
| Pan glide | exponential decay | 0.998^ms | Edge spring-back w 0.02, z 1. |
| Reduce Motion | see CSS above | | Fades only; direct manipulation stays; no bounce; no zoom-in animation. |

**Spring versus ease-out.** Use a spring when: a gesture ends and velocity should carry on; the animation can be interrupted or retargeted; position, scale or size of an object changes. Use ease-out for: non-spatial properties (opacity, colour), fixed-duration entrances with no gesture, and CSS-only transitions. Use ease-in for exits only. Use linear only for progress, opacity cross-fades and the decay in inertia. Use JS springs when you need to inject velocity (CSS cannot), and `linear()` springs when you cannot (tap-driven).

### Haptics (Vibration API)
- Support: Chrome and Firefox on Android; **not iOS Safari**. MDN lists it as not Baseline; the exact matrix was not retrievable in this research **[verify]**. Always feature-detect (`navigator.vibrate?.()`), call only from a user gesture handler (browsers may ignore it without activation), and wrap it in one helper.
- Map to HIG meanings: selection (cubby selected, detent crossed): 6 ms. Light impact (record dropped in a cubby, sheet settles): 10 ms. Success (move confirmed, sync done): `[8, 40, 8]`. Warning or error (rejected drop, sync failed): `[20, 40, 20]`.
- Rules (HIG): short discrete events only, one haptic per cause, never during a continuous pan or pinch, consistent meaning, always paired with a visual change, and a Settings toggle (default on). Wrap in one `tap(kind)` helper that feature-detects and rate-limits to one call per 60 ms. iOS has no supported web haptic API; the hidden `<input switch>` tick trick is unofficial, so do not build on it.

## 5. Density
### 5.1 What Apple does
- iOS Display Zoom scales the whole interface; Dynamic Type scales text and rows grow with it. The HIG asks for at least 200 percent text enlargement without clipping (Accessibility, Layout). Finder list view offers icon-size and text-size options; Mail offers 0 to 5 preview lines, which changes row height. **[verify]** exact option names.
- Layout follows size classes (space available), not device type, and functionality stays the same across classes (Layout).
- HIG control sizes (Accessibility): iOS default 44x44 pt, minimum 28x28; macOS default 28x28, minimum 20x20. Padding: about 12 pt around bezeled elements, 24 pt around unbezeled ones. Type: iOS default 17 pt, minimum 11 pt; macOS 13 and 10.
- Crates policy is stricter than the HIG minimum: **no touch target below 44 px.** Compact saves space in type, thumbnails and padding, never in the hit area.

Implement as CSS custom properties on `:root[data-density="compact"]`. Default is regular. Use `rem` for text so browser font-size settings still apply; on iOS Safari `font: -apple-system-body` can follow Dynamic Type. **[verify]**

| Token | Regular | Compact | Notes |
|---|---|---|---|
| Record row min-height (touch) | 64 px | 48 px | Never under 44. |
| Record row min-height (`pointer: fine`) | 44 px | 32 px | Desktop only; matches macOS default row feel. |
| Cover thumb | 48 px | 36 px | Square, 4 px radius. |
| Title font / line | 17 px / 22 | 15 px / 20 | Weight 600. |
| Secondary line (artist, label) | 15 px / 20 | 13 px / 18 | |
| Meta (year, BPM, catalogue no.) | 13 px / 18 | 12 px / 16 | `tabular-nums`; never below 11 px. |
| Row padding block / inline | 10 px / 16 px | 6 px / 16 px | Keep the 16 px gutter in both. |
| Section header height | 36 px | 28 px | 13 px uppercase, sticky. |
| Icon button visual / hit | 32 px / 44 px | 28 px / 44 px | Hit area extended with `::after { inset: -8px }` or padding. |
| Sheet peek height | 96 px + safe area | 80 px + safe area | |

```css
:root { --row-h: 64px; --thumb: 48px; --fs-title: 1.0625rem; --fs-sub: .9375rem; --fs-meta: .8125rem; --row-py: 10px; }
:root[data-density="compact"] { --row-h: 48px; --thumb: 36px; --fs-title: .9375rem; --fs-sub: .8125rem; --fs-meta: .75rem; --row-py: 6px; }
@media (pointer: fine) { :root { --row-h: 44px; } :root[data-density="compact"] { --row-h: 32px; } }
.row { min-height: var(--row-h); padding-block: var(--row-py); }
```
The playlist and player surfaces keep their larger type (project brief) and ignore compact for the title line. Persist the choice in `localStorage` (try/catch) and expose it as a segmented control in Settings, with a live preview row. A density change animates row height over `--dur-small`, with no layout animation on lists longer than 50 rows.

## 6. Detail checklist (20 items an Apple-quality reviewer checks)
1. **Press feedback within one frame.** `:active` styles appear on touch-down. No `-webkit-tap-highlight-color` flash (set to transparent and supply your own).
2. **No 300 ms tap delay or double-tap zoom** outside the canvas: `touch-action: manipulation` on interactive elements (MDN: alias for pan-x pan-y pinch-zoom, no click delay).
3. **Hit areas at least 44x44 px** with at least 8 px between neighbours; small visuals use hit slop (`::after` inset). Check with the 44 px overlay in DevTools.
4. **Focus rings.** `:focus-visible` shows a 2 px ring at 2 px offset, 3:1 contrast against both adjacent colours, in both themes; no ring on mouse click. Cubbies in the SVG/DOM canvas are focusable (`tabindex="0"`, role button, label "K1 B2, 14 records").
5. **Disabled states.** Controls stay in place at 38 to 40 percent opacity, `aria-disabled` (not removed), still explain why on focus or long-press ("Nothing to undo").
6. **Scroll chaining and overscroll.** Sheet list, columns and side panel use `overscroll-behavior: contain` (MDN: stops chaining, keeps bounce). The canvas uses `none`. Body does not scroll while the Map is open (`position: fixed` shell or `overflow: hidden`).
7. **Text truncation.** One-line titles use `min-width: 0` plus `text-overflow: ellipsis` inside flex rows; secondary lines clamp to 2. Truncate in the middle only for catalogue numbers. Never truncate an address like `K1·B2`; shrink the label first.
8. **Number alignment.** `font-variant-numeric: tabular-nums` for BPM, year, counts, track durations; right-align numeric columns in the desktop table; thousand separators from `Intl.NumberFormat`.
9. **Images never shift layout.** Covers have `aspect-ratio: 1`, a neutral placeholder colour, `decoding="async"`, `loading="lazy"` below the fold, and a 150 ms opacity fade-in on load. Cumulative layout shift is 0.
10. **Large lists stay at 60 to 120 fps.** `content-visibility: auto` with `contain-intrinsic-size` on rows, virtualisation past about 300 rows, no layout reads in scroll handlers, only `transform` and `opacity` animated.
11. **Interruptible everything.** Test: start a sheet snap, touch it mid-flight, drag away. It follows the finger with no jump. Same for fly-to and push/pop.
12. **Scroll position and selection survive navigation.** Popping restores the exact `scrollTop`; returning to the Map restores `T`; the selected row stays highlighted when re-entering.
13. **Safe areas everywhere.** Notch landscape left/right (`env(safe-area-inset-*)`), home indicator under sheet content and player, status bar; test with an iPhone 15 Pro landscape frame. The existing prototype pattern `max(16px, env(...))` is the reference.
14. **Text scaling to 200 percent.** Rows grow, no clipping or overlap, the sheet peek grows with its title, and the nav bar wraps rather than truncates actions. Use `rem` and avoid fixed heights on text containers.
15. **Reduce Motion, Reduce Transparency, Increase Contrast.** `prefers-reduced-motion` (fades only, no bounce), `prefers-contrast: more` (solid separators, stronger ring), `prefers-reduced-transparency` where blur is used. Check 4.5:1 text contrast in light and dark (HIG: up to 17 pt needs 4.5:1).
16. **Hover only where hover exists.** Wrap hover styles in `@media (hover: hover)`; no sticky hover after touch; desktop rows use the default arrow cursor, not `pointer`, except for links.
17. **Gesture alternatives and accessibility.** Zoom in, zoom out and fit buttons; grabber is a button that cycles detents; drag-and-drop move has a "Move to..." menu path; sheet is `role="dialog"` with `aria-modal="false"` at peek and half; canvas has `role="application"` only if keyboard handlers exist, otherwise a labelled `role="group"` with the cubbies as buttons.
18. **Keyboard parity.** Esc closes the sheet or panel and returns focus to its trigger; arrows move through rows in Columns; Left/Right collapse to the parent column (Finder behaviour); `/` or Cmd/Ctrl+K focuses search; tab order follows visual order and never enters off-screen (inert) columns.
19. **Honest states.** Empty (an empty cubby says "Empty" with an Add action), loading (skeleton rows at final height), error (what failed and a Retry), offline. Simulated features say they are simulated (project rule in `CLAUDE.md`). Destructive actions use Undo toasts, not `confirm()`.
20. **Optimistic and consistent feedback.** Moves update the UI at once, toast mirrors the button label ("Move..." then "Moved to K1·B3"), failures roll back with a spring and an error haptic, and the same action gives the same animation and sound/haptic in both views. Haptics and motion toggles live in Settings.

## 7. Build order and open questions
Order: tokens and density variables; `spring()` and the canvas behind a flag with +/-/fit buttons; the sheet with fly-to-above-sheet; Columns push/pop with VT and history, then the track-based edge swipe. Playwright (`CRATES_NO_PATCH=1`): two-touch pinch via CDP, ctrl-wheel, sheet drag with velocity, no horizontal scroll at 390 px, reduced-motion emulation, Back restores `scrollTop`. Device-only: iOS Safari (edge swipe, safe areas), Android Chrome (vibrate), Safari and Chrome trackpad pinch.

Unverified, in priority order: iOS edge-swipe back versus same-document VT (3.4); Safari `gesture*` pinch (1.2); sheet-to-list handoff within one gesture (2.2); VT `types` support; Vibration API matrix; the SwiftUI spring mapping and `.998` constant; `interactive-widget` and `scrollsnapchange` support. Not covered here: the Navigation API (not Baseline, so avoided).
