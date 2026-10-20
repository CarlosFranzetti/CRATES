# Crates: future ideas

Ideas beyond what the prototype does today (see [LIST.md](LIST.md) for what exists and [PRD.md](PRD.md) for v1 scope). Last updated 2026-10-20.

Each idea has a one-line reason, a rough effort, and what it depends on.

- **Effort:** S is a day or two, M is a week or two, L is a month or more of part-time work.
- **Flags:** `[Discogs approval]` means the idea likely needs Discogs' written permission or a different API tier. `[ToS risk]` means it brushes against the API Terms of Use (caching limit, 6-hour freshness, image restrictions, no commercial use of restricted data). Read `research/features.md` section A before starting either kind.
- Ordering inside each group is by value to the owner, not by effort.
- These are ideas, not commitments. Anything not already in `docs/ROADMAP.md` has no date.

## Next

Closes the gap between the prototype and a daily-use app. Most of this is already specified in `docs/`.

1. **Real backend and sign-in** (L). Why: the prototype keeps everything in one browser, so a cleared cache loses the collection. Needs: Vercel project (create it in the dashboard), `app/api`, Neon Auth or similar, per-owner scoping on every query. Unblocks nearly everything below.
2. **Export and import of your data (JSON and CSV)** (S). Why: protects the browser-only data today and stays useful later as a backup. Needs: nothing; can ship in the prototype first.
3. **Discogs import by personal token** (M). Why: nobody will retype 800 records, and import gives covers, tracklists and YouTube links in one pass. Needs: backend, a Discogs token kept on the server, a throttled queue (60 requests a minute; about 34 minutes for 2,000 records). `[ToS risk]` for how long release data is stored; decide the snapshot policy (PRD open question 9) first.
4. **Real barcode lookup** (S). Why: the prototype shows example pressings only; this is the fastest accurate way to add post-1979 records. Needs: backend, Discogs `/database/search?barcode=`, a candidate picker filtered by format, country and year.
5. **Photo identification on the server** (L). Why: photo recognition works today only inside the claude.ai preview. Needs: backend, a vision model, Discogs search to confirm each candidate, a labeled photo set to measure accuracy, EXIF stripping and private photo storage. Never auto-commit; keep the tick-to-confirm step.
6. **Real Discogs Location write-back** (M). Why: puts "K1·A2 (Acid)" in your Discogs collection, searchable in the Discogs app, as a portable backup of where things are. Needs: Discogs import (instance IDs), the existing outbox table and trigger, a worker that respects 60 requests a minute, a decision on the text format (PRD open question 8). `[ToS risk]` low; it writes the owner's own data.
7. **Player hardening** (M). Why: the prototype handles the common failures; the spec covers the rest. Items: error-code handling (100, 2, 5 terminal; 150, 101 recoverable), autoplay retry after a skip, prefetch of the next four records, a background link verifier and weekly rescan, a quota notice with "Open in YouTube", a stop after one lap of dead tracks, saving working links back to the database. Needs: backend, `docs/PLAYER.md`.
8. **Movement history view and "where was this last?"** (S). Why: every move is already logged in the schema; the prototype shows none of it. Needs: backend (or a local event list).
9. **Order inside a cubby** (S). Why: flip order is undefined today. Needs: the owner's answer to PRD open question 1, then a `slot` column or a sort rule.
10. **Shelf capacity and full warnings** (S). Why: a cubby that fits about 50 LPs looks the same as one with 80. Needs: user-editable capacity per cubby (research found no sourced per-cube figure), a bar in the unit view.
11. **Offline PWA for gigs and record fairs** (L). Why: venues and fairs have bad signal, and gig mode is where the app is used under pressure. Needs: service worker, local-first store with sync and conflict rules, backend. Start with gig mode only (packing list, played ticks, return list).
12. **Accessibility pass** (M). Why: screen-reader names for cubbies ("Kallax 2, row B, column 2"), keyboard drag for playlists, 44 px targets, contrast checks on every finish. Needs: nothing.

## Later

Clear value, but each depends on the real app existing.

