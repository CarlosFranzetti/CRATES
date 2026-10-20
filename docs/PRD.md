# Crates: Product Requirements

Last updated 2026-10-20. Owner and first user: Carlos "Los" Franzetti.

## Problem

A working DJ with hundreds of records spread across Kallax shelves, milk crates and record bags cannot answer "where is it?" quickly, and cannot see what is out of its home slot after a gig. Spreadsheets and Discogs lists know *what* you own, not *where it is right now*. Cataloguing 800 records by typing is the reason it never gets done.

## Users

1. **The owner (v1).** One DJ, phone in hand at the shelf, at home or packing a bag. Wants speed, one-handed use, a good-looking app.
2. **Later, other DJs.** The schema is already multi-owner (`owner_id`), but v1 ships no sign-up flow, sharing or public pages.

## Goals

- Photograph furniture and bags, then photograph records, and have them land in the database with Discogs data.
- Answer "where is this record" in one search: "Kallax 2, shelf B2" or "bag Crater".
- Browse a unit shelf by shelf, or "All", and flip through the records.
- Move one record in one or two taps. Reconcile a whole bag from one photo.
- Track current location and home slot, with history and undo.
- Let the owner correct Discogs data and add BPM, key, rating, condition, notes, tags and custom fields without losing the original.
- Play the collection with the discogs-stream player: spinning vinyl, large-font playlist, YouTube links with redundant fallbacks.
- Organise records into playlists.

## Non-goals (v1)

- Selling, marketplace pricing, wantlist (discogs-stream has these; not ported).
- Audio analysis (BPM/key detection). Fields are manual.
- Multi-user sharing, public profiles, collaboration.
- Offline-first sync. The app is online; cached views are best effort.
- Digital files, Rekordbox/Serato export. Possible later.
- Barcode scanning (possible later; Discogs search by barcode is cheap to add).

## Addressing (summary; full rules in [DATA_MODEL.md](DATA_MODEL.md))

Each unit has an id (`K1`, `K2`, `B1`). Kallax cubbies are row letter plus column number: a 2x4 is `A1..A4` / `B1..B4`, a 2x2 is `A1..A2` / `B1..B2`. A shelf code always carries the unit id, **`K2·B2`**, so it never reads like a Discogs side/track position. Bags are named ("Crater"); the photo of the container is its cover.

## Core flows

### F1. Capture furniture and bags

Pick a preset (many Kallax sizes and finishes, other shelving, milk crates with a color, boxes, DJ bags such as UDG and Magma with per-bag colors), photograph it, name it. The app assigns the id and shows the grid.

- AC1.1 A Kallax 2x4 yields cells `A1..A4`, `B1..B4`; a 2x2 yields `A1..A2`, `B1..B2`. A custom grid takes rows and columns.
- AC1.2 Ids are unique per owner, prefixed by type, assigned on create, never reused after delete.
- AC1.3 The container photo is the unit's cover everywhere (room view, search result, bag picker).
- AC1.4 Finish and bag color are editable per unit after creation.
- AC1.5 A unit that still holds records cannot be deleted; the user is offered "move records first".

### F2. Shelf-by-shelf capture

Open a unit, choose a cell, photograph the spines or covers in it. The app proposes Discogs matches, the user confirms, records are added to that cell.

- AC2.1 From unit to confirmed records in at most 3 taps plus the shutter.
- AC2.2 Every proposed record shows cover, artist, title, label, year and a confidence cue. Pre-checked only when vision confidence is high **and** the Discogs match is exact; everything else starts unchecked.
- AC2.3 Nothing is saved before confirm. A confirmed record has a Discogs snapshot, tracks, and a location with current = home.
- AC2.4 A record the vision pass cannot read can be added by manual Discogs search without leaving the cell.
- AC2.5 A second photo of the same cell does not duplicate records already there.

### F3. Search

- AC3.1 Typing artist or title returns matches within 300ms for a 2,000-record collection (trigram indexes).
- AC3.2 Each result shows its place: "Kallax 2, shelf B2" / `K2·B2`, or "bag Crater".
- AC3.3 A record that is not at home shows a visible "away" cue and its home slot.
- AC3.4 Tapping a result opens its unit at that cell with the record focused.

