# Crates: how to use it and how to work on it

Part A is for the person using Crates. Part B is for the person changing it. Last updated 2026-10-20.

---

# Part A: Using Crates

This guide describes the prototype as it exists today. Where something is a demo or a simulation, it says so.

## Before you start

- **It is a prototype.** It opens with a demo collection: three places (Kallax 1, a bag called Crater, a blue milk crate) and 10 records with placeholder cover art.
- **Your data stays in your browser.** Everything you add is saved in this browser on this device (local storage). It is not sent anywhere and is not shared between your phone and your laptop. Clearing site data, using a private window, or switching browsers loses it. There is no export yet.
- **Reset any time.** Settings, then "Reset demo collection", puts back the 10 demo records and removes what you added.
- **Two ways to open it.**
  - Inside the claude.ai preview: photo recognition works (Claude reads your photos), but YouTube cannot play inline, so the play button opens YouTube instead.
  - On Crates' own site: YouTube plays inline with the fallback chain, QR stickers can print directly, but photo recognition is not available yet. You type records in.
- **Works best on a phone**, held one-handed at the shelf. It also works on a laptop.

## Find your way around

- Top bar: the tabs **Room**, **Playlists** and **Gigs**; the **Add** button; the **Settings** gear.
- Search box under the bar.
- Once something is queued, a mini player sits at the bottom. Tap it to open the full player.
- Codes look like `K1·B2`: unit `K1`, cubby `B2`. The unit ID is always there so the code never looks like a side-B track.

## Set up your furniture

1. Tap **Add**, then **Furniture**.
2. Pick a group (IKEA Kallax, IKEA other, Record furniture, Wall and bins, Crates, Record boxes and cases), then a preset. Kallax comes in every size; a 2x4 gets cubbies `A1..A4` and `B1..B4`.
3. Pick a finish, or "Custom" for any color.
4. Give it a name ("Kallax 2") and check the ID (`K2`). Change it if you like; it must be unique and up to 6 letters or digits.
5. If the preset's grid is not what you have, change **Rows** and **Columns** (1 to 10).
6. Optionally tap **Photo** to take a picture of the real piece. It becomes the cover instead of the drawing.
7. Tap **Add shelf unit** (or **Add crate**).

Tips:
- Choose "Custom grid" for something not in the list.
- Preset capacities are the maker's rough figures. "Capacity not listed" means nobody published one.

## Set up your record bags

1. Tap **Add**, then **Record bag**.
2. Filter by brand or choose from All (UDG, Magma, Zomo, Glorious, Reloop, Odyssey, Gator and more).
3. Pick a color and a name ("Crater").
4. Optionally add a photo of the bag; it becomes the cover.
5. Tap **Add bag**.

Crates and boxes are in the Furniture list (milk crates, wooden crates, Glorious boxes and so on).

## Add records

1. Open the place you want, then tap **Add**, then **Record**. (Opening a cubby first makes it the default.)
2. **Pick where they live.** Tap a cubby on a shelf, or a bag or crate.
3. Add the records one of three ways.
   - **Photograph the shelf** (only when photo recognition is available). Fan or line up the sleeves so the covers or spines show. Review the list it finds. Tick what is right; anything it was unsure about starts unticked. Tap **Add to <slot>**.
   - **Type it in.** Fill artist and title, optionally label, year and catalog number. Tap **File into <slot>**.
   - **Scan a barcode.** See the next section.
4. Records filed into a bag or crate have no home slot yet. Move them to a shelf once to set one.

Nothing is saved from a photo until you tap the final button.

### Duplicates

While you type, Crates compares artist and title (ignoring case, accents and a leading "The") and any barcode with what you own. If it finds a match, a yellow notice says "You already own this. It's in Kallax 1, shelf A1 (Detroit & Chicago)". Tap **Show it** to go look. The button becomes **Add another copy**; use it if you really have two copies.

### Barcode

1. In **Add record**, find "Scan a barcode".
2. Type the digits under the bars, or use the photo button to take a picture of the barcode. Fill the frame with the bars and avoid glare.
3. Crates reads the photo with the browser's barcode reader, falls back to a second reader, and then to Claude when available.
4. You get a list of candidate pressings. In the prototype these are **example data**, clearly labeled; the real app will list actual Discogs matches.
5. Tap a candidate to fill the form, then file it.

