# WP-A notes: Detail sheet and lending

## What was built

- **Detail sheet.** `openEditRecord(id)` is now the Detail sheet (kept the name and the `er-*` field ids, so existing hooks and tests still work). New action `detail` (`data-r`) opens it; `edit-rec` is an alias. Visible buttons now say "Detail" (record info, Now Playing sheet, table "Lent to" cell). Sections are collapsible `<details>`: Discogs metadata, Lending, Notes, Your own fields, Tracklist. Desktop is two columns (cover, id, spot chip, Play and Preview, facts, `photoSection(r)` slot on the left; forms on the right); phones get a full-height sheet with a sticky Save bar.
- New editable fields beyond the old sheet: country, format(s) (`r.formats`, entered as `A / B`), genres, all styles, barcode, date added. Release id is a read-only link to Discogs. Saves go through the old mechanics: one `lastUndo` snapshot (now also restoring keys that did not exist and `S.remind`), `r.orig` is never touched, edited fields keep the dot and the "Undo edit" revert link.
- **Lending.** `r.lent = {to, phone, since, note} | null`, `r.lentLog = [{to, phone, since, back}]`, `S.remind = {recordId: day}`. "Since" defaults to today when a name is first typed. "Returned" (in Detail, the record info, the banner and the Lending sheet) clears `r.lent`, appends to `r.lentLog`, drops the snooze, and is undoable.
- **Indicators.** "Lent out" pill on `recordRows` (both normal and select mode), a "Lent to Sam · 16 days" line in `recInfo`, a `Lent out` chip in `T_FILTERS`, a sortable `Lent to` table column (opens Detail). Lent records keep their `loc`/`home` untouched.
- **Reminders.** `dueReminders()`: 14 days after `since`, then again 7 days after each "Remind me next week" (`S.remind[id]` = that day). `render()` shows a slim banner at the top of `#main` and a count badge on the Collection tab (desktop tabs and the phone tab bar). Buttons: "Text <name>" (`sms:<digits>?body=<friendly text>`, hidden without a phone), "Mark returned", "Remind me next week", "Lending".
- **Lending sheet** (`lending` action; from the banner and Settings -> Your collection): grouped by person with per-record and per-person actions, recently returned, "Email me this list" (`mailto:` with `lendingDigest()`), and "Send via server" (only when `API.ok`).
- **`api/remind.js`**: POST `{digest, to?}`; needs `RESEND_API_KEY` and `REMIND_EMAIL` (optional `RESEND_FROM`), else 503 with the missing names. Never called automatically.
- **`migrate()`** sanitises `lent`, `lentLog`, `S.remind` (and `country`, `dateAdded`, `genres`, `styles`, `formats`, which Discogs sync writes but migrate had skipped; `formats` objects are flattened to strings).
- Tests WA01 to WA07 in `tests/test_crates.py`.

## Decisions and deviations

- The banner's "Mark returned" is only shown when exactly one person is due (with several people it would return everyone's records in one tap). "Text X" appears once per person who has a phone number; "Remind me next week" applies to all due records.
- "Next week" is exactly 7 days after the snooze date (not "until the next 7-day boundary after the 14th day").
- `api/remind.js` uses `json()` from `_lib.js` but not `env()` (that helper only knows the Discogs variables). `to` is accepted but must equal `REMIND_EMAIL` (400 otherwise); the mail always goes to `REMIND_EMAIL`, so the endpoint cannot be used to mail strangers.
- The sheet's visible buttons switched from `data-act="edit-rec"` to `data-act="detail"`, so the existing tests that clicked `[data-act=edit-rec]` were updated to `[data-act=detail]`.
- `R10` (density) was already failing on the base commit (the flat look sets its own row height, so compact density changes nothing). The test now measures density in the Shop look.
- Detail uses `:has(.dt)` to widen/full-height the generic `.sheet` (no change to `openSheet`).

## Open issues

- The Discogs-synced `formats` shape is flattened to plain strings on load; if a later WP wants the structured form it should store it under another key.
- `mailto:` bodies are cut at 1500 characters for long lists (some mail clients cap URLs).
- Reminders only appear while the app is open; there is no push or scheduled email (by design).
