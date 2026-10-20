# Crates: product requirements

Crates is the "Vinyl DJ Librarian": an app that knows where every record in a DJ's collection physically is, and plays it.

- Owner and first user: Carlos "Los" Franzetti. Repo: github.com/CarlosFranzetti/crates.
- Last updated: 2026-10-20.
- This file replaces the earlier draft at `docs/PRD.md` (removed; see git history). That draft numbered its flows F1 to F9; this file regroups them and adds everything the prototype gained since.
- Companion files: [LIST.md](LIST.md) (every feature, with build status), [FUTURE.md](FUTURE.md) (ideas), [HOWTO.md](HOWTO.md) (using and developing), `docs/` (data model, architecture, player spec, roadmap, infra).

## Status in one paragraph

What exists is a single-file prototype, `crates.html` (HTML, CSS and vanilla JS, no build step). It runs a full demo collection (3 places, 10 records) and keeps all data in the browser's localStorage. Anything that needs a server is either simulated or skipped: Discogs lookups, Discogs write-back, photo recognition outside the claude.ai preview, shared data. A Postgres schema (Neon project `crates`) is applied and seeded but nothing reads it yet. Every flow below says what the prototype does today.

## Problem

A working DJ with hundreds of records across Kallax shelves, milk crates and record bags cannot answer "where is it?" quickly, and cannot see what is out of its home slot after a gig. Discogs and spreadsheets know what you own, not where it is right now. Typing in 800 records is why most collections never get cataloged.

## Users

1. **The owner (v1).** One DJ with a phone in one hand and a record in the other, at home or packing a bag. Wants speed, one-handed use, and an app that looks good enough to keep open.
2. **Other working DJs (later).** Same needs. The schema already has `owner_id`, but v1 ships no sign-up, sharing or public pages.
3. **Collectors (later).** Care more about duplicates, condition and value than about gigs. Served by the same data, with different defaults.

## Goals

- Capture physical places (furniture, crates, bags) by photo and preset, then capture records into them.
- Answer "where is this record" in one search: "Kallax 1, shelf A2 (Acid)" or "bag Crater".
- Browse a place shelf by shelf, or All, flipping through sleeves.
- Move one record in two taps, many records in one pass, and a whole bag from one photo.
- Remember where a record came from and where its home slot is, with undo on every change.
- Let the owner correct Discogs data and add BPM, key, rating, condition, tags, notes and custom fields without losing the original values.
- Track gigs: pack, play, bring home, and keep set history.
- Play the collection through the player ported from the Discogs stream app.

## Non-goals (v1)

- Selling, marketplace pricing, wantlist.
- Audio analysis (BPM and key detection). Those fields are typed by hand.
- Multi-user sharing, public profiles, collaboration.
- Offline-first sync. The app is online; the prototype happens to work offline for local data.
- Digital files, Rekordbox or Serato export.
- Native apps. The target is a web app that works well on a phone.

## Principles

1. **Physical first.** The unit of organization is the thing you can touch: this Kallax, this bag. Addresses read the way a DJ talks.
2. **One or two taps.** Moving a record, putting it in a bag, sending it home: never more than two taps from the record.
3. **Never auto-commit a guess.** Photo and barcode results are proposals. Nothing is saved until the owner confirms. Low-confidence guesses start unticked.
4. **Discogs is the source of record data; the owner's edits win.** The Discogs snapshot is kept untouched. Edited fields are marked, can be reset, and are never overwritten by a re-sync.
5. **Everything is undoable.** A move, a scan apply, a cubby swap, a playlist change.
6. **A dead link never stalls a set.** Playback falls through its chain on short timeouts and never cuts off audio that is already playing.
7. **Honest about simulation.** Where the prototype fakes a server answer, the screen says so.

## Addressing