## Name your cubbies

Open a unit, tap a cubby chip (for example `A2`), and type in "Name A2, e.g. House". Press Enter. The cubby now shows as `K1·A2 (House)` in search, lists and warnings. Clear the field to remove the name.

## Find a record

1. Type in the search box: artist, title, label, catalog number, year, style, BPM, key, tag, a word from your notes, a cubby name. Every word you type must match.
2. Results show where each record is: "Kallax 1, shelf A2 (Acid)" or `Bag "Crater"`.
3. Tap a result (or use the arrow keys and Enter). Crates opens that place, shows the record, and flashes the cubby.
4. Searching a unit's name or ID (`K1`, "Crater") also lists the unit.

## Flip through a place

1. In **Room**, tap a unit.
2. Tap **All** to see everything in it, or a cubby chip (`A1`, `B3`) to see one cubby. The number on each chip is its record count.
3. Swipe the sleeves left or right, tap the arrows, tap a neighbor sleeve, or press the left and right arrow keys on a keyboard.
4. Below the sleeves you see the record's details, where it is, where it came from if it is in a bag, and its home slot if it is away.
5. Tap **Select records** to tick several at once.
6. Tap **Not played in a year** to show only records you have not played for a year.

## Move one record

1. Flip to the record and tap **Move...**
2. Tap a destination. The top buttons are shortcuts: the record's home slot and your last three targets. Below them are all your shelves and bags; tap a cubby or a bag.
3. Done. A toast says where it went; tap **Undo** within 5 seconds to take it back.

Rules to know:
- Moving to a shelf sets that shelf as the record's home slot.
- Moving to a bag or crate keeps the home slot, so you can send it back.
- **Put in bag** puts the record in your bag in one tap (if you have one bag). **Back to K1·A2** sends it home in one tap.

## Move many records, a whole cubby, or swap two

- **Many records:** tap **Select records**, tick them (or **Select all**), then **Move N...** or **Put in bag**.
- **A whole cubby:** open the cubby, tap **Move whole cubby...**, tap the target. If the cubby has a subtitle you can bring it along.
- **Swap two cubbies:** tap **Swap with...** and choose the other cubby. Both trade records, and optionally subtitles. Home slots follow the records.
- All of these have **Undo**.

## Use a bag: scan and unpack

### Scan a bag to reconcile it

1. Open the bag and tap **Scan bag**.
2. Fan the records out so the sleeves show and take one photo (when photo recognition is available), or tap **Simulate a scan** to see how the step works.
3. Crates lists everything it thinks is in the bag. Tick anything it missed and untick anything that is not there. Records it saw that you do not own are listed separately.
4. Tap **Review changes**. You see **Into bag** (found, not yet in the bag) and **Not in bag** (in the bag but not found; they go to their home slot).
5. Tap **Update N locations**. Everything updates at once, with **Undo**.

### Unpack a bag

Open the bag and tap **Unpack to home slots**. Every record goes back to its home slot. A record with no home slot stays in the bag, and the toast tells you how many.

In a bag's list, each record shows "from K1·A2" so you know where it belongs.

## Edit a record's details

1. On the record, tap **Edit details**.
2. You can change artist, title, label, catalog number, year, style, BPM, key, media and sleeve condition (M, NM, VG+, VG, G+, G, F, P), star rating, tags, notes, and add your own fields ("Bought at" / "Halcyon").
3. A small dot marks any field you changed from the original. Open Edit details again and tap **Undo edit** beside a field to restore the original value.
4. Tap **Save details**.

Your edits win over Discogs, and the original Discogs values are kept so you can always go back.

## Playlists

1. Open the **Playlists** tab and tap **+ New playlist**. Name it and pick a color.
2. Add records: **+ Add records** (filter by artist, title or shelf), or tap **+ Playlist** on any record.
3. Reorder: drag the handle on the left of a row, or use the up and down buttons.
4. **Sort** by pull order (grouped by shelf, so you can pull them in one pass), artist, year, BPM, or reverse. Undo is offered.
5. **Play** or **Shuffle**.
6. **Pack into bag...** moves every record in the playlist into the bag you choose. Home slots stay, so unpacking returns them.
7. **Duplicate** copies it. **Delete playlist** asks first; the records stay in your collection.

