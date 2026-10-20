# Crates: the big list

Every feature, screen, control, preset group, data field, table and integration, with its status. Last updated 2026-10-20. Summary and rationale are in [PRD.md](PRD.md); ideas beyond this list are in [FUTURE.md](FUTURE.md).

## Legend

- `[x]` built in the prototype (`crates.html`) and working as described.
- `[~]` simulated or partial in the prototype. The note on the line says what is fake.
- `[ ]` not built yet.

In the database sections, `[x]` means the table or object exists in the Neon project `crates` (per `docs/DATA_MODEL.md`). The prototype does not read or write the database.

## Totals

- 64 furniture presets in 6 groups (40 shelving, 24 crates and boxes); 138 finish entries across them (33 with wood grain, 7 gloss).
- 41 record-bag presets from 12 brands; 73 color entries.
- 16 database tables, 1 view, 5 functions, 4 triggers (from `001` and `003`).
- 3 demo places (Kallax 1, bag Crater, Milk crate), 10 demo records, 2 playlists, 2 gigs.

## 1. App shell

- [x] Single-file page, no build step, no framework, no dependencies except an inlined QR generator
- [x] Top bar: Crates logo, tabs (Room, Playlists, Gigs), Add button, Settings button
- [x] Search box under the bar, always visible
- [x] Mini player bar pinned at the bottom once something is queued
- [x] Sheets (modal panels) for add, move, scan, edit, settings, stickers, pickers
- [x] Toast with Undo after changes (5 seconds)
- [x] Light and dark themes that follow the system setting
- [x] Reduced-motion support (no sheet animation, no vinyl spin or glow, no tonearm motion)
- [x] Footer note: demo data, placeholder art, changes stay in this browser
- [x] Responsive layout: two columns on wide screens, one column below 780 px
- [x] Safe-area padding for phones (added by the build wrapper)
- [ ] Sign-in
- [ ] Install as an app (PWA manifest, service worker)
- [ ] Manual light/dark toggle (the CSS supports a `data-theme` attribute; there is no control)

## 2. Room view

- [x] "Your room" grid of unit cards: name, ID tag, drawing or photo, preset and finish, record count
- [x] Header line: total records and number of places
- [x] "Play collection" button (queues every record)
- [x] "Not played in a year" button with a live count
- [x] "QR stickers" button
- [x] Tap a card to open the unit
- [x] Furniture drawn in the app, not images:
  - [x] Kallax with shaded cubbies, wood grain and gloss finishes
  - [x] Cube cabinets, ledges and bins drawn from the preset style
  - [x] Record bags with texture (nylon, canvas, metal, board), stitching and a name tag
  - [x] Bag forms: shoulder, sling, trolley (flap, bar, wheels), backpack, tote, hard case (corners, handle)
  - [x] Milk crates with grid holes, wooden crates with slats, hard cases with ribs
  - [x] Record spines peek out of each drawing, so a full unit looks full
- [x] Photo as cover: an uploaded photo replaces the drawing everywhere

## 3. Furniture presets (64)

Grid is rows x columns. Finish counts come from the research data. "Set your own sections" means the real grid is unknown, so the owner edits rows and columns.