- Each unit has an ID: `K1`, `K2` (Kallax and Expedit), `S1` (other shelving), `C1` (crates and boxes), `B1` (bags). The owner can type any ID up to 6 letters or digits.
- Cubbies are a row letter plus a column number: top row `A1..A4`, next row `B1..B4`, then `C`, `D`. A 2x2 has `A1..A2` and `B1..B2`.
- A shelf code always carries the unit ID, written `K1·B2`, so it never reads like a Discogs side or track position ("B2").
- A cubby may have a subtitle: `K1·A2 (Acid)`.
- Bags and crates have names ("Crater"). Their location is the unit alone, never a cell.
- Deep links: `#K1` opens a unit, `#K1-A2` opens a cubby and flashes it. QR stickers carry these links.

## Flows and acceptance criteria

### 0. Navigation model (2026-10-20)

The page never scrolls; each view scrolls inside itself. Room has two layouts the owner can switch between, remembered per device: **Map** (the furniture drawn on a pannable, pinch-zoomable canvas; a spot's records in a side panel on desktop or a snapping bottom sheet on phones) and **Columns** (spots → records → record, one column at a time on phones with push/pop). Phones use a bottom tab bar with Add in the middle. A density setting (regular / compact) tightens rows and bars.

- AC0.1 At 390×844, 844×390, 1280×800 and 1440×900 the document never scrolls and never scrolls sideways; only panes do.
- AC0.2 Tapping a cubby on the map selects it without moving the map; double-tap zooms to its unit; Fit room restores the fitted scale.
- AC0.3 A plain tap on the map never pans; a pan never fires a tap. A pinch zooms around the fingers' midpoint.
- AC0.4 On phones the sheet snaps to peek, half and full; the list scrolls only inside the sheet.
- AC0.5 In Columns on a phone, the hardware back button pops one column; ‹ › step to the neighbouring spot without going back.
- AC0.6 ← → flip records and ↑ ↓ step spots in both layouts when no field has focus.
- AC0.7 The chosen layout, look and density survive a reload.

### 0b. Backups, files and Discogs import

- AC0b.1 Four backup slots, newest first; one is written before every import, restore and reset; the oldest is dropped at five.
- AC0b.2 Restore writes a backup of the current collection first and is confirmed in-page.
- AC0b.3 Save to file produces a JSON the app loads back unchanged; a non-Crates file is refused with a toast.
- AC0b.4 A Discogs CSV export imports with quoted fields intact; records already owned (normalised artist + title) are skipped and the count is shown; new records are Unplaced until filed.
- AC0b.5 Upload to Discogs is queued per record and sent only from the server, within the rate limit.

### 1. Capture furniture and bags

The owner picks a preset (or a custom grid), picks a finish or color, names it, optionally photographs it, and it appears in the room.

- AC1.1 A Kallax 2x4 yields cubbies `A1..A4`, `B1..B4`; a 2x2 yields `A1..A2`, `B1..B2`. A custom grid takes 1 to 10 rows and columns.
- AC1.2 IDs are unique. The app proposes the next free one for the type; the owner can edit it.
- AC1.3 The container photo, when given, replaces the drawing as the unit's cover everywhere.
- AC1.4 Finish or bag color (preset swatches or a custom color) and name can be changed later from "Look & name".
- AC1.5 A unit that still holds records cannot be removed. Removing an empty unit asks for confirmation; records that had it as a home slot become homeless.
- Prototype: built. 64 furniture presets and 41 bag presets, drawn in the app. Photos are shrunk to 900 px and stored in the browser.

### 2. Capture records into a place

The owner picks a destination slot, photographs the shelf or types the records, reviews what was found, and files them.

- AC2.1 From the room to confirmed records in at most 3 taps plus the shutter.
- AC2.2 Every proposed record is shown before saving. A record is pre-ticked unless the model reports low confidence or it matches a record the owner already has. Those start unticked.
- AC2.3 Nothing is saved before confirm. A filed record gets location = home = the chosen slot (bags and crates get no home slot).
- AC2.4 A record the photo pass cannot read can be typed in without leaving the sheet.
- AC2.5 Owning a record already triggers the duplicate warning (flow 11).
- Prototype: partly simulated. Photo recognition works only when the page can send images to Claude (the claude.ai preview). On its own site it shows a notice and the owner types records. Matches are not checked against Discogs; the real app does that on the server.

### 3. Search

- AC3.1 One box searches artist, title, label, catalog number, year, style, BPM, key, tags, notes and cubby names. Every typed word must match.
- AC3.2 Each result shows its place: "Kallax 1, shelf A2 (Acid)" or `Bag "Crater"`.
- AC3.3 A record that is away from home shows a visible cue and its home slot.
- AC3.4 Choosing a result opens its place with the record focused and the cubby flashing. Units match by name or ID too.
- AC3.5 Target for the real app: under 300 ms on a 2,000-record collection (trigram indexes exist in the schema).
- Prototype: built, in memory.

### 4. Flip through a place

- AC4.1 A unit shows chips: All plus one per cubby, each with a count. Empty cubbies are shown.
- AC4.2 Flip is a sleeve stack with swipe or arrow-key navigation. Neighbors are tappable. A list below mirrors the stack.
- AC4.3 Each record shows its facts (label, catalog number, year, style, BPM, key, rating, tags, notes), its place, where it came from if it is in a bag, and its home slot if it is away.
- AC4.4 Order inside a cubby is stable between visits (open question 1).
- Prototype: built. Order is insertion order.

### 5. Move records

- AC5.1 Move one: tap Move, then a destination. The picker offers quick buttons for the home slot and up to three recent targets, then every shelf and bag. The home slot is outlined.
- AC5.2 Moving to a shelf sets both current location and home. Moving to a bag or crate sets current only.
- AC5.3 "Put in bag" is one tap when there is a single bag. "Back to <home slot>" is one tap.
- AC5.4 Multi-select: tick records in a cubby, then move them together or put them in a bag.
- AC5.5 Move a whole cubby to another slot, optionally taking its subtitle. Swap two cubbies, optionally swapping subtitles. Home slots follow the records.
- AC5.6 A toast with Undo follows every move. The prototype toast stays up 5 seconds; the target for v1 is 8 seconds. Undo restores locations, homes and the Discogs sync queue.
- AC5.7 Moves are recorded in history with a reason: `move`, `cubby_move`, `swap`, `scan`, `unpack`, `gig_pack`, `gig_return`, `undo`, `add`.
- Prototype: built. History is not shown in the UI yet; the database schema has it.

### 6. Bags and scan-to-reconcile

The owner opens a bag, takes one photo of the fanned-out records, reviews, and applies.

- AC6.1 The review lists **Into bag** (found, not yet in the bag) and **Not in bag** (in the bag, not found, going to its home slot), with a count.
- AC6.2 Apply is one undoable step. Dismissing the sheet changes nothing.
- AC6.3 A record missing from the photo returns to its home slot. If it has no home, it stays in the bag and the review says so.
- AC6.4 The owner can tick or untick any record before reviewing. Records the photo shows that are not in the collection are listed as "Not in your collection yet".
- AC6.5 "Unpack to home slots" sends everything in a bag home in one tap, with undo.
- AC6.6 Records in a bag show where they came from.
- Prototype: the reconcile logic is built. Recognition is real only inside the claude.ai preview; elsewhere "Simulate a scan" picks a plausible result so the review step can be tried.

### 7. Gigs

- AC7.1 Create a gig with name, venue, date, a bag or crate, and optionally a playlist to start from.
- AC7.2 Four steps in order: Plan, Load out, At the gig, Back home. Then a summary.
- AC7.3 Ticking a record in Load out moves it into the gig's bag and remembers where it came from. Unticking puts it back.
- AC7.4 At the gig lists only packed records. Ticking "played" writes a play (gig date, venue) to the record's set history.
- AC7.5 Back home ticking returns a record to its home slot. Unticked records are flagged Missing in the summary, and the owner can check more in.
- AC7.6 Records can be added to a gig one by one or from a playlist, and the whole list can be played.
- Prototype: built.

### 8. Set history

- AC8.1 "Log a play" takes a date and a venue.
- AC8.2 A record shows last played, play count, and the last few plays.
- AC8.3 "Not played in a year" is a dig list (also a filter chip in a unit) with Play these and Save as playlist. Records never logged count as not played.
- Prototype: built.

### 9. Playlists

- AC9.1 Create, rename, color, duplicate, delete with confirm and undo.
- AC9.2 Reorder by dragging the handle or with up and down buttons. Sort by pull order (by shelf), artist, year, BPM, or reverse; sort is undoable.
- AC9.3 Add from the playlist, from any record ("+ Playlist"), or from a gig. A playlist item shows where the record is right now.
- AC9.4 "Pack into bag" moves every record in the playlist into the chosen bag; home slots stay.
- Prototype: built. Drag reorder is pointer-based; keyboard users use the up and down buttons.

### 10. Player

Full spec in `docs/PLAYER.md`.

- AC10.1 A mini player bar opens a slide-up sheet. The vinyl uses the cover as its label, shows grooves, dust and a sheen, and spins only while playing.
- AC10.2 The Up next list uses a large font (20 px titles, 15.5 px artist lines in the prototype). Each row shows a status dot (working, trying, not working, pending) and where the record is.
- AC10.3 Each record has up to several YouTube links. A track with no signal inside 3 seconds, or a stall after 12 seconds while buffering, moves to the next link. A video shorter than 30 seconds is treated as a teaser and skipped. When all links fail the track is marked not working and skipped. Audio that is already playing is never cut by the 3-second window.
- AC10.4 Tapping a not-working track retries its links.
- AC10.5 Where YouTube cannot embed (inside the claude.ai preview), the play button opens YouTube instead. On Crates' own site it plays inline.
- AC10.6 In link mode, a dry run visualizes the fallback chain without needing a failure.
- Prototype: built, except the server re-search step (shown in the chain, no backend), the quota notice, link prefetch and the background verifier.

### 11. Edit details

- AC11.1 Editable: artist, title, label, catalog number, year, style, BPM, key, media and sleeve condition (Goldmine grades M to P), rating (0 to 5), tags, notes, and any number of custom name/value fields.
- AC11.2 A field that differs from the Discogs value shows a dot and an "Undo edit" action that restores the original.
- AC11.3 A re-sync from Discogs never overwrites an edited field (database rule; the prototype has no sync).
- Prototype: built.

### 12. Duplicates

- AC12.1 While adding, matching on artist and title (normalized: case, accents, leading "The", punctuation) or on barcode shows "You already own this. It's in <place>" with a Show it button.
- AC12.2 The file button then reads "Add another copy". Two copies are two records with their own locations.
- AC12.3 Photo results that match an owned record start unticked. Pressing candidates from a barcode show "You own a copy" with its place.
- Prototype: built.

### 13. Barcode

- AC13.1 Type the digits or photograph the barcode. Decoding tries the browser BarcodeDetector, then ZXing (loaded from a CDN), then Claude vision when available.
- AC13.2 Fewer than 8 digits is rejected with a hint.
- AC13.3 A barcode lookup returns candidate pressings (format, country, year, label, catalog number). The owner picks one and the form fills in.
- Prototype: decoding is real; the candidates are labeled example data. The real app calls Discogs `/database/search?barcode=` from the server.

### 14. Save locations to Discogs

- AC14.1 A setting, off by default, queues a "Location" custom-field value for each record: `K1·A2 (Acid)`, `Bag: Crater`, `Crate: Milk crate`.
- AC14.2 Later moves overwrite the pending value for the record. A record is "Saved" once its value was written.
- AC14.3 Writing respects the Discogs rate limit (60 requests a minute authenticated).
- Prototype: simulated. "Sync now (demo)" marks the queue as saved. The database has the outbox (`discogs_sync_queue`) and a trigger. The value format in the prototype and in the trigger differ slightly (open question 8).

### 15. QR stickers and deep links

- AC15.1 One sticker per unit, and optionally one per cubby, in 1, 1.5 or 2 inch sizes, laid out on US Letter pages at actual size.
- AC15.2 Output: print (when hosted on its own site), a print-ready page (.html that opens the print dialog), SVG, and PNG (first page only).
- AC15.3 Each QR code opens the app at that unit or cubby (`#K1`, `#K1-A2`) and the cubby flashes.
- Prototype: built. Inside the claude.ai preview and on localhost, codes point to the published artifact link, not to the local address.

## Data and privacy

- **Where data lives.** Prototype: the browser only (localStorage key `crates-demo-v3`, photos included). Clearing site data deletes it. Real app: Neon Postgres, every query scoped to the owner.
- **Discogs terms** (from `research/features.md`, read from the API Terms of Use):
  - Do not cache or store Discogs content longer than needed to serve the app. Do not display content more than 6 hours older than Discogs shows it. The schema keeps a snapshot for owner reference; this needs a decision before any public launch (open question 9).
  - Show "Data provided by Discogs." with a link to discogs.com next to Discogs data, and the line "This application uses Discogs' API but is not affiliated with, sponsored or endorsed by Discogs."
  - Discogs images are Restricted Data: no passing to third parties, no commercial use, no mirroring to storage. Use the owner's own photos as covers; fetch Discogs art through an authenticated proxy for display only. The prototype uses generated placeholder covers.
  - A personal token is server-side only. Send a descriptive User-Agent. Stay under 60 requests a minute.
  - A paid tier would need written permission from Discogs and a design that works without Discogs images.
- **Photos.** They can show the owner's home. Store privately, serve short-lived signed URLs, strip EXIF location before upload, cap size.
- **Photo recognition.** Output is untrusted text. It is used only as search input, never as a command, URL or query.
- **No analytics or third-party trackers** in the prototype. It loads YouTube (player), ZXing (barcode fallback, on demand) and Google Fonts.

## Success measures

- Time from "I want X" to its location: under 10 seconds.
- A 60-record bag reconciled in under 2 minutes including review.
- Share of photo-added records that need no manual correction (tracked on a labeled photo set).
- Share of tracks that play first time without a skip.
- Share of records with a home slot: above 95 percent after the first full inventory.

## Release scope

**v1 (real app, single owner):** sign-in; furniture, bags and presets; capture by photo with Discogs confirmation; search; flip; moves with undo and history; bag scan and reconcile; edits with snapshot; playlists; player with the full fallback chain; gigs and set history; duplicates and barcode; QR stickers; Discogs Location write-back; Discogs import of an existing collection.

**Later:** see [FUTURE.md](FUTURE.md). Highlights: offline PWA, smart crates, export to Rekordbox or Serato, photo-sweep re-inventory, lending, value report, multi-user.

## Open questions for the owner

1. **Order inside a cubby.** Alphabetical by artist, manual drag order, or newest first?
2. **Crates and boxes.** Do they need sections (front and back), or is the unit enough?
3. **Bag capacity.** Warn when a bag passes its preset's rough capacity?
4. **Whole-record playlist items.** Play all tracks with links, or one chosen track?
5. **Existing Discogs collection.** Import it first and use photos only to locate, or build entirely by photo?
6. **Duplicates.** Two copies of a release are separate records with their own locations (assumed). Confirm.
7. **Unit ID letters.** The prototype uses K (Kallax, Expedit), S (other shelving), C (crates, boxes), B (bags). `docs/DATA_MODEL.md` says K, B, M, X. Pick one set.
8. **Discogs Location text.** Prototype writes `K1·A2 (Acid)` and `Bag: Crater`; the database trigger writes `K1·A2` and `Crater`. Which form, and should it include the subtitle?
9. **Snapshot storage.** Keep the Discogs snapshot in the database (needed for "Undo edit") or store only IDs and refetch, to stay inside the caching terms?
10. **Gig statuses.** The prototype has planning, packing, out, return, done. The database has planning, packed, out, returned. Align them.
11. **Undo window.** 5 seconds (prototype) or 8 seconds (older spec)?
12. **Name.** "Crates" collides with crates.app and "Kallax" is an IKEA trademark. Decide before a public launch whether UI copy says "cube shelf".