## Play records

- Tap the round play button on a record, **Play** on a cubby or unit, **Play collection** in the room, or **Play** on a playlist, gig or dig list.
- The mini bar at the bottom shows the record. Tap it to open the player: a spinning vinyl with the cover as its label, the **Up next** list in large type, and two more tabs.
- **YouTube links** shows each link and why one failed.
- **Fallback chain** shows the steps Crates takes when a link is dead: try the saved link, give it 3 seconds to start, try the alternates, try a fresh search (not available in the prototype), then mark it not working and skip. In link mode (the claude.ai preview), a **Dry run** button on that tab animates the chain without needing a real failure.
- A track with no sound after 3 seconds, a stall while buffering, or a clip under 30 seconds (a teaser) counts as a failed link.
- A dimmed row is a record that failed; tap it to retry.
- Drag the player down or tap the handle to close it.
- Inside the claude.ai preview, YouTube cannot play inside the page. The play button opens the track on YouTube instead, and a note says so.

## Gigs

1. Open the **Gigs** tab and tap **+ New gig**. Give it a name, venue, date, the bag or crate you will use, and optionally start from a playlist.
2. **Plan.** Add records (**+ Add records**), add a whole playlist, or remove records. Tap the next-step button when the list is right.
3. **Load out.** As you put each record in the bag, tick it. Crates moves it into the bag and remembers where it came from. Tap **Head out** (it tells you how many were left behind).
4. **At the gig.** Tick each record you actually played. Each tick writes a play (the gig date and venue) to the record's history.
5. **Back home.** Tick each record as it goes back on its shelf. Unticked records are flagged **Missing** in the summary; tap **Check in more** to continue.
6. The summary shows how many you played out of how many you packed. You can play the whole list with **Play the list** at any step, or delete a gig (records stay where they are and history is kept).

## Set history and the dig list

- On a record, tap **Log a play**, set the date and venue.
- The record shows when it was last played and how many times.
- In **Room**, tap **Not played in a year**. The list shows when each was last played, or "never logged". Tap **Play these** or **Save as playlist**.

## Save locations to Discogs (demo)

Settings, then **Save locations to Discogs**. When it is on, every record gets a pending "Location" value such as `K1·A2 (Acid)` or `Bag: Crater`, and a line on the record shows "Saved" or "Waiting to sync". **Sync now (demo)** marks the values as saved. **Nothing is sent to Discogs in the prototype.** The real app will write the Location field of your Discogs collection, at Discogs' rate limit.

## QR stickers

Stickers let you aim your phone at a shelf and jump straight to it.