13. **Smart crates** (M). Why: DJs already think in Rekordbox and Serato smart crates; a saved filter by BPM, key, genre, tag, rating or "not played in a year" fits that habit. Needs: BPM and key data (typed by hand, or item 20), a saved-filter model.
14. **Export to Rekordbox or Serato** (M). Why: lets a Crates playlist become a digital crate. Needs: a decision on which format first (CSV, M3U or the vendor's own), BPM and key fields, and a way to match a vinyl record to a digital file. Note the two worlds only meet if the owner also has the track as a file.
15. **Photo-sweep re-inventory** (L). Why: photograph a shelf, read the spines, and flag records that are missing or in the wrong cubby. This is the "audit" that no catalog app does. Needs: photo identification (item 5), a compare step against the database, patience with spine reading accuracy.
16. **Lending tracker** (S). Why: "who has my copy of X" is a real way to lose records. Needs: a place called "Out on loan" with a name and date, and a reminder.
17. **Cleaning, play-count and sleeve log** (S). Why: sleeve replacement, last cleaned, and condition notes belong with the copy. Needs: extra fields on the record; set history already exists.
18. **Condition photos** (S). Why: proof of condition for insurance and selling. Needs: photo storage.
19. **Per-track playlists, cue notes and transition notes** (M). Why: DJs play a track, not a record; the schema already has per-track BPM and key. Needs: per-track links, a track-level playlist item, a Discogs tracklist import.
20. **BPM and key analysis** (L). Why: removes the typing. Needs: an audio source, which a vinyl catalog does not have; the old AcousticBrainz route is deprecated; YouTube audio analysis has ToS and quality problems. Likely a "tap tempo" and manual route first, a file match later (item 14).
21. **Value and insurance report** (M). Why: a condition-aware PDF of what the collection is worth. Needs: Discogs collection value and price suggestions (the owner must have seller settings completed). `[ToS risk]` for storing the numbers and for any commercial use; `[Discogs approval]` if offered to others.
22. **Label printer support** (M). Why: QR stickers print on letter paper today; a thermal label printer gives durable 1 inch labels. Needs: printer formats (Dymo, Brother), a physical test on the real shelf.
23. **Wantlist and shop mode** (M). Why: "do I own this?" scanned at the shop counter is the duplicate check in its most useful moment. Needs: Discogs wantlist read, barcode scanning, offline tolerance. Marketplace price hints `[ToS risk]`.
24. **Shared bag lists for back-to-back sets** (M). Why: two DJs splitting one bag or one crate need a shared list. Needs: multi-user (item 28), invitations.
25. **Discogs-style duplicate cleanup** (S). Why: after import, find the same release twice, mark the second as an intentional extra copy or a mistake. Needs: import, the duplicate key already in the schema.

## Someday

Large or uncertain; revisit once the single-owner app is in daily use.

26. **Native wrapper** (M). Why: background camera, NFC and better lock-screen player controls. Needs: the PWA first; a wrapper such as Capacitor.
27. **NFC tags as an alternative to QR** (S to M). Why: tap a tag on the shelf instead of aiming a camera in a dark booth. Needs: Web NFC (limited to Android Chrome), writable tags, the same deep-link format as the QR codes.
28. **Multi-user and OAuth for other collectors** (L). Why: other DJs and collectors want the same tool. Needs: Discogs OAuth 1.0a, row-level security, privacy review of photos. `[Discogs approval]` and `[ToS risk]`: Discogs user data and images are restricted data; check what is allowed before serving anyone else.
29. **Nearby-shop wantlist alerts** (L). Why: "a record on your wantlist is in a shop two blocks away." Needs: marketplace or shop data, location permission, background jobs. `[Discogs approval]` `[ToS risk]`.
30. **Public crate pages** (M). Why: share a playlist or a crate with other DJs or fans. Needs: a decision to use only owner-made photos and generated covers; Discogs images cannot be republished. `[ToS risk]`.
31. **Paid tier** (L). Why: a way to fund hosting and vision costs. Needs: written permission from Discogs, a design that works without Discogs images, and a name check (PRD open question 12). `[Discogs approval]`.
32. **Marketplace listing helper** (L). Why: sell a record straight from its page with its condition grades. Needs: Discogs seller API, strong guardrails. `[Discogs approval]` `[ToS risk]`.
33. **Household sharing** (M). Why: a partner who puts records back wrong. Needs: multi-user and a simple "who moved this" log.

## Experiments

Small bets worth a weekend each, to see whether they earn a place.

34. **Laser or LED shelf pointer** (M). Why: a published project drove a laser at the shelf position of a record; Crates already knows the cubby. Needs: a microcontroller and servo, or LED strips on the Kallax, and a calibration step.
35. **Photo overlay** (M). Why: show a marker on the photo of your shelf where the record sits. Needs: a photo per cubby and a pixel position per record; Claude vision could suggest the position.
36. **Voice search** (S). Why: hands full of records. "Where's Voodoo Ray?" Needs: the browser's speech recognition, a spoken answer.
37. **Shortest pull route** (S). Why: "pull order" sorts by shelf today; a route that walks the room once is nicer when the list spans several units. Needs: a position for each unit in the room.
38. **Play-frequency heat map** (S). Why: shows which cubbies you never dig in. Needs: set history over time.
39. **Harmonic mix suggestions** (M). Why: given the record on the deck, show records in the collection that fit by key and BPM, with their shelf. Needs: BPM and key fields filled in on enough records.
40. **Crate-digging mode on a phone at a store** (M). Why: scan a barcode, see "own it / on wantlist / similar in my collection". Needs: items 4 and 23.