- [x] **IKEA Kallax** (10): Kallax 1×4 · 42×147 cm; Kallax 2×2 · 77×77 cm; Kallax 2×4 · 77×147 cm; Kallax 2×4 with 2 doors + 4 drawers · 147×77 cm; Kallax 2×4 on underframe · 147×94 cm; Kallax TV bench on underframe · 147×39×78 cm; Kallax 3×3 · 112×112 cm; Kallax 3×4 · 112×147 cm; Kallax 4×4 · 147×147 cm; Kallax 5×5 · 182×182 cm
- [x] **IKEA (other)** (12): Eket cube cabinet 35x35x35 cm; Eket storage combination with legs; Eket storage combination with feet; Besta frame/cabinet; Tonstad cabinet with doors; Bror cabinet with 2 doors; Ekenabben cabinet; Vittsjo shelf unit; Expedit 2×2; Expedit 4×2; Expedit 4×4; Expedit 5×5
- [x] **Record furniture** (15): Zomo VS-Rack Vinya 150; Zomo VS-Rack Vinya 100; Mapleshade Record Shelf System; LP Bin (unnamed model); Department Chicago Walnut Record Cabinet; Dual Portland cabinet; Can-Am LPCAB29; Siosi Record // LP Shelving; Symbol Audio Aero 51in media cabinet; Symbol Audio Aero 76.5in LP storage console; Atocha Record Cabinet; Gothic Furniture LP Record Rack; Cubitec 13.25in-deep cube kit; Boltz LP Record Storage Rack (4 shelves); Custom grid
- [x] **Wall & bins** (3): Wax Rax LP-V4 vertical rack; Record store browser/flip bin; Wall-mounted LP display ledge
- [x] **Crates** (7): Wax Stacks crate; Vinyl Styl Original LP Crate (VS-RS-04); Vinyl Styl Metro LP Crate (VS-RS-05); Studio 57 Vinyl Record Crate (wood); Crosley Record Storage Crate; Plastic milk crate, 16 qt (13x13x11 in); Wooden apple/produce crate
- [x] **Record boxes & cases** (17): Glorious Record Box 110; Glorious Record Box Advanced 110; Glorious Record Box 230; Glorious Record Rack 330; Zomo VS-Box 100/1; Zomo VS-Box 100/2; Zomo VS-Box 100/4; Zomo VS-Box 50; Zomo VS-Rack Loft; Zomo VS-Rack Wave; Zomo VS-Rack Cube; UDG Ultimate 12" Vinyl Record Case 80; Odyssey Flight Zone FZLP80 utility case; Hama 50 LP Vinyl Record Storage Case; Pro-Ject Rack It - Basic Cube; Keep Them Spinning The Standard modular wood cube; Corrugated cardboard 12in record box

## 4. Record-bag presets (41)

Shape, texture and capacity come from the research data. Capacity is the maker's figure and real-world fit is lower with outer sleeves.

- [x] **UDG** (9): Ultimate SlingBag Trolley Set DeLuxe MK2 (~90); Ultimate SlingBag Trolley DeLuxe (~60); Ultimate SlingBag MK2 (~45); Trolley To Go (~40–50); Ultimate 7" SlingBag 60 (~60); Ultimate StarterBag (~50); Ultimate SoftBag 60 (~60); Ultimate SoftBag 90 / 90 Slanted (~90); Ultimate Backpack Slim (~7)
- [x] **Magma** (10): LP-Bag 100 Trolley (~90); Riot LP-Trolley 50 (~40–45); Riot LP-Bag 50 with Trolley Sling (~50); LP-Bag 40 II with Trolley Sling Straps (~40); LP Bag II 42640 (courier style) (~40); LP-Bag 60 Profi (~60); LP 100 Profi Bag (Capacity not listed); 12" Sandwich (~60); Solid Blaze Vinyl Bag (~50); Solid Blaze Vinyl-Trolley (~60 7" singles)
- [x] **Zomo** (4): VS-Box 50 (~50–60); VS-Box 100 (~100–120); Technics BackBag (45 LPs) (~45); Technics DJ-Bag (~60)
- [x] **Glorious** (3): Record Box Advanced 110 (~110); Record Box 110 (~110); Record Rack 330 (~330)
- [x] **Reloop** (2): 80 Record Case (~80); Club Series 120 Trolley Case (~120)
- [x] **Odyssey** (6): CLP100P Carpeted Record Case (~100); CLP200P Pro Record/Utility Carpeted Case (~200); Flight Zone FZLP80 (~80); Flight Zone FZLP120HW (trolley) (~120); Krom KLP70BL / KLP1 (~70); Krom KLP2 Stacking Record Case (~70)
- [x] **Gator** (1): ONYX Case for 12" Vinyl (~50–70)
- [x] **Gorilla** (1): GC-LP100 Flight Carry Case (~100)
- [x] **Selektor** (1): Worker DJ Record Bag (~50)
- [x] **Crosley** (2): Record Carrier Case (~30); Platter-Pak (~30)
- [x] **HumminGuru** (1): Vinyl Record Tote Bag (~30)
- [x] **Generic** (1): Canvas Record Tote (preset template) (~20–30)

Bag capacities are in LPs unless stated; "Capacity not listed" means the maker gave none.

### Bag forms (41 presets)

- [x] Hard case (17), shoulder bag (12), trolley (6), sling (2), backpack (2), tote (2)

### Bag textures

- [x] Nylon (22), metal (8), board (7), canvas (4)

## 5. Finishes and colors

