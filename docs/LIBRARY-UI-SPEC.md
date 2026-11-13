# Library UI spec: a pro, dense Collection view

Status: proposal, 2026-11-12. Scope: the Collection view (`renderTable()` and the `.ctable` CSS in `crates.html`), the sidebar that replaces the spot chips above it, the phone list, a "flip" stack, and loan tracking. Nothing here is implemented yet.

Brief from the owner: resemble Serato or rekordbox, pro, dense, lean, not gaudy; today's look is "a little gaudy and the sizes aren't correct".

Evidence labels: **[verified]** = read on an official manual or support page (URL in section 9). **[unverified]** = from memory, forum posts or inference; check against the real app before you copy it. Where a number is mine, it says **[proposal]**.

## 1. What the pro apps do

### 1.1 Serato DJ Pro

| Area | Finding | Label |
|---|---|---|
| Sidebar | Crates panel on the left of the library. Crates nest: drag a crate onto another to make a subcrate, drag to the far left edge to return to top level. Subcrates collapse and expand. A track can sit in many crates. Double-click renames. | verified |
| Smart crates | Rules (Add Rule), a Match All / Any dropdown, and a Live Update checkbox. With Live Update off, the crate refreshes only when you press its refresh button. | verified |
| Other sidebar entries | Files, Browse, Playlists, History sessions, "All..." entries exist in the real app. The pages I could open did not list them. | unverified |
| Columns | 23 optional columns (Artist, Album, BPM, Key, Color, Rating, Plays, Length, Location, Added and more). Right-click the header to choose. Drag an edge to resize. Which columns are on by default is not documented. | verified |
| Sorting | Click header to sort, click again to flip. Cmd/Ctrl-click a second header for a secondary sort, Ctrl+Shift-click removes it. A status column groups missing files. | verified |
| Text and art size | Ctrl/Cmd plus and minus change library text size. Settings have a Font Size slider and an Album Art Size slider (continuous, no named presets, no px values published). | verified |
| Row height in px | Not published. Visual estimate from screenshots: 20 to 24 px at default font, rows tighten and grow with the font slider. | unverified |
| Zebra, selection color | Not published. Estimate: faint alternating rows are available, selection is a flat blue-grey bar that dims when the list loses focus. | unverified |
| Search | Filters as you type. Ctrl/Cmd+F jumps to the box and exits the current crate back to the main library. Clicking a crate afterwards clears the query. | verified |
| Keyboard | Arrow keys move through the library. | verified |
| Drag | Drag tracks into crates to add; drag within a crate to reorder; drag folders from Finder to import. | verified |
| Color coding | A Color column exists; row colors come from track color tags. | verified (column), unverified (palette) |

### 1.2 rekordbox 6 and 7

| Area | Finding | Label |
|---|---|---|
| Tree view | Collection, Playlists (folders, playlists, Intelligent Playlists via right-click), Related Tracks, Hot Cue Bank Lists, Histories, Recordings, Devices, Explorer, iTunes, rekordbox xml. Up to 8 shortcuts to folders or playlists. A Playlist Palette holds up to 4 playlists as drop targets. | verified |
| Browser layout | Track list, category filter, track filter (color, rating, key and others), search filter, My Tag area, Sub Browser. | verified |
| Columns | Right-click the header to pick columns. Drag a header to reorder. Default set not published. | verified |
| View preferences | Preferences > View has Font Size, Line Space ("sets line space of track lists"), Artwork size for list and Tag List, and "Show the selected track to the center". | verified (names), unverified (values) |
| Row height in px | Not published. Estimate: 24 px with no art, roughly 40 to 48 px when artwork is on. | unverified |
| Search | Search filter lets you pick a column, then type. "Alphabet search" jumps to and selects tracks whose names start with the typed letters. | verified |
| Info panel | INFO panel shows color, rating, comments for the selected track. | verified |
| Drag | Drag a track onto a playlist in the tree, or onto a Playlist Palette slot, to add it. Delete removes from the playlist or Collection. | verified |
| Color coding | Eight track colors, filterable. | color filter verified; the eight hues unverified |

### 1.3 Traktor and Engine DJ

| App | Worth borrowing | Label |
|---|---|---|
| Traktor Pro | Favorites bar above the tree with pinned folders and playlists. Inline edit: click a field, Enter to commit, Esc to cancel. The preview player does not change play count. | verified |
| Traktor Pro | Key column highlights harmonically matching rows. | verified |
| Engine DJ | Sidebar: Playlists and Smartlists, Stems, History (split by drive), third-party libraries (read-only). No crates. | verified |
| Engine DJ | Column menu on header right-click, drag to reorder, Shift-click for multi-sort. Preview column for audition. | verified |
| Engine DJ | Search: space-separated words are ANDed. Magnifier icon scopes the search to one field (Title, Artist, BPM). Ctrl/Cmd+F focuses search. | verified |
| Engine DJ | Five filter boxes (Genre, Artist, Album, BPM, Key) with BPM tolerance and key compatibility. | verified |

### 1.4 The pattern to copy

1. A tree on the left (about 230 px), a dense table in the middle, an optional info panel on the right, a thin status bar under it.
2. The table is read-only text. Editing happens in an info panel or a dialog (Traktor allows inline edit on click; see 3.6).
3. Header is quiet: small, muted, sentence case, with column separators only in the header.
4. Selection is one flat neutral fill. Color is reserved for data (track color dot, key match) and for one now-playing marker.
5. Font size and row height are user settings, not breakpoints.

