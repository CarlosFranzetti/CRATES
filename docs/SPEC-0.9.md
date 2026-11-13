# Crates 0.9 build spec (lead: Fable; builders: Sonnet/Haiku agents)

Shared rules for every work package (WP). Read CLAUDE.md first.

- One file, `crates.html`. Keep the section order (TDZ). Each WP adds its CSS in its own marked block directly before `</style>` (`/* ==== WP-x: name ==== */`) and its JS in its own marked block directly before the line `/* ---------- Claude photo recognition (optional) ---------- */`. Register actions with `Object.assign(A, {...})` inside your block. Touch existing functions only where this spec says so, with the smallest possible edit.
- Colors and sizes through the existing CSS variables (`--bg --surface --surface-2 --ink --muted --line --accent --accent-ink --f-display --f-body --f-mono --row-h`). No new glows, gradients or drop shadows: the look is about to get leaner. Sentence case copy. Every user string through `esc()`. No alert/confirm/prompt. Moves through `place()`. Undo through `lastUndo = ...`.
- State lives in `S` (saved to localStorage by `save()`), view state in `V`. New persisted fields must be sanitised in `migrate()` (see how `r.tracks`/`r.videos` are handled) and must tolerate being absent.
- Must work at 390x844 and 1440x900, in both looks, with no page scroll and no sideways scroll. Touch targets 44px.
- Tests: add tests to `tests/test_crates.py` (style of `r11_delete_and_upload`, registered in the `TESTS += [...]` block as `("W<x>NN name", fn)`), run `CRATES_NO_PATCH=1 python3 tests/test_crates.py` and finish with every test passing. Syntax check with the command in CLAUDE.md.
- Work only in your worktree. Commit there (message `WP-x: ...`). Do not push, do not touch README/docs other than a short `docs/WP-x-NOTES.md` (what you built, decisions, open issues).

## Shared data shapes

- Lending: `r.lent = {to, phone, since:'YYYY-MM-DD', note} | null`; history in `r.lentLog = [{to, phone, since, back}]`. Reminder bookkeeping: `S.remind = {[recordId]: 'YYYY-MM-DD' last nudged/dismissed}`. Overdue = 14 days after `since`, then every 7 days.
- Photos: `r.photos = [{id, kind:'cover'|'label'|'back'|'other', at, w, h}]`; bytes in IndexedDB (`crates-photos`, store `photos`: `{id, blob, thumb}`); `r.coverSrc = 'discogs'|'personal'` (default: discogs when `r.cover` exists, else personal when a personal cover photo exists, else generated art); `r.coverPhoto = photoId|null`.
- Capture inbox: `S.inbox = [{id, photos:[photoId], status:'queued'|'identifying'|'matched'|'review'|'aside'|'failed', guess:{artist,title,label,catno}|null, recordId|null, at}]`.
- Hooks between WPs (call only if defined): `photoSection(r)` returns HTML for the Detail sheet (WP-C defines, WP-A calls); action `detail` with `data-r` opens the Detail sheet (WP-A defines, WP-B and WP-C call); `stackView(list)` returns the flip-stack HTML for a spot (WP-B defines).