- [x] Per-preset finish swatches from the research data (Kallax: White, Black-brown, White stained oak effect, and more depending on size)
- [x] Fallback finish sets by style when a preset lists none: cube (White, Black-brown, White stained oak effect, Oak effect, High-gloss white, Grey), ledge, milk crate, wood crate, case
- [x] Per-preset bag colors (for example Zomo Technics DJ-Bag: 9 colors)
- [x] Milk crate colors: the preset lists 12; the fallback set has 8 (Blue, Red, Black, Green, Yellow, White, Orange, Grey)
- [x] Custom color picker on any furniture or bag
- [x] Wood grain effect on finishes marked grain; gloss highlight on finishes marked gloss
- [x] Changeable after creation from "Look & name"
- [~] Hex values are close matches to maker color names, not sampled swatches (stated in the app footer)

## 6. Addressing and IDs

- [x] Unit IDs by type: K (Kallax and Expedit), S (other shelving), C (crates, boxes), B (bags); next free number proposed
- [x] Editable ID, up to 6 letters or digits, uppercased, must be unique
- [x] Cubby codes: row letter plus column number (A1, B2), rows A to Z then AA
- [x] Shelf code always includes the unit ID: `K1·B2`
- [x] Cubby subtitles: `K1·A2 (Acid)`, up to 28 characters
- [x] Bags and crates addressed by name ("Crater"), never by cell
- [x] Long form in search and warnings: "Kallax 1, shelf A2 (Acid)" and `Bag "Crater"`
- [x] Short form in chips and pickers: `K1·A2` or the bag name
- [x] Custom grid: 1 to 10 rows and columns
- [x] Rows and columns editable on any shelving preset before adding
- [x] Capacity text shown per preset
- [ ] Capacity per cubby editable and used for a "shelf is full" hint
- [ ] Parse typed addresses (`K2 B2`, `k2-b2`) into a jump (the database doc defines the pattern; the deep link `#K1-A2` is the only parser built)

## 7. Add flows

### Add chooser

- [x] Three tiles: Record, Furniture, Record bag

### Add furniture

- [x] Group filter chips (6 groups)
- [x] Preset grid with a drawn preview, grid size and capacity per tile
- [x] Finish swatches plus custom color
- [x] Live preview of the chosen look
- [x] Name, ID, rows, columns, photo fields
- [x] Photo shrunk to 900 px JPEG before saving
- [x] Opens the new unit after adding

### Add bag

- [x] Brand filter chips (All plus 12 brands)
- [x] Preset grid with preview
- [x] Color swatches plus custom color
- [x] Bag name, ID, photo (becomes the cover)

### Add record

- [x] Step 1: pick a destination (any cubby, bag or crate) on tappable grids; defaults to the open cubby
- [~] Step 2a: photograph the shelf or bag; works only when the page can send images to Claude (claude.ai preview); on its own site the option is hidden and a notice says so
- [x] Step 2b: type artist, title, label, year, catalog number
- [x] Found list with tick boxes; low-confidence and duplicate matches start unticked
- [x] "Add to <slot>" files the ticked records
- [x] Duplicate warning and "Add another copy" (section 13)
- [x] Barcode box with digits input and photo input (section 13)
- [x] New record gets a generated cover (palette and pattern from its name)
- [ ] Look up the typed record on Discogs and fill cover, tracklist, YouTube links
- [ ] Import an existing Discogs collection

### Edit and remove a unit

- [x] "Look & name": rename, change finish or color, replace or remove photo
- [x] Remove a unit, with confirm; disabled while it holds records
- [ ] Reorder units in the room
- [ ] Duplicate a unit's layout

## 8. Unit view and flip

