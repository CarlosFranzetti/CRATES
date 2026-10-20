# Bugs

Known issues in the Crates prototype (`crates.html`) and the database (`app/db/`). When you fix one, move it to **Fixed** with the commit, and add or point to a test that would catch it coming back. Code-review findings and the full error-handling audit are in [QA.md](QA.md).

Severity: **High** means it crashes or loses data, **Medium** means a feature is broken or the layout breaks, **Low** means it's cosmetic or a minor wrong behavior.

## Open

| ID | Severity | Area | What happens | Notes / proposed fix |
|---|---|---|---|---|
| B-101 | Low | Cubby move | Moving a named cubby onto a cubby that already has a subtitle overwrites it without asking ("A1 → A2" loses "Acid"). | Undo restores it. Ask which subtitle to keep, or keep both ("Acid / Detroit & Chicago"). |
| B-102 | Low | Gigs | During load-out, unticking "packed" on a record that was already in the gig's bag before the gig moves it out to its home shelf. | Remember the pre-gig location per gig item and restore that instead. |
| B-103 | Low | Collection | Changing **Home spot** on a record that's sitting on a shelf also moves the record there. | By design today (on a shelf, home follows location). Decide: separate "Move to" and "Set home" columns? |
| B-104 | Low | Deep links | Deep links and QR codes in the claude.ai preview point at the artifact URL, which only the owner can open. | They'll point at the Vercel site once it's deployed, because `BASE_URL` picks the site's own origin. |
| B-105 | Medium | Player | YouTube can't embed inside the claude.ai preview, so play opens YouTube in a new tab and the fallback chain only runs as a dry run. | Expected in the preview. Verify inline playback and the chain on the Vercel deploy. |
| B-106 | Medium | Barcode | Barcode lookups return example pressings, not real Discogs data. | Simulated on purpose. The real app calls `GET /database/search?barcode=` server-side with a Discogs token. |
| B-107 | Medium | Discogs sync | "Save locations to Discogs" only queues updates; "Sync now (demo)" marks them saved without calling Discogs. | Simulated on purpose. Needs a server job using the collection custom-fields endpoints within the 60 requests/min limit. |
| B-108 | Low | Data | Unit ID prefixes (K/S/C/B) and gig status names differ between the prototype and `docs/DATA_MODEL.md` / `003_features.sql`. | Pick one set before the React port. See the open questions in PRD.md. |
| B-109 | Medium | DB | `records.discogs_instance_id` isn't unique per owner, so a re-import could duplicate rows. | Add a unique index on `(owner_id, discogs_instance_id) where discogs_instance_id is not null`. |

## Fixed

| ID | Severity | What was wrong | Fix | Test |
|---|---|---|---|---|
| B-001 | High | First visit with no saved data crashed: the state block ran before the helper `const`s existed (TDZ), so the published preview could fail to load. | Moved the state block below the helpers. Tests now run with `CRATES_NO_PATCH=1`. | 01 Boot |
| B-002 | High | Naming or moving a cubby on a unit added this session crashed (`labels` undefined). | New units get `labels:{}`; the handlers guard with `||= {}`. | X9, X10 |
| B-003 | Medium | A malformed deep link (`#%E0%A4%A`) threw in `decodeURIComponent` and stopped the player from starting. | `try/catch` around the decode. | X11 |
| B-004 | Medium | The QR stickers sheet scrolled sideways at 390px (long unbroken URL). | `overflow-wrap:anywhere` on the URL. | N13 |
| B-005 | Low | Cubby subtitles overlapped the record count on the big shelf drawing. | Label is clipped with an ellipsis before the count. | X13 |
| B-006 | Low | The subtitle toast named the wrong cubby when you clicked another chip before pressing Enter. | Capture the cubby key when the change fires. | X12 |
| B-007 | Low | The deep-link hash was never cleared, so reopening the same sticker link did nothing and refresh always jumped back. | `history.replaceState` after routing. | X14 |
| B-008 | Low | Collection thumbnails rendered at 15px. | Override the `.mini-btn svg` size for covers. | N14 |
| B-009 | Low | With "Not played in a year" on, Play queued the whole cubby. | Play uses the filtered list. | — |
| B-010 | Low | After a 12-second timeout the barcode library loader stayed stuck until reload. | Reset the loader on timeout. | — |
| B-011 | Medium | Earlier fixes: an empty cell plus arrow key plus Undo crashed; a record filed straight into a bag couldn't unpack; removing a unit left records pointing at it; slot changes wiped typed fields; "Undo edit" lost unsaved fields; the playlist picker allowed duplicates; 4px of overflow at 390px from the sleeve stack. | See commits before `74425ac`. | X1–X8, 14 |

## How to report

Add a row to **Open** with: steps to reproduce, expected and actual behavior, the browser and window size, and the console error if there is one. If you're an agent in the swarm, also add a failing test (`tests/test_crates.py`, named `X<n> …`) in the same PR.