### 1.5 Why today's table reads as gaudy (from the code)

| Today (`crates.html`) | Problem | Fix in this spec |
|---|---|---|
| `min-width:1480px`, 16 columns, every cell an `<input>` or `<select>` | Looks like a form, not a library; forces horizontal scroll | Read-only cells, column set per width (3.3) |
| Bag and Home are `<select>` in every row | Heavy chrome, 160 to 210 px each | Plain mono text; "Move…" opens a picker |
| Header `uppercase`, `letter-spacing:.06em`, 11.5 px | Shouty | Sentence case, 11.5 px, 600, no tracking |
| Rows have `border-radius:10px`, zebra at 55% surface, pill hover | Soft and playful, not tool-like | Square rows, hairline between rows, no zebra |
| Selected row = 12% coral tint | Coral glow on purple | Neutral grey fill plus a 2 px coral marker |
| Body 13.5 px, thumb 32 px, row about 38 to 44 px | Neither compact nor touch-sized: "sizes aren't correct" | Three density steps (3.2) |
| Purple-navy `#150F22` base with coral `#FF7077` on top | Two saturated hues compete | Neutral graphite base, coral used in 3 places (4.1) |
| Display face (Big Shoulders) in views | Poster feel | Display face only on furniture unit names |

## 2. Anatomy for Crates

```
+--------------------------------------------------------------------------------+
| top bar 44: logo   [ search in: All records x ]                    view  density |
+-------------+----------------------------------------------------+-------------+
| sidebar 232 | header row 28 (sticky)                             | info 280    |
|             |----------------------------------------------------| (toggle I,  |
| Library     | row 32                                             |  off < 1280)|
| Spots       | row 32                                             |             |
| Smart       | ...                                                |             |
| Playlists   |                                                    |             |
| Gigs        |                                                    |             |
+-------------+----------------------------------------------------+-------------+
| status bar 24: 1,284 records  |  12 selected  |  3 lent out  |  sorted by artist |
+--------------------------------------------------------------------------------+
| player (existing, 76 px)                                                       |
+--------------------------------------------------------------------------------+
```

### 2.1 Sidebar tree (exact)

Row 28 px (compact 24), indent 14 px per level, chevron 12 px, counts right-aligned in mono 11.5 px. Width 232 px, resizable 180 to 320, persisted. Section labels 11 px, 600, `--ink-3`, sentence case, 12 px above and 4 px below.

```
Library
  All records                      1,284
  Recently added                      38   (last 30 days)
  Play history                            (sessions by date)
Spots
  v K1  Kallax 2x4                   212
      A1  Acid                        18
      A2  ...                         ..
      B4  ...
  > K2  Kallax 2x2                    64
  v Bags                              47
      Crater                          31
      Day bag                         16
  > Milk crates                       58
Smart
  Unplaced                            12
  Away from home                       9
  Lent out                             2   (badge turns amber when a reminder is due)
  Borrowed                             1
  Not played in a year               301
Playlists
  > Folders and playlists
Gigs
  Loft, Fri 21 Nov                    24
```