- [x] Unit header: back to room, name, ID tag, preset, finish, capacity
- [x] Big drawing of the unit with chips below: All plus one per cubby, each with a count and subtitle
- [x] Selected cubby is highlighted; a deep link or search result flashes it for about 2.6 seconds
- [x] Subtitle field for the selected cubby (Enter or leaving the field saves; empty removes)
- [x] Sleeve stack: current sleeve plus two neighbors on each side, scaled and rotated
- [x] Tap a neighbor sleeve to jump to it
- [x] Previous and next round buttons, disabled at the ends
- [x] Big play button for the current record
- [x] Record panel: title, artist, label, catalog number, year, style, BPM, key, star rating, tags, notes
- [x] Dot marker on fields that differ from the Discogs value
- [x] Place chip, "came from" chip when in a bag, "home" chip when away from home
- [x] Plays line (last played, count, recent dates)
- [x] Discogs Location line when sync is on (Saved or Waiting to sync)
- [x] Buttons: Move, Put in bag, Back to home slot, Edit details, + Playlist, Log a play, Discogs link
- [x] Full list of the cubby or unit under the stack, with the current row highlighted
- [x] In All view, each list row shows its place
- [x] For bags and crates, each row shows where the record came from
- [x] "Play" button plays the open cubby or the whole unit
- [x] Empty states for an empty cubby, an empty bag, and "everything played this year"
- [x] "Not played in a year" filter chip
- [x] "Select records" chip (multi-select)
- [x] "QR sticker" chip for this unit
- [ ] Sort control inside a cubby
- [ ] Drag a record from one cubby to another in the drawing
- [ ] Cubby capacity bar

## 9. Search

- [x] Searches artist, title, label, catalog number, year, style, BPM, key, tags, notes, place, cubby subtitle
- [x] All typed words must match (any order)
- [x] Up to 8 records and 3 units per query
- [x] Each result: cover, title, artist, long address, place chip
- [x] Choosing a result opens the unit at the record's cubby, focuses the record, flashes the cubby, scrolls into view
- [x] Unit results match name or ID
- [x] Empty result message lists what is searched
- [x] Results close on outside click or Escape
- [ ] Typo tolerance and fuzzy match
- [ ] Search history
- [ ] Barcode scan from the search box ("do I own this?" in a shop)

## 10. Moving records