### F4. Flip through a unit

Tapping a unit shows its cells and an "All" option. A cell or All opens a flip view of the records.

- AC4.1 "All" lists every record in the unit; a cell filters to that cell.
- AC4.2 Flip is swipe or arrow driven, with large cover art, and works one-handed.
- AC4.3 Cells show a count. Empty cells are shown, not hidden.
- AC4.4 Order within a cell is stable between visits (rule decided; see open questions).

### F5. Move one record

From the flip view or a search result.

- AC5.1 Two taps at most: Move, then the destination (recent destinations first, then any cell or bag).
- AC5.2 Moving to a shelf sets both current and home; moving to a bag sets current only.
- AC5.3 A toast with Undo for 8 seconds. Undo restores the previous location and records an `undo` event.
- AC5.4 Every move is in the record's history with timestamp.

### F6. Bag scan and reconcile

Photograph the whole bag. The app lists the records it recognises among the owner's records, the user reviews, applies.

- AC6.1 Review shows two lists: **Going in** (not yet in the bag) and **Returning home** (in the bag, not seen).
- AC6.2 Apply is one atomic operation; either everything changes or nothing does.
- AC6.3 Records missing from the photo go to their home slot. A record with no home stays unplaced and is flagged.
- AC6.4 Unrecognised spines are shown and can be matched by hand or ignored; they never block apply.
- AC6.5 History records `scan` for records placed in the bag and `unpack` for records returned.
- AC6.6 Dismissing the review leaves nothing changed (the scan stays unapplied).

### F7. Play

Tap a record, shelf, bag, search result or playlist to start playback. Full spec in [PLAYER.md](PLAYER.md).

- AC7.1 The player slides up from a mini bar; the vinyl shows the cover as its center label, grooves, dust and a pulse glow, and spins only while playing.
- AC7.2 The queue list uses a larger font than discogs-stream (title 18px / artist 15px by default).
- AC7.3 A track with no working link never leaves the user in silence for more than about 3 seconds plus search time: it resolves or is skipped. A playing or buffering track is never interrupted by that timeout.
- AC7.4 A region-blocked or teaser link recovers through the alternate link, then one forced re-search, then skip.
- AC7.5 When the YouTube API quota is exhausted, playback continues via quota-free search and the UI shows a quiet note with an Open in YouTube action.
- AC7.6 Links that failed are dimmed in the list; tapping one retries it silently before it plays.

### F8. Playlists

- AC8.1 Create, rename, duplicate, delete (with confirm).
- AC8.2 Reorder by drag (touch long-press, keyboard alternative); the order survives reload.
- AC8.3 Add from a shelf, a bag or search results, with multi-select and a one-tap "add to last used".
- AC8.4 A playlist item shows where the record is right now.

### F9. Edit fields

- AC9.1 The owner can edit artist, title, label, catalog number, year, BPM, key, rating (0-5), media and sleeve condition, notes, tags and custom fields.
- AC9.2 Edited Discogs-derived fields are marked as edited; "reset to Discogs" restores the original value.
- AC9.3 Re-sync from Discogs never overwrites an edited field.
- AC9.4 Custom fields are free-form name/value pairs and are searchable.

## Success measures

- Time from "I want X" to its location: under 10 seconds.
- A 60-record bag reconciled in under 2 minutes including review.
- Share of records added by photo that need no manual correction (tracked in the vision eval set).
- Share of tracks that play first time without a skip.

## Open questions for the owner

1. **Order inside a cell.** Alphabetical by artist, manual drag order, or most recently added at the front?
2. **Crates and boxes.** Do they need sections (front/back), or is the unit enough?
3. **Bag capacity.** Warn when a bag exceeds its preset's rough capacity (about 60 LPs)?
4. **Whole-record playlist items.** When a record is added to a playlist, play all tracks with links, or only one chosen track?
5. **Existing Discogs collection.** Import it first (token or CSV) and use photos only to *locate*, or build entirely by photo?
6. **Duplicates.** Two copies of the same release: separate records with their own locations (assumed)?
7. **Unit prefixes.** `K` Kallax, `B` bag, `M` milk crate, `X` box. Keep, or letters you prefer?