Rules:
- Selecting a unit shows all its cubbies' records with a cubby column; selecting a cubby filters to it. "All" for a unit is the unit row itself (matches the project brief's "(All) option").
- Smart rows show their definition on hover (tooltip) and have no edit affordance in v1. Live count, always on (Serato's Live Update off is not worth the complexity here).
- Pin up to 8 nodes to a "Favorites" strip above the tree (rekordbox shortcuts, Traktor favorites). Phase 2.
- Right-click or long-press a node: Rename, Print labels, QR stickers, Open on map.
- Drop targets: any unit, cubby, bag, crate, playlist, gig. Hover over a collapsed unit for 600 ms to expand it.
- Keyboard: Up/Down move, Right expands or enters, Left collapses or goes to parent, Enter selects and moves focus to the table.

### 2.2 Table behaviour

- **Sort:** click toggles ascending then descending. Cmd/Ctrl-click or Shift-click adds a secondary sort (both conventions verified). Indicator is an 8 px chevron after the label, `--ink`; secondary sort shows a smaller `--ink-3` chevron. Default sort: artist, then title.
- **Resize:** 6 px hit area on the header cell's right edge; double-click auto-fits (cap 360 px); min widths in 3.3. Persist per user.
- **Reorder:** drag a header; a 2 px `--accent` insertion line shows the drop point. Sticky first two columns (art, title) are not reorderable.
- **Column menu:** right-click header or the 24 px "columns" button at the end of the header. Checkboxes, plus "Reset columns".
- **Selection:** click selects one, Cmd/Ctrl-click toggles, Shift-click ranges, Shift+arrows extend. No checkbox column on desktop (checkboxes return in phone multi-select mode only).
- **Edit:** double-click a cell or press Enter/F2 opens an inline editor in that cell (Traktor pattern: Enter commits, Esc cancels). Only text-like fields: title, artist, label, cat no, year, style, BPM, key, notes, condition. Spot and home use the Move picker, never inline selects. Edited-by-me marker: a 4 px dot at the cell's top-right in `--ink-3` (replaces the red cell edge).
- **Zebra:** none by default. Optional "Row stripes" toggle in Settings at `#FFFFFF` 2.5% alpha.
- **Now playing:** the playing row gets a 2 px `--accent` bar on its left edge and title in `--ink` 600; play icon replaces the row's art overlay.
- **Row drag:** pointer down then 4 px move starts a drag from anywhere on the row (no grip column). Drag image is a 28 px-tall chip "3 records". Valid targets get a 1 px `--accent` outline and `#FFFFFF` 6% fill. Drop calls `place(r, to)` with an undo snapshot first, toast "Moved to K1·B3" (CLAUDE.md convention). Edge autoscroll within 32 px of the table top or bottom.
- **Away from home:** spot cell shows `K1·B2` and, in `--ink-3`, `from A1` is not shown inline; the home column carries it. If Home is hidden, show a 6 px `--warn` dot before the spot text.

### 2.3 Search

- One box in the top bar, 28 px high, width 320 px (flex up to 480). Placeholder: "Search this list". Shortcut `/` or Cmd/Ctrl+F focuses it; Esc clears, then blurs.
- **Scoped by default:** a removable chip inside the box shows the scope ("K1·A2", "Lent out"). Backspace on an empty box removes the chip (searches All records). This differs from Serato, where Ctrl+F exits the crate [verified]; for a physical-location app, "find it in this cubby" is the common case, and "where is it?" is one backspace away.
- Words are ANDed (Engine DJ [verified]). Prefix filters: `artist:`, `label:`, `cat:`, `spot:`, `bpm:120-128`, `key:8A`, `year:1996..1999`, `lent:`. Autocomplete shows them after typing a prefix character.
- Empty result: "No records in K1·A2 match. Search all records" (a link).
- Column filter boxes (Engine's Genre/Artist/BPM boxes) are phase 2, as a 40 px collapsible strip under the toolbar.
- Debounce 120 ms; keep focus and caret across re-render (existing `#t-q` handler already does this).

### 2.4 Info panel (right, 280 px, toggle `I`, closed under 1280 px)

Top to bottom: sleeve 248 x 248 px, title 15/600, artist 13, then label rows (12 px, label `--ink-3` 88 px wide, value `--ink`): Spot (mono, big 15 px), Home, Label / cat no, Year, Style, BPM / key, Condition (media / sleeve), Rating, Tags, Plays and last played, Lent to, Notes. Actions row: Play, Move…, Lend…. Edits made here are the primary edit path (rekordbox / Serato pattern).

### 2.5 Status bar (24 px)

Left: `1,284 records` (or `37 of 1,284` when filtered), `12 selected`. Middle: `3 lent out` (amber when a reminder is due), `9 away from home`. Right: `Sorted by Artist, Title`, density, Discogs sync state (simulated label stays, per CLAUDE.md). 11.5 px, `--ink-3`, hairline above.

### 2.6 Keyboard

| Key | Action |
|---|---|
| Up / Down | Move selection one row; selected row scrolls into view, kept centered if "keep selected centered" is on (rekordbox option [verified]); default off |
| Home / End, PageUp / PageDown | First / last row; page by visible rows minus 1 |
| Shift+Up / Down | Extend selection |
| Cmd/Ctrl+A | Select all in this list |
| Letters (table focused) | Alphabet jump: select first row whose sort-key starts with the typed letters; buffer clears after 800 ms (rekordbox alphabet search [verified]) |
| `/` or Cmd/Ctrl+F | Focus search |
| Space | Preview/play the selected record through the existing player (rekordbox/Serato preview key: unverified; here Space is play/pause) |
| Enter | Play selected, or commit an inline edit while editing |
| F2 | Edit the focused cell |
| M | Move… picker for the selection |
| L | Lend… dialog |
| I | Toggle info panel |
| `[` and `]` | Collapse / expand sidebar |
| Cmd/Ctrl+Z | Undo (existing `lastUndo`) |

Focus ring: 1 px `--accent` inset on the row plus 1 px `--bg` gap. Table is one tab stop (roving tabindex), `role="grid"`.

## 3. Table spec

### 3.1 Default columns for vinyl

Order left to right:

| # | Column | Source | Align | Notes |
|---|---|---|---|---|
| 1 | Art | cover or label photo | center | square, radius 2 px, sticky |
| 2 | Title | `title` | left | 13/500 `--ink`, sticky |
| 3 | Artist | `artist` | left | `--ink-2` |
| 4 | Label | `label` | left | `--ink-2` |
| 5 | Cat no | `catno` | left | mono 12 |
| 6 | Year | `year` | right | tabular |
| 7 | Style | genre / style | left | first value, rest in tooltip |
| 8 | BPM | `bpm` | right | tabular, mono |
| 9 | Key | `key` | left | mono, Camelot or open-key per Settings |
| 10 | Spot | current location | left | mono, `K1·B2`, or bag name |
| 11 | Home | `home` | left | mono, `--ink-3` |
| 12 | Last played | last play | left | `12 Mar 26`; `--warn` when over a year, "Never" in `--ink-3` |
| 13 | Plays | count | right | tabular |
| 14 | Condition | media / sleeve | left | `NM / VG+`, 11.5 mono |
| 15 | Lent to | loan | left | name; auto-shown in Lent out and Borrowed lists |
| 16 | Color | one of 8 dots | center | optional, off by default |

Rating and Tags from today's table move to the info panel and the column menu (off by default).

### 3.2 Density and sizes

One variable set on `html[data-density]`. Rows never wrap (`white-space:nowrap; text-overflow:ellipsis`).

| Token | Compact | Regular (default, pointer: fine) | Comfortable (touch) |
|---|---|---|---|
| Row height | 24 px | 32 px | 44 px |
| Art | none (column hidden) | 28 px | 36 px |
| Cell padding x | 8 px | 10 px | 12 px |
| Body font | 12 px / 16 | 13 px / 18 | 14 px / 20 |
| Mono font | 11.5 px | 12 px | 13 px |
| Header height | 24 px | 28 px | 32 px |
| Header font | 11 px / 600 | 11.5 px / 600 | 12 px / 600 |
| Sidebar row | 24 px | 28 px | 36 px |

Why: 24 px is the WCAG 2.2 AA minimum target size [from memory, unverified here]; 44 px matches Apple's minimum touch target [from memory, unverified here; the HIG page was not reachable]. 32 px with a 28 px thumbnail is close to what rekordbox and Serato show with artwork on, per my estimate of their screenshots [unverified]. Auto choice: `pointer: coarse` defaults to Comfortable on tablets; phones use the list in section 5, not the table.

### 3.3 Columns by width

Sidebar 232 px, info panel closed unless noted. Widths are start widths; Title and Artist flex to absorb leftover, then everything else keeps its width.

| Column (width px, min) | 1440 | 1024 | 390 |
|---|---|---|---|
| Art (28, fixed) | yes | yes | list thumb 44 (section 5) |
| Title (216, 120) | yes | yes | list line 1 |
| Artist (156, 100) | yes | yes | list line 2 |
| Label (108, 72) | yes | yes | line 2 after artist |
| Cat no (84, 64) | yes | yes | no |
| Year (44, 40) | yes | yes | no |
| Style (108, 72) | yes | no | no |
| BPM (44, 40) | yes | yes | right, line 2 |
| Key (40, 36) | yes | no | right, line 2 |
| Spot (72, 56) | yes | yes | right, line 1 |
| Home (72, 56) | yes | yes | only when away |
| Last played (84, 72) | yes | no | no |
| Plays (40, 32) | yes | no | no |
| Condition (44, 40) | yes | no | no |
| Lent to (96, 72) | in Lent lists | in Lent lists | status text |

Budget check at 1440: viewport 1440 minus sidebar 232 minus 8 px scrollbar = 1200. Sum with defaults 28+216+156+108+84+44+108+44+40+72+72+84+40+44 = 1140. Fits with 60 px of flex. With the info panel open (280 px), the app drops, in order: Condition, Plays, Last played, Style, Label until it fits, and the user's manual choices are kept in a per-width profile. At 1024 the sidebar narrows to 200 px, so 824 px remain; the nine columns total 28+200+148+100+84+44+44+72+72 = 792. Between 700 and 1023 px the sidebar becomes an overlay (button in the top bar) and the 1024 set is used. Under 700 px, section 5. There is no horizontal scroll at any supported width (test 14 keeps passing); a user who adds columns beyond the budget gets horizontal scroll inside the table only, with the first two columns sticky.

### 3.4 Type scale

| Role | Size / line | Weight | Face |
|---|---|---|---|
| Table title | 13 / 18 | 500 | Instrument Sans |
| Table body | 13 / 18 | 400 | Instrument Sans |
| Table mono (spot, cat no, key, BPM) | 12 / 18 | 400 | DM Mono, `tabular-nums` |
| Header | 11.5 / 16 | 600 | Instrument Sans, `--ink-3`, no uppercase |
| Sidebar item | 13 / 18 | 400 (selected 500) | Instrument Sans |
| Sidebar section | 11 / 16 | 600 | Instrument Sans, `--ink-3` |
| Counts, status bar | 11.5 / 16 | 400 | DM Mono |
| Info panel title | 15 / 20 | 600 | Instrument Sans |
| Info panel spot | 15 / 20 | 500 | DM Mono |
| Toolbar, chips | 12.5 / 16 | 500 | Instrument Sans |

Weights 400, 500, 600 only. Use `rem` so the browser font-size setting still applies (INTERACTION-SPEC section 5).

### 3.5 Grid and art modes

View switch (segmented, 3 icons, 28 px high) at the right of the toolbar: **List**, **Art**, **Flip**. CLZ offers list, cover wall and (tablet only) cover flow [verified]; Discogs iOS offers list, small grid and large grid [verified]; Serato has an Album Art Size slider [verified].

- **Art grid:** square cells, art-size slider 80 to 240 px (step 8, default 144), gap 12 px, caption below: title 12/500 one line, artist 11.5 `--ink-2` one line, spot mono 11.5 `--ink-3`. Ctrl-wheel changes size. Selection = 2 px `--accent` outline offset 2 px. Same keyboard model (arrow keys move by cell).
- **Flip:** section 6.

### 3.6 Inline edit versus info panel

Open question for the owner: Traktor allows inline edit on click [verified], Serato and rekordbox lean on a separate panel. I recommend double-click/F2 inline for single cells and the info panel for anything multi-field. The spreadsheet feel the app has today ("click any cell to edit") is kept, but behind a deliberate gesture so rows read as a list.

## 4. Color system

### 4.1 Tokens (dark, default "Studio")

Neutral graphite with a faint cool cast. Saturation only in data and the one accent.

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#0E0F12` | app chrome, behind panels |
| `--side` | `#121317` | sidebar |
| `--panel` | `#15161A` | table body, info panel |
| `--head` | `#1A1B20` | table header, status bar, top bar |
| `--line` | `#23252B` | 1 px hairlines: panel edges, header, status bar |
| `--line-row` | `#1C1E23` | 1 px between rows |
| `--line-2` | `#2F323A` | column separators in header, input borders |
| `--hover` | `#1A1C21` | row and sidebar hover |
| `--sel` | `#252932` | selected row, focused table |
| `--sel-idle` | `#1E2127` | selected row when table is not focused |
| `--ink` | `#E6E7EA` | primary text (14.6:1 on `--panel`) |
| `--ink-2` | `#A4A7B0` | secondary text (7.5:1) |
| `--ink-3` | `#80848F` | tertiary, headers, counts (about 4.9:1 on `--panel`; verify in the test pass) |
| `--accent` | `#FF7077` | see rules below (6.8:1 on `--panel`) |
| `--accent-ink` | `#17080A` | text on filled accent (7.3:1) |
| `--ok` | `#4FBF85` | synced, returned |
| `--warn` | `#E0A93B` | away from home, reminder due, not played in a year |
| `--bad` | `#F0766B` | destructive confirm text only |

Contrast numbers for `--ink`, `--ink-2`, `--accent`, `--ok`, `--warn`, `--bad` and `--accent-ink` were computed with the WCAG formula on `--panel` (`#15161A`); `--ink-3` is the one to re-measure.

**Accent rules (coral `#FF7077`, used sparingly, no glows, no tints):**
1. The now-playing marker (2 px bar on the row, play glyph).
2. The focus ring and the 2 px selected-node bar in the sidebar.
3. One primary button per view (for example "Put 9 back home"), filled `--accent` with `--accent-ink` text. Everything else is a ghost button with a 1 px `--line-2` border.

Not accent any more: selected-row tint, zebra, edited-cell edges, chips that are "on" (use `--sel` fill and `--ink` text), progress bars (use `--ink-2`), links (use `--ink` underline on hover).

**Status color collision:** coral is close to a red, so red cannot also mean "overdue". Statuses use amber (`--warn`) plus a glyph (clock, arrow), never color alone. `--bad` is limited to destructive confirmations.

**Mapping from today's "Booth" look (`:root[data-look="booth"]`):**

| Token | Old | New |
|---|---|---|
| `--bg` | `#150F22` | `#0E0F12` |
| `--surface` | `#1E1530` | `#15161A` |
| `--surface-2` | `#281D3E` | `#1A1B20` |
| `--line` | `#3A2E54` | `#23252B` |
| `--ink` | `#EEEBF3` | `#E6E7EA` |
| `--muted` | `#AFA7C2` | `#A4A7B0` |
| `--accent` / `--brand` | `#FF7077` | `#FF7077` (unchanged, used less) |

Keep the purple look as an opt-in Look called "Booth" for the Map and Columns views if the owner likes it; the Collection view uses Studio tokens either way. The existing "Shop floor" light look keeps its accent `#D2412C`.

### 4.2 Light theme (short)

`--bg #ECEEF1`, `--side #F4F5F7`, `--panel #FFFFFF`, `--head #F4F5F7`, `--line #DFE2E7`, `--line-row #EEF0F3`, `--sel #E3E7EE`, `--ink #15161A`, `--ink-2 #4B505A`, `--ink-3 #6B707B`, `--accent #D2412C`, `--warn #9A6200`, `--ok #17894B`.

### 4.3 Shape and motion

- Radius: 0 on rows and panels, 4 px on buttons, inputs and art, 6 px on popovers and sheets, 999 px only on the 8 px color dot.
- Shadows: none, except popovers and menus `0 8px 24px rgba(0,0,0,.45)` with a 1 px `--line-2` border.
- Hairlines are 1 px; use `box-shadow: inset 0 -1px 0` on rows so heights stay exact.
- Transitions: background 80 ms linear on hover/selection; nothing else animates in the table. `prefers-reduced-motion` already honored app-wide.

### 4.4 Track color tags (data, not chrome)

Eight dots, 8 px, muted so they do not fight the accent: red `#D9695F`, orange `#D98E4A`, yellow `#CDB04F`, green `#5DB37E`, aqua `#4FB3B3`, blue `#5B8FD9`, violet `#8E7BD9`, pink `#C77BAF`. Shown in the Color column and the sidebar (a user can color a bag or crate). Both Serato and rekordbox offer color coding [verified that it exists]; the exact hues are mine.

## 5. Phone (390 px)

### 5.1 What the phone apps do

| App | Finding | Label |
|---|---|---|
| CLZ Music | List view with a small thumbnail plus several fields; Cover Wall; Cover Flow on tablets only; one "switch views" button at the top right next to the A-Z sort button. | verified |
| Discogs iOS | Collection offers list, small grid, large grid; sort by Artist, Title, Year, Date Added, Label, Format, Cat #, Rating or a custom field; folders chosen from the top-left. Swipe actions not documented. | verified |
| rekordbox mobile, Serato / djay mobile | A library screen with playlists and a search field above a track list; I could not open an official layout description. | unverified |

Takeaway: phone apps drop columns, not features. Two lines per row, a thumbnail, one view switch, sort as a menu.

### 5.2 Layout

```
+-------------------------------+
| 44  [ All records v ]   [view]|  top bar: crate picker button, view switch
+-------------------------------+
| 40  ( search in All records ) |  sticky, scoped chip inside
+-------------------------------+
| 32  Away 9  Lent 2  Unplaced  |  optional chip row, horizontal scroll
+-------------------------------+
| 60 [art] Title            K1·B2|
|     Artist · Label    124 8A  |
| 60 ...                        |
+-------------------------------+
| player mini bar (existing)    |
+-------------------------------+
```

Row: height 60 px (comfortable), padding 8 px 16 px, art 44 px radius 4 px, gap 12 px. Line 1: title 15/500, right-aligned spot in mono 12 `--ink-2`. Line 2: artist then label separated by " · ", 13 `--ink-2`; right: `124  8A` mono 12 `--ink-3` (BPM, key) or a status in `--warn` ("Lent to Sam", "Away, home A1"). Hairline `--line-row` inset 72 px from the left. Safe-area padding at the bottom for the player. No horizontal scroll (test 14).

- **Crate picker:** tapping the top-bar title opens a bottom sheet (INTERACTION-SPEC sheet model, snap at 50% and 92% of height) with the section 2.1 tree, 44 px rows, a filter field, and recent nodes at the top. Selecting closes the sheet.
- **Sticky search:** 40 px field, pinned under the top bar while scrolling (`position: sticky; top: 44px`). Scope chip inside; tapping the chip's x searches everything. Keyboard "Search" key dismisses the keyboard and keeps the results.
- **Index rail:** when sorted by artist or title, a 16 px A-Z rail on the right edge (touch-drag scrubs, with a 56 px letter bubble). Hidden when sorted by anything else.
- **Swipe actions (row):** swipe left reveals two 72 px buttons, "Move" (neutral `--sel`) and "Lend" (`--warn` text on `--sel`); full swipe past 55% of width or velocity above 0.5 px/ms commits Move and opens the picker. Swipe right reveals one 72 px "Play next" button. Tick `navigator.vibrate?.(8)` at the reveal threshold. Animation 220 ms `cubic-bezier(.2,.8,.2,1)`, interruptible. No red delete swipe; delete lives in the row's context sheet (avoids the coral/red clash and accidental loss).
- **Long-press 350 ms:** enters multi-select (checkbox circles appear on the left, 24 px), bottom action bar: Move, Lend, Add to playlist, Put back home.
- **Tap:** opens the detail overlay (existing). **Pull to refresh:** not used (data is local).
- **Type:** 15 px for titles keeps the text readable without zoom; inputs 16 px to stop iOS zoom on focus.

## 6. Flip: a record-store stack

### 6.1 How apps represent flipping

| Pattern | Where | Note |
|---|---|---|
| Cover Flow: centered cover, side covers rotated about 45 deg on a shelf | Apple iTunes and Finder (historic); CLZ cover flow on tablets [verified] | CSS demo values [verified]: rotateY -45 / 0 / +45 deg, perspective 40em, center scale 1.5 with translateZ 1em, scroll-snap x mandatory, a 0.5em reflection. Apple discontinued it in recent macOS (from memory, unverified). |
| Cover wall / grid | CLZ, Discogs | Fast to scan, no sense of order |
| Stacked cards with peeking edges | iOS Photos / Wallet-style stacks | Good on phone, poor for large sets |
| Bin flipping: front sleeve tips toward you to reveal the next | Real record stores | Strongest metaphor, hardest to make fast |

Recommendation: **one component, "Flip"**, a Cover Flow derivative sized for records. It maps to the physical act (thumb through, sleeve by sleeve, dividers by letter), it is pure CSS transforms (cheap), and it reuses the sort order of the current list, so a cubby shows its records in shelf order if sorted by position. Sources for images stay as today (own photos, YouTube thumbs); do not mirror Discogs images (CLAUDE.md).

### 6.2 Numbers

| Parameter | Desktop | Phone (390) |
|---|---|---|
| Stage | 100% x 360 px | 100% x 300 px |
| Center card | 240 x 240 px, scale 1 | 232 x 232 px |
| Side cards | scale .8, rotateY ∓58 deg | scale .82, rotateY ∓48 deg |
| Cards visible each side | 3 | 2 |
| Center-to-neighbor offset | 150 px, then +52 px per further card (150, 202, 254) | 150 px, then +32 px (150, 182) |
| Overlap | side cards overlap each other by about 60% of their projected width; all overlap the center card by 20 px | center card leaves 79 px of each neighbor visible |
| Depth | translateZ(-60 px) per step | translateZ(-40 px) per step |
| Perspective | 900 px, origin 50% 40% | 700 px, origin 50% 40% |
| Opacity | 1, .85, .6, .4 | 1, .8, .5 |
| Reflection, glow, drop shadow | none; 1 px `rgba(0,0,0,.5)` edge shadow on side cards | same |
| Caption | under center card: title 16/600, artist 13 `--ink-2`, spot mono 13 | same, title 15 |
| DOM | render center +/- 7 cards only, recycle nodes | center +/- 5 |

### 6.3 Desktop interaction

- **Keys:** Left/Right (and Up/Down) step one; Shift+arrow or PageUp/PageDown step 10; Home/End jump; a typed letter jumps to the first artist starting with it (record-bin dividers); Space plays; Enter opens detail; M moves; Esc returns to list at the same record.
- **Wheel and trackpad:** accumulate `deltaX + deltaY`, one step per 48 px of travel, max one step per 45 ms. Native trackpad momentum is respected by feeding the same accumulator (no extra easing). `preventDefault` only inside the stage, with `overscroll-behavior: contain`.
- **Animation:** single step 240 ms `cubic-bezier(.2,.8,.2,1)`. Held key (`event.repeat`) or fast wheel: switch to 90 ms linear and coalesce to the latest target in `requestAnimationFrame`, so it never queues more than one pending move. Click on a side card moves to it (240 ms). Respect `prefers-reduced-motion`: cross-fade 120 ms, no rotation.
- **Scrubber:** a 4 px high strip under the stage showing position in the list; drag it for a long jump; labelled with the current letter.

### 6.4 Phone interaction

- Horizontal pointer drag on the stage (`touch-action: pan-y`). Track velocity over the last 80 ms. One card of travel = 64 px of finger movement.
- On release, project like a scroll view: distance = v * 0.998 / (1 - 0.998) with v in px/ms (iOS "normal" deceleration rate, from memory, unverified), then cards = round(distance / 64), capped at 30 per flick. Snap with duration clamp(220 + 18 * cards, 260, 700) ms using `cubic-bezier(.2,.8,.2,1)`; interruptible by touching again.
- Tap center card: detail overlay. Tap a side card: move to it. Long-press the center card: Move picker. Double-tap: play.
- Haptic tick `navigator.vibrate?.(4)` per card crossed, at most one per 60 ms (Android Chrome only).
- A 24 px letter bubble follows the current artist initial while dragging fast (above 1.5 px/ms).

## 7. Lending

### 7.1 What others do

| App | Fields and behavior | Label |
|---|---|---|
| CLZ Books / Comics (Loan Manager) | Loaner, loan date, due date, return date, notes editable on each loan; lend from a record's "Loan" button or batch via the action bar (person and due date); return from the Loan Manager or by scanning the barcode; print a single person's current loans. Overdue display and reminders not documented. | verified |
| Libib | Has checkout / lending; support pages for fields and reminders could not be opened. | unverified |
| LibraryThing | Lending ("circulation") feature announced; details not read. | unverified |
| BookBuddy, Lendee, Splitwise-style reminders | Not verified at all. Splitwise sends reminder emails and lets you nudge; the cadence is not something I could confirm. | unverified |

The documented core is small: who, since when, due when, returned when, notes, plus a place that lists everything currently out. Reminders are where the documented apps are thin, so Crates can do better with a simple fixed cadence.

### 7.2 Fields (add to `records[].loan`, one open loan per record, history kept)

| Field | Type | Rule |
|---|---|---|
| `dir` | `lent` or `borrowed` | default `lent` |
| `who` | text | required; autocomplete from past people |
| `phone` | text | optional; rendered as a tap-to-message link |
| `since` | date | default today |
| `due` | date or null | optional; quick picks: None, 2 weeks, 1 month, Custom |
| `note` | text | optional ("bring it to the gig") |
| `returned` | date or null | set by "Mark returned"; moves the loan to history |
| `nextRemind` | date | computed; see below |
| `snoozeUntil` | date or null | set by Snooze |

Spot behaviour: lending does not call `place()` to a physical spot. The record keeps its home; the Spot cell reads "Lent to Sam" in `--warn`, and "Away from home" counts it. Returning offers "Put back in K1·A2" as the default action (one tap, undo available). This follows the `place()` convention in CLAUDE.md.

### 7.3 Reminder and overdue rules

- **Reminder schedule (owner's spec):** first reminder at `since` + 14 days, then every 7 days until returned. So days 14, 21, 28, and so on.
- If `due` is set and falls before day 14, add one reminder on `due` and keep the weekly cadence from day 14.
- **State labels:** *Out* (neutral `--ink-2`, "Out 6 days"), *Reminder due* (from the reminder date onward, until snoozed or returned: `--warn` clock glyph, "Out 3 weeks"), *Overdue* (only when `due` is set and passed: "Overdue 4 days", `--warn`).
- **Snooze:** 1 day, 3 days, 1 week. A snooze moves only the next reminder; the weekly rhythm resumes from the snooze date. Snooze never changes `due`.
- **Stop conditions:** returned, or loan deleted. No auto-escalation, no emails to the borrower.
- **Settings:** two steppers, "First reminder after [14] days" and "Then every [7] days", range 1 to 90 and 1 to 30. Defaults are the owner's numbers.

### 7.4 UI

- **Lend dialog (L, or swipe Lend):** single sheet. Fields in order: Who (autofocus), Phone, Since (today), Due (segmented: None / 2 weeks / 1 month / Pick), Note. One primary button "Lend 2 records", toast "Lent to Sam", undo. Multi-select lends all selected records to one person.
- **Sidebar:** `Lent out` row with count. When any reminder is due, the count gets a 6 px `--warn` dot. `Borrowed` is separate so the two directions never mix.
- **Lent out list:** columns Art, Title, Artist, Lent to, Since, Out for, Due, Phone, Spot of origin (home). Sorted by `Out for`, longest first. A banner above the table when reminders are due: "2 records are due a reminder" with buttons "Message Sam" and "Snooze all 3 days".
- **Row actions (info panel and context menu):** Message, Snooze, Edit loan, Mark returned (primary, accent). "Message" opens `sms:<phone>?body=<text>` (the `?body=` form works on Android; iOS wants `&body=`: unverified, test both) with the text "Hey, quick one: can I get <title> back when you get a chance?". If there is no phone it copies the text.
- **Out of the app:** "Add reminder to calendar" downloads an `.ics` with a weekly `RRULE` starting at `since` + 14 days, because a static page cannot push. A Web Push or email reminder is a backend phase (Neon + a cron function); until then reminders surface on open, in the sidebar badge and the status bar, and as a `Notification` only if the user grants permission while the tab is open.
- **Per-person view:** clicking a name in Lent to filters to that person; "Copy list" produces plain text for a message (CLZ prints a per-person list [verified]).
- **Empty state:** "Nothing lent out. Select records and press L."

## 8. Build plan and tests

Order: (1) tokens and density variables, read-only cells, header restyle, remove zebra/pill/tint (CSS only, lowest risk); (2) sidebar tree replacing the spot chips, with scoped search chip; (3) column menu, resize, reorder, persisted per width; (4) info panel and status bar; (5) keyboard model and alphabet jump; (6) phone list, picker sheet, swipe actions; (7) Flip; (8) loans and reminders.

Tests to add in `tests/test_crates.py` (run with `CRATES_NO_PATCH=1`):
- No horizontal page scroll at 390, 1024 and 1440 px (extends test 14); column sets match 3.3.
- Row height equals the density token (24 / 32 / 44 px) within 1 px.
- Both themes: `--ink` / `--panel` contrast at least 4.5:1, `--ink-3` / `--panel` at least 4.5:1.
- Keyboard: arrows, Home/End, alphabet jump, `/` focuses search, Esc clears.
- Drag a row onto a sidebar cubby: `place()` called, toast "Moved to K1·B3", undo restores.
- Flip: 7 DOM cards at most, 30 steps by held ArrowRight finish without queueing more than one transition.
- Loans: reminder dates at day 14, 21, 28 for a loan with no due date; snooze shifts only the next one; returning offers "Put back in ...".

## 9. Sources

Verified (opened and read):
- Serato, Navigating and managing your library: https://support.serato.com/hc/en-us/articles/14359483189135-Navigating-and-Managing-your-Library
- Serato, Sorting and browsing: https://support.serato.com/hc/en-us/articles/203015464-Sorting-and-browsing-your-library
- Serato DJ Tips, custom crate columns: https://wearecrossfader.co.uk/blog/custom-crate-columns-serato-dj-tips/
- Serato, Smart Crates: https://support.serato.com/hc/en-us/articles/360001447715-Library-Smart-Crates
- Rane SL1 manual (Serato), Font Size and Album Art Size: https://www.manualslib.com/manual/1631513/Rane-Sl1.html?page=33
- rekordbox 6.6.4 manual (tree view, columns, search, drag to playlist): https://cdn.rekordbox.com/files/20220627093437/rekordbox6.6.4_manual_EN.pdf (first 100,000 of about 276,000 characters read)
- rekordbox Preferences > View (Font Size, Line Space, Artwork): https://manualslib.com/manual/1135837/Pioneer-Rekordbox.html?page=215
- Engine DJ user guide 5.1.0: https://cdn.inmusicbrands.com/engine/51/Engine%20DJ%20-%20User%20Guide%20-%20v5.1.0.pdf
- Traktor Pro manual: https://docs.native-instruments.com/online-guides/traktor-pro-manual/en/managing-your-track-collection and https://docs.native-instruments.com/online-guides/traktor-pro-manual/en/basic-usage-tutorials
- djay Pro side panel (Library, Queue, Match, History, Info): https://help.algoriddim.com/user-manual/djay-pro-mac/music-library/advanced/side-panel
- CLZ Music iOS view modes: https://clz.com/music/mobile/manual/ios/2.0/en/topic/choosing-view-modes
- CLZ Books loan manager: https://app.clz.com/books/manual/1/en/topic/managing-loans
- Discogs iOS collection: https://support.discogs.com/hc/en-us/articles/360039334454-How-To-Use-The-Collection-Feature-On-iOS
- CSS cover flow demo values: https://scroll-driven-animations.style/demos/cover-flow/css/

Not verified (search results only, or page not reachable): exact row heights and default columns of Serato and rekordbox; Serato smart-crate field list and History/Files/Browse entries; rekordbox mobile and Serato/djay mobile library layouts; Libib, LibraryThing, BookBuddy, Lendee and Splitwise reminder behavior; Apple HIG 44 pt target (page blocked); WCAG 2.2 24 px target size; iOS 0.998 deceleration constant; Apple Cover Flow's discontinuation; `sms:` URL differences.