- [x] Move one: sheet with quick buttons (Home, up to 3 recent) and every shelf and bag as tappable grids
- [x] Current slot disabled; home slot outlined
- [x] Shelf target sets current and home; bag or crate target sets current only and remembers the origin
- [x] Put in bag: one tap if there is one bag, otherwise the move sheet
- [x] Back to home slot: one tap
- [x] Unpack to home slots: whole bag, records with no home stay and are counted in the toast
- [x] Multi-select: tick records, Select all, Move N, Put in bag
- [x] Move whole cubby to another slot (optionally take the subtitle)
- [x] Swap two cubbies (optionally swap subtitles); home slots follow the records
- [x] Recent targets remembered (last 3)
- [x] Undo for every move, multi-move, cubby move, swap, scan apply, pack
- [~] History: the prototype keeps no event list; the schema has one
- [ ] "Where was this last?" history view
- [ ] Move by scanning two QR stickers (record's shelf, then target)

## 11. Bags and scan

- [x] Scan bag sheet from a bag's page
- [~] Photo scan: Claude vision reads the photo and matches it to the collection, only when the page can send images; otherwise the option is hidden
- [~] Simulate a scan: picks all but one of the bag's records and two others, so the review step can be tried
- [x] Found list with tick boxes (all records, found ones first); correct what the scan missed
- [x] "Not in your collection yet" list for unknown sleeves seen in the photo
- [x] Review changes: lists Into bag and Not in bag (to home slot) with before and after
- [x] Notice for unticked records with no home slot
- [x] "Everything already matches" notice
- [x] Apply as one undoable step; toast with count
- [ ] Review on the real photo with boxes drawn over the recognized records
- [ ] Add the unknown sleeves from the scan in one tap

## 12. Record details

- [x] Edit sheet: artist, title, label, catalog number, year, style
- [x] BPM, key
- [x] Media condition and sleeve condition: M, NM, VG+, VG, G+, G, F, P
- [x] Rating: 1 to 5 stars, tap again to clear
- [x] Tags (comma separated)
- [x] Notes (free text)
- [x] Custom fields: add, edit, delete name/value pairs
- [x] Undo edit per field, shows only for fields that differ from the original
- [x] Dot marker next to edited fields in the flip view
- [x] Details search (BPM, key, tags, notes are searchable)
- [ ] Re-sync from Discogs that respects edits (rule is in the schema)
- [ ] Per-track BPM, key and notes (columns exist on `tracks`)
- [ ] Cue points and transition notes
- [ ] Delete a record
- [ ] Photo of the actual copy (condition shots)

## 13. Duplicates and barcode

- [x] Duplicate check on artist and title (case, accents, leading "The" and punctuation ignored)
- [x] Duplicate check on barcode
- [x] Warning while typing: "You already own this. It's in <place>", with Show it
- [x] Button changes to "Add another copy"
- [x] Photo results that match owned records start unticked
- [x] Barcode digits input; Enter or Look up
- [x] Barcode photo decode: BarcodeDetector (EAN-13, UPC-A, EAN-8, UPC-E), then ZXing from a CDN, then Claude vision when available
- [x] Fewer than 8 digits rejected with a hint
- [x] Already-owned barcode shown before any lookup
- [~] Candidate pressings: three example pressings labeled as example data; the real app calls Discogs `/database/search?barcode=`
- [x] Pick a candidate: fills artist, title, label, year, catalog number, barcode
- [x] Candidates show a "You own a copy" chip with its place
- [ ] Real Discogs barcode search with format and country filters
- [ ] Catalog-number and matrix search
- [ ] Continuous barcode scanning in a shop

## 14. Playlists

- [x] Playlists tab with cards (cover strip, name, count, number of places)
- [x] New playlist; name edited inline; 6 colors
- [x] Add records from a picker with filter (artist, title, shelf)
- [x] "+ Playlist" on any record: pick a playlist or make a new one
- [x] Play and Shuffle
- [x] Drag to reorder with the handle (pointer drag)
- [x] Up and down buttons per row
- [x] Remove a row, with undo
- [x] Sort: pull order (by shelf), artist, year, BPM, reverse; undoable
- [x] Each row shows number, cover, title, artist, BPM, place
- [x] Duplicate ("X copy")
- [x] Delete with confirm and undo; records stay
- [x] Pack into bag: all records move to the chosen bag, homes kept
- [x] Start a gig from a playlist
- [ ] Keyboard reorder on the drag handle
- [ ] Per-track playlist items (whole records only)
- [ ] Playlist notes and total runtime
- [ ] Facet filters (genre, label, decade)

## 15. Player

### Shell

- [x] Mini bar: spinning vinyl, title, artist, status, previous, play or pause, next
- [x] Slide-up sheet from the bar; closes with the grab handle, a close button, Escape, or a drag down (90 px)
- [x] Source and position line ("K1·A1 · 3 of 8")
- [x] Facts under the title (label, year, BPM, place)
- [x] Buttons in the sheet: Edit details, + Playlist, Show on shelf
- [x] Tabs: Up next, YouTube links, Fallback chain

### Vinyl

- [x] Black disc, three groove rings, dust specks seeded from the record
- [x] Cover as center label, spindle hole, light sheen
- [x] Spins only while playing; pause freezes the angle
- [x] Pulse glow while playing
- [x] Tonearm that swings on when playing
- [x] No spin or glow with reduced motion

### Queue

- [x] Up next list in large type (20 px titles, 15.5 px artist lines)
- [x] Status dot per row: working, trying, not working, pending
- [x] Not-working rows dimmed; tapping retries the links
- [x] Play from any cubby, unit, playlist, gig, "not played" list, or the whole collection
- [x] Row shows where the record is
- [ ] Shuffle button in the player (shuffle exists on playlists)
- [ ] Seek by dragging the timeline (the bar shows progress only)
- [ ] Skip 5 seconds back and forward
- [ ] Per-track playback (the prototype plays one link set per record)
- [ ] Lock-screen controls (Media Session)

### Playback chain

- [x] Primary link first, then cached alternates in order
- [x] 3-second window: no playing or buffering state means the link failed
- [x] 12-second stall check while buffering
- [x] Teaser guard: video shorter than 30 seconds is treated as bad
- [x] Record with no saved link: marked not working and skipped after 3 seconds
- [x] All links failed: marked not working, skipped
- [x] End of video goes to the next record
- [x] Links tab lists primary and alternates with their failure reason; each opens on YouTube; plus a YouTube search link
- [x] Fallback chain tab with five steps highlighted as they run
- [x] Dry run: animates the chain without a real failure (button shown only in link mode, when inline playback is unavailable)
- [x] Event log (last 30 lines)
- [x] Link mode when YouTube cannot embed: play button opens YouTube; shows a notice
- [~] "Force a fresh search" step: shown in the chain and the dry run; the prototype has no backend to search
- [ ] Error-code handling (100, 2, 5 terminal; 150, 101 recoverable)
- [ ] Autoplay retry loop after skips
- [ ] Prefetch of the next 4 records' links
- [ ] Background link verifier and weekly rescan
- [ ] Quota notice with "Open in YouTube"
- [ ] Dead-list guard (stop after one lap of not-working tracks)
- [ ] Save which link worked back to the database

## 16. Gigs

- [x] Gigs tab: cards (date, venue, name, step, record count)
- [x] New gig: name, venue, date, bag or crate, start from a playlist
- [x] Step bar: Plan, Load out, At the gig, Back home
- [x] Plan: add records (picker), add a whole playlist, remove records
- [x] Load out: tick to pack (record moves into the bag, origin remembered); progress bar; "Head out (N left behind)"
- [x] At the gig: list of packed records; tick played (writes a play with the gig date and venue)
- [x] Back home: tick to return to the home slot; progress bar
- [x] Finish: summary of played count, Missing list, played list
- [x] Check in more (reopen) when records are missing
- [x] Back to plan from load out
- [x] Play the whole list from the gig
- [x] Delete gig with confirm; records stay where they are, set history is kept
- [x] Unticking undoes the move
- [ ] Setlist order and notes per gig
- [ ] Shared packing list for a back-to-back set
- [ ] Gig reminders

## 17. Set history

- [x] Log a play: date (defaults to today) and venue
- [x] Last played, count and recent plays on each record
- [x] "Over a year ago" tag on stale records
- [x] "Not played in a year" sheet with date or "never logged", Play these, Save as playlist
- [x] Same filter as a chip in a unit
- [x] Plays written by gig ticks, removed again when unticked
- [x] Undo for a logged play
- [ ] Edit or delete a single play
- [ ] Play counts and charts

## 18. Discogs

- [~] "Discogs" button on a record opens a Discogs search page for artist and title (a search, not the release page)
- [~] Save locations to Discogs (setting): queue and "Sync now (demo)" that marks values as saved without calling Discogs
- [x] Location value formats: `K1·A2 (Acid)`, `Bag: Crater`, `Crate: Milk crate`
- [x] Queue keeps one pending value per record; later moves overwrite it
- [x] Queue restored by undo
- [x] Count of waiting updates and saved records in Settings
- [ ] Token or OAuth connection
- [ ] Import collection (folders, instance IDs)
- [ ] Release fetch: tracklist, videos, images, identifiers
- [ ] Real write-back at 60 requests per minute with backoff
- [ ] Rate-limit header reading
- [ ] "Data provided by Discogs." attribution and the non-affiliation line
- [ ] Image display through an authenticated proxy

## 19. QR stickers and deep links

- [x] Sticker sheet from the room, a unit page, or the unit chip
- [x] Pick units with chips; "One per cubby too" toggle
- [x] Sizes: 1, 1.5, 2 inch
- [x] Live preview of every sticker
- [x] Sticker design: QR (error correction M), code text (`K1·A2`), subtitle or unit name on 1.5 and 2 inch
- [x] Letter pages, 0.5 inch margins, 0.125 inch gaps: 54 stickers per page at 1 inch, 24 at 1.5, 12 at 2
- [x] Page count shown
- [x] Save print-ready page (.html; opens the print dialog at actual size)
- [x] Save SVG (all pages)
- [x] Save PNG (first page, 3x)
- [x] Print button (hidden in the claude.ai preview)
- [x] Deep links: `#K1` and `#K1-A2` open the unit or cubby and flash it; work on page load and on hash change
- [~] Link base: published artifact link inside the preview, on localhost and from a file; the page's own address when hosted
- [ ] Short URLs per unit (`/u/<token>`; the column exists)
- [ ] Label printer formats (Dymo, Brother)
- [ ] Log of printed stickers (table exists)

## 20. Settings

- [x] Accent color: Signal red, Brass, Booth cyan
- [~] Save locations to Discogs: on or off (default off), queue status, "Sync now (demo)"
- [x] Addressing explainer
- [x] Reset demo collection (confirm; restores the 10 demo records)
- [ ] Compact playlist text size
- [ ] Pulse and rainbow-pulse toggles for the vinyl
- [ ] Units (inches or centimeters) and capacity defaults
- [ ] Export all data (JSON, CSV)
- [ ] Import data
- [ ] Account, sign out

## 21. Keyboard, pointer and gesture interactions

- [x] Left and right arrow: previous and next record in the open unit (not while typing or when a sheet or the player is open)
- [x] Escape: close the player, then a sheet; close search results
- [x] Search box: up and down move the highlighted result, Enter opens it, Escape closes
- [x] Enter in a subtitle field saves it
- [x] Swipe the sleeve stack left or right (40 px threshold)
- [x] Tap a neighbor sleeve to jump
- [x] Drag the playlist handle to reorder (pointer, works with touch)
- [x] Drag down on the player grab handle or vinyl deck to close (90 px)
- [x] Tap the scrim outside a sheet to close it
- [x] Tap the mini bar to open the player
- [x] Focus moves into a sheet when it opens; visible focus ring on all controls
- [x] Print dialog from the sticker sheet
- [ ] Long-press to start a drag on touch
- [ ] Keyboard shortcuts for move, play, next
- [ ] Pinch or double-tap on the sleeve to zoom

## 22. Accessibility and polish

- [x] Buttons have labels; icon buttons use aria-label
- [x] Chips and toggles expose pressed state
- [x] Dialogs have role and label; toasts use role status
- [x] Cubby buttons read as "Kallax 1 A2" with "(current)" when applicable
- [x] Screen-reader-only labels for search and form fields
- [x] Dark theme
- [x] Reduced motion
- [ ] Full screen-reader pass ("Kallax 2, row B, column 2" names everywhere)
- [ ] 44 px target audit
- [ ] Contrast audit of all finishes
- [ ] Loading skeletons (not needed until there is a server)

## 23. Prototype data and persistence

- [x] All state in the browser (`localStorage`, key `crates-demo-v3`), saved after every change
- [x] Photos stored as data URLs in the same place
- [x] Schema migration on load (adds gigs, sync queue, labels, plays, barcodes)
- [x] Falls back to the demo collection if stored data is unreadable or refers to missing presets
- [x] Works when storage is blocked (data lasts until reload)
- [x] Reset to demo
- [ ] Export or import of the browser data
- [ ] Sync to the database

### Demo collection

- [x] Kallax 1 (2x4, K1) with subtitles on A1 "Detroit & Chicago" and A2 "Acid"
- [x] Bag "Crater" (B1)
- [x] Milk crate (C1, blue)
- [x] 10 records: Model 500, Rhythim Is Rhythim, Mr. Fingers, Joey Beltram, Phuture, Josh Wink, 808 State, Inner City, A Guy Called Gerald, Daft Punk
- [x] 3 of them in Crater with home slots on Kallax 1
- [x] 2 playlists: Warm-up, Acid hour
- [x] Seeded gigs and plays so history and "not played" have content
- [x] Generated placeholder covers; YouTube IDs on each record

## 24. Database (Neon project `crates`)

Region aws-us-east-2, Postgres 17, extensions `pgcrypto` and `pg_trgm`. Files: `app/db/001_init.sql`, `002_seed.sql`, `003_features.sql`, `004_seed_features.sql`. Seed owner is `demo`.

### Tables from 001

- [x] `units`: code, name, kind (shelf, crate, bag, box, wall, bin), preset_key, rows, cols, finish name and hex, photo_url, sort
- [x] `records`: Discogs release and master IDs, `discogs_snapshot`, artist, title, label, catno, year, country, format, genres, styles, cover_url, bpm, musical_key, rating, condition_media, condition_sleeve, notes, tags, custom, edited_fields, timestamps
- [x] `tracks`: position, title, duration_s, bpm, musical_key, notes
- [x] `media_links`: provider, external_id, rank, status (pending, working, non_working), last_checked_at
- [x] `record_locations`: current unit and cell, home unit and cell, moved_at
- [x] `location_events`: from and to, reason, time
- [x] `playlists`: name, description, color, sort
- [x] `playlist_items`: position, optional track, note
- [x] `bag_scans`: photo, found (jsonb), applied

### Tables and objects from 003

- [x] `cell_labels`: cubby subtitles
- [x] `record_locations.prev_*`: came-from slot, filled by trigger `record_locations_track_prev`
- [x] `records.barcode`, `records.discogs_instance_id`
- [x] `records.dup_key`: generated from `record_dup_key(artist, title)`, indexed with owner
- [x] Indexes on `(owner_id, discogs_release_id)` and `(owner_id, barcode)`
- [x] `barcode_lookups`: barcode, candidates, chosen release
- [x] `discogs_sync_queue` (pending, done, failed; attempts; last_error) with a unique pending row per record and field
- [x] `records.discogs_location_synced` and `_at`
- [x] Function `cell_code(row, col)` and trigger `record_locations_enqueue_discogs`
- [x] `gigs` (planning, packed, out, returned) and `gig_items` (packed_at, played, returned_at)
- [x] `plays` and view `records_last_played`
- [x] `units.qr_token` (8 characters, unique) and `sticker_prints`
- [x] `location_events.reason` extended with gig_pack, gig_return, cubby_move, swap
- [x] Trigram indexes on lower(artist) and lower(title); other indexes on owner, cell, playlist position, tracks, media links, events
- [x] Trigger `records_set_updated_at` and `discogs_sync_queue_set_updated_at` using `set_updated_at()`

### Known schema gaps (from `docs/DATA_MODEL.md`)

- [ ] Order inside a cubby
- [ ] Unique `(owner_id, discogs_instance_id)`
- [ ] Unique `tracks (record_id, position)`
- [ ] `media_links` duration and failure count
- [ ] Cell bound checks
- [ ] Auth link and row-level security
- [ ] `ON DELETE` rule for `playlist_items.track_id`
- [ ] Gig status names aligned with the prototype
- [ ] Preset table (the schema stores only `preset_key`; preset keys differ between prototype and seed)

## 25. Server and API (planned in `docs/ARCHITECTURE.md`)

- [ ] Vite, React, TypeScript, Tailwind app (the prototype is vanilla JS)
- [ ] Vercel Functions under `app/api`
- [ ] Auth (Neon Auth or similar) and per-owner scoping on every query
- [ ] `GET /api/presets`
- [ ] `GET, POST /api/units`; `PATCH, DELETE /api/units/:id`
- [ ] `POST /api/uploads` (private photo storage)
- [ ] `GET /api/units/:id/records`
- [ ] `POST /api/identify` (photo to candidates)
- [ ] `POST /api/records`; `GET, PATCH, DELETE /api/records/:id`; `POST /api/records/:id/resync`
- [ ] `GET /api/records?q=`
- [ ] `POST /api/records/:id/move`; `POST /api/moves/:eventId/undo`
- [ ] `POST /api/bag-scans`; `POST /api/bag-scans/:id/apply`
- [ ] Endpoints for gigs, plays, cubby labels, cubby move and swap
- [ ] `GET /api/records/:id/media`; `POST /api/media/resolve`; `POST /api/media/:id/report`
- [ ] Playlist endpoints, including `PUT /api/playlists/:id/order`
- [ ] `GET /api/cron/verify-links`
- [ ] Discogs endpoints: search, barcode, release, collection import, Location write-back worker
- [ ] Rate limiting on paid-model routes
- [ ] CI check that no secret name appears in the client code

## 26. Hosting, tooling and tests

- [x] `vercel.json`: build command `node scripts/build.mjs`, output `dist`, clean URLs, rewrite to `/index.html`, security headers
- [x] CSP allowing YouTube frames and scripts, jsDelivr and cdnjs scripts, Discogs and YouTube images, Google Fonts; camera allowed for the same origin
- [x] `scripts/build.mjs`: wraps `crates.html` in a full document and copies `logos/` to `dist/`
- [x] `research/build_presets.py`: regenerates the preset block in `crates.html` from `research/furniture.json` and `bags.json`
- [x] `tests/test_crates.py`: Playwright feature tests (15 numbered groups plus 8 extra cases) with screenshots
- [x] `.gitignore` for `dist/`, `.env*`, test output
- [ ] Vercel project created (the connector could not create one; use the dashboard)
- [ ] GitHub remote and CI
- [ ] Unit tests for addressing and the player state machine
- [ ] Vision evaluation set
- [ ] Preview deployments with a database branch per pull request
- [ ] Error tracking

## 27. Brand and docs

- [x] Logo: concept 3 "Half-pulled" (a record sliding out of a square sleeve plus rounded lowercase "crates")
- [x] Colors: lacquer `#1E1530`, dust sleeve `#EEEBF3`, cue red `#E5404A` (`#FF7077` in dark)
- [x] Files: `logos/concept-3.svg`, `logos/mark-3.svg`; five other concepts and `logos/logos.html` kept for reference
- [x] Favicon from the mark
- [x] Research: `research/furniture.md`, `bags.md`, `features.md` (and the JSON behind them)
- [x] Docs: PRD, data model, architecture, player spec, roadmap, infra
- [x] This list, FUTURE.md, HOWTO.md