1. In **Room**, tap **QR stickers** (or tap **QR sticker** inside a unit).
2. Choose which units. Leave **One per cubby too** on to get a sticker for every cubby, or off for one per unit.
3. Choose a size: 1, 1.5 or 2 inch. Bigger stickers also show the cubby's subtitle.
4. Check the preview, which shows exactly what prints, and the page count.
5. Choose an output:
   - **Print** (only on Crates' own site) opens the print dialog.
   - **Save print-ready page** saves an .html file; open it and the print dialog appears at actual size.
   - **Save SVG** saves all pages as one vector file.
   - **Save PNG** saves the first page only, as an image.

Printing tips:
- Print at **100 percent or "Actual size"**, on **US Letter** paper. Turn off "Fit to page" and "Scale to fit". Letter holds 54 stickers at 1 inch, 24 at 1.5 inch and 12 at 2 inch.
- **Test one sheet first.** Print on plain paper, hold a sticker against the shelf, and scan it with your phone before you print a full sheet of label paper.
- Use matte label paper or clear tape over the sticker; glossy glare makes QR codes hard to read.
- Keep the quiet white border around each code when you cut.
- Black and white is fine. Use a high-quality print setting for 1 inch stickers.
- A sticker links to `<site address>#K1-A2`. In the claude.ai preview and when run from your own computer, codes point to the published preview, not to your computer. Print the final stickers from the hosted site so they point to the real address, and re-print if the site moves.

## Settings

- **Accent color:** Signal red, Brass or Booth cyan.
- **Save locations to Discogs:** see above.
- **Reset demo collection.**
- The page follows your phone's light or dark mode, and reduced-motion setting.

## When something does not look right

- *The photo button is missing.* Photo recognition runs only when the page can send images to Claude (the claude.ai preview). Type records in, or use the simulated scan.
- *Nothing plays inline.* You are in the preview. Tap play to open YouTube, or use Crates' own site.
- *My records are gone.* The data lives in one browser. A different browser, a private window or cleared site data starts fresh from the demo.
- *The QR code opens the wrong place.* Each code carries the site address it was made on. Make them on the hosted site.

---

# Part B: Developing Crates

## What is in the repo

| Path | Purpose |
|---|---|
| `crates.html` | The prototype. Page content only (no `<html>` or `<head>`), so it can be published as a claude.ai artifact and wrapped for hosting |
| `scripts/build.mjs` | Wraps `crates.html` into a full page at `dist/index.html` and copies `logos/` to `dist/logos/` |
| `vercel.json` | Static deploy: build command, output folder, rewrites, security headers, CSP |
| `app/db/` | `001_init.sql`, `002_seed.sql`, `003_features.sql`, `004_seed_features.sql` |
| `research/` | Furniture and bag research JSON and notes; `build_presets.py` turns them into the preset block inside `crates.html` |
| `tests/` | Playwright tests (`test_crates.py`), the harness builder, screenshots |
| `logos/` | Logo concepts; concept 3 ("Half-pulled") is chosen |
| `docs/` | Architecture, data model, player spec, roadmap, infrastructure notes |
| `PRD.md`, `LIST.md`, `FUTURE.md`, `HOWTO.md` | Requirements, feature checklist, ideas, this guide |
| `CLAUDE.md`, `QA.md` | Rules for agents working here; the test catalog, error checks and review findings |

Rules for editing, code order, and conventions are in `CLAUDE.md`. Read it before changing `crates.html`.

## Run the prototype locally

Node 18 or newer is enough. There is nothing to install.

```bash
node scripts/build.mjs        # writes dist/index.html and dist/logos/
npx serve dist                # then open the URL it prints
```

`python3 -m http.server -d dist` works too. Opening `crates.html` directly in a browser will not work well: it is a page fragment, not a full document.

Notes:
- On `localhost` the QR stickers link to the published preview address, not to localhost (see `BASE_URL` in `crates.html`).
- The page loads the YouTube iframe API and Google Fonts from the internet; ZXing loads from jsDelivr on demand. Offline, the player falls back to link mode.
- Photo recognition needs `window.claude`, which exists only inside the claude.ai preview.

## Run the tests

The suite drives the real page with Playwright and system Chrome.

```bash
pip install playwright                      # add --break-system-packages on a managed Python
CRATES_NO_PATCH=1 python3 tests/test_crates.py
CRATES_NO_PATCH=1 python3 tests/test_crates.py search flip   # only tests whose name contains these words
```

- It expects Chrome at `/opt/google/chrome/chrome`. Edit the `CHROME` constant in `tests/test_crates.py` if yours is elsewhere. No `playwright install` is needed because it uses the system browser.
- Always set `CRATES_NO_PATCH=1`. Without it, the harness rewrites the boot order of the page, which once hid a real crash.
- External requests (fonts, YouTube) are blocked on purpose so the player runs in link mode; one test makes the YouTube API hang to check the timeout path.
- Output: pass or fail lines on screen, `tests/results.json`, and screenshots in `tests/shots/` (ignored by git). The suite has 15 numbered groups plus 8 extra cases (X1 to X8). The harness page `tests/harness.html` is generated and ignored.
- Before pushing, also syntax-check the inline scripts (see `CLAUDE.md`).

## Regenerate the presets

The 64 furniture and 41 bag presets live between `/*PRESETS_START*/` and `/*PRESETS_END*/` in `crates.html`. Do not edit inside the markers by hand.

```bash
# edit research/furniture.json or research/bags.json, then:
python3 research/build_presets.py
```

The script reads both JSON files, normalizes names, finishes, capacities and groups, and rewrites the block in place. It prints the counts to the terminal (`bags: 41  furniture: 64` today). Re-run the tests after.

## The database (Neon)

- Project `crates` (id `super-sea-94522798`), region aws-us-east-2, Postgres 17, branch `main`, database `crates`. Get the connection string from the Neon console or from the Vercel project's environment.
- Run the files in order. Every file is idempotent.

```bash
export DATABASE_URL='postgresql://...'      # from Neon; never commit it
psql "$DATABASE_URL" -f app/db/001_init.sql
psql "$DATABASE_URL" -f app/db/002_seed.sql             # demo owner; skip in production
psql "$DATABASE_URL" -f app/db/003_features.sql
psql "$DATABASE_URL" -f app/db/004_seed_features.sql    # demo gigs and plays; skip in production
```

- **Never commit `DATABASE_URL`**, a Discogs token or any key. `.gitignore` covers `.env*`. In code, secrets are read only on the server and never get a `VITE_` prefix.
- Try a new migration on a Neon branch first (copy-on-write), then apply it to `main`.
- The files separate statements with a line `-- ;;` so tools that run one statement at a time can split them. `psql -f` ignores those as comments and runs fine.
- Seed data uses `owner_id = 'demo'`. Remove it before real sign-in exists.
- The prototype does not use the database yet. Table and column details are in `docs/DATA_MODEL.md`.

## Deploy on Vercel

The site is static: one HTML page and the logos.

1. Push the repo to GitHub (`CarlosFranzetti/crates`).
2. In the Vercel dashboard choose **Add New, Project**, and import the repository.
3. Set **Framework Preset** to **Other**. Leave everything else alone: `vercel.json` already sets the build command (`node scripts/build.mjs`), the output directory (`dist`), an empty install command, clean URLs, rewrites, and the security headers.
4. Deploy. No environment variables are needed for the prototype.
5. When the real app lands, add `DATABASE_URL` (mark it sensitive) and the other server-only variables listed in `docs/ARCHITECTURE.md`.

Notes:
- The Vercel connector available to Claude sessions could not create projects (it returned 403), so create or link the project in the dashboard. After it exists, the connector can read deployments and logs.
- `vercel.json` rewrites everything except `/logos/` and paths with a file extension to `/index.html`. When `app/api` exists, the rewrite must also exclude `/api`.
- The Content-Security-Policy allows YouTube frames and scripts, jsDelivr and cdnjs scripts, Discogs and YouTube images, and Google Fonts. If you add a new third-party origin, add it there. `Permissions-Policy` allows the camera for the same origin.

## Publish the preview (claude.ai artifact)

The prototype is also published as a private page on claude.ai so it can be tried inside Claude. The published file is `crates.html` as it is (page content only).

1. In a Claude Code session in this repo, ask Claude to publish `crates.html` as an artifact. Publishing the same file path again updates the same link, so the link in stickers and docs stays valid.
2. The link is private by default. Share it only if you want others to open it.
3. The page remembers its own link in `ARTIFACT_URL` near the QR sticker code. If the preview is ever re-created at a new address, update that constant and republish.
4. Inside the preview, `window.claude` is present, which turns on photo recognition. YouTube cannot embed there.

## Agent swarm

Several agents may work in this repo at once, one per work package.

- **`CLAUDE.md`** (repo root) holds the repo rules: file order in `crates.html`, how to move records and render, escaping, copy style, secrets, branches and commits. Read it first.
- **`QA.md`** (repo root) holds the test catalog, the error checks, review findings and the work packages to pick from.
- Stay inside the files your package lists. `crates.html` is one file, so keep edits local to your section.
- If a doc disagrees with the code, the code wins; fix the doc in the same change.

## Where to look for what

| Question | File |
|---|---|
| What should it do? | `PRD.md` |
| What exists, simulated or missing? | `LIST.md` |
| What might come next? | `FUTURE.md` |
| How is data modeled, and which SQL? | `docs/DATA_MODEL.md`, `app/db/*.sql` |
| What is the planned stack and API? | `docs/ARCHITECTURE.md` |
| How does the player fall back? | `docs/PLAYER.md` |
| Phases and test strategy | `docs/ROADMAP.md` |
| Where is Neon, Vercel, GitHub at? | `docs/INFRA.md` |
| Where did the presets come from? | `research/*.md` |
