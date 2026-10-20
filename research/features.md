# Crates: feature and API research (2026-10-20)

Legend: [C] confirmed in a fetched page. [3P] from a third-party spec or wrapper doc, not Discogs' own text. [U] unconfirmed or from memory.

## A. Discogs API fact sheet

Primary sources: [API docs](https://www.discogs.com/developers), [API Terms of Use](https://support.discogs.com/hc/en-us/articles/360009334593-API-Terms-of-Use), [Collection help](https://support.discogs.com/hc/en-us/articles/360007331534), [Collection notes help](https://support.discogs.com/hc/en-us/articles/360007425393-How-Can-I-Add-Collection-Wantlist-Notes), [Barcodes & Identifiers guideline](https://support.discogs.com/hc/articles/360005054893-Database-Guidelines-5-Barcodes-Identifiers).

**Auth** [C, developers page]
- Personal token (Developer Settings): `Authorization: Discogs token=...` or `?token=`. Fine for a single-owner app. Server-side only; it grants account access.
- Key/secret ("Discogs Auth"): HTTPS only, identifies the app, not a user. It cannot read private collections.
- OAuth 1.0a: `/oauth/request_token`, `/oauth/authorize`, `/oauth/access_token`. Docs recommend PLAINTEXT signatures. Tokens do not expire unless the user revokes. Needed only if Crates serves other users.
- A descriptive `User-Agent` is mandatory (include a contact URL). Requests without one can return empty responses.

**Rate limits** [C]
- 60 requests/min authenticated, 25/min unauthenticated "with some exceptions". Moving average over 60 s.
- Headers: `X-Discogs-Ratelimit`, `-Used`, `-Remaining`. Pagination: `page`, `per_page` (max 100, default 50), `Link` header.
- Image requests count against the limit.
- Discogs forbids circumventing limits, e.g. by creating extra API keys (Terms).
- A 2014 Mp3tag thread mentions a 1,000 requests/day per-app cap on images ([thread](https://community.mp3tag.de/t/x-discogs-source-cover-art-fails-to-download/15507)). Likely obsolete, current status [U].

**Collection** [paths from 3P OpenAPI spec](https://repo.rock-n-code.com/rock-n-code/discogs-service/blame/tag/v0.6.0/Sources/DiscogsService/openapi.yaml); the official page lists names only; param semantics also seen in [minim docs](https://minim.readthedocs.io/en/dev/api-ref/minim.api.discogs.UsersAPI.html) [3P]
- `GET /users/{u}/collection/folders`; `POST` creates a folder. Folder 0 = "All" (read-only, cannot add to it). Folder 1 = "Uncategorized".
- `GET /users/{u}/collection/folders/{id}/releases` lists items. Each item carries an `instance_id`.
- `POST .../folders/{id}/releases/{release_id}` adds a release. It returns `instance_id`.
- Move an instance: POST to the instance with `to_folder_id`. Delete an instance: DELETE.
- `GET /users/{u}/collection/fields` lists custom fields (id, name, type, options, public).
- `POST .../instances/{instance_id}/fields/{field_id}` sets a field value (string).
- `GET /users/{u}/collection/value` returns min/median/max, owner auth required.
- Folder cap: 1,000 per collection [C, help page]. Default fields: Media Condition, Sleeve Condition (dropdowns, Goldmine-style marketplace grades), Notes (free text), customizable, private by default [C].
- Not confirmed: max number of custom fields, which custom-field types can be created, whether duplicate copies of one release are allowed [U].

**Release and master data** [C]
- `GET /releases/{id}` includes `tracklist` (position, title, duration), `identifiers` (type Barcode shown in sample; Matrix/other types exist on site, [U] whether all are in API), `labels[].catno`, `formats`, `images` (`uri`, `uri150`), `videos` (`uri` is a YouTube watch URL, `embed`, `title`, `duration`), `community` (have/want/rating), `lowest_price`, `notes`.
- `GET /masters/{id}` has `main_release`; `/masters/{id}/versions` filters by format/label/country/catno.
- `GET /releases/{id}/stats` gives have/want. The 3P spec says its documented response differs from the real one.
- Videos: the docs note YouTube embeds may use third-party cookies. Link rot of those YouTube IDs is expected but I found no source quantifying it [U]. Keep the owner's redundant-link fallback.

**Search** [C]: `GET /database/search` requires auth. Params include `barcode`, `catno`, `q`, `type=release|master`, `title`, `artist`, `label`, `format`, `year`, `country`, `track`.

**Collection list payload** [U, from memory]: the folder-releases endpoint returns `basic_information` (title, artists, labels, formats, thumb, year) but not tracklist or videos. Per-release `GET /releases/{id}` is therefore needed for videos. 2,000 records is roughly 34 min of calls at 60/min. Verify with a live call.

**Marketplace price** [3P spec]: `GET /marketplace/price_suggestions/{release_id}` returns price by condition grade (M..P) in the seller's currency. Needs auth and the user must have completed seller settings. Not confirmed on the official page (the section rendered as a heading only). Release marketplace stats (`lowest_price`, `num_for_sale`) need no auth per the same spec.

**Terms that shape architecture** [C, API Terms]
1. Caching: "You may not cache or store the Content longer than is necessary to provide a service to Your application's users."
2. Freshness: you may not display Content "more than six (6) hours older" than Discogs shows.
3. Attribution: "Data provided by Discogs." next to Discogs data, hyperlinked to discogs.com, no nofollow. Also show: "This application uses Discogs' API but is not affiliated with, sponsored or endorsed by Discogs."
4. Images are Restricted Data: governed by Discogs' image guidelines, cannot be passed to third parties or used commercially.
5. Commercial use of the API is "generally permitted" but Discogs can prohibit it. Restricted Data may not be used commercially at all.
6. Discogs User Data (username, collection) is Restricted Data. Discogs may change or end the API without notice.
7. Terms do not mention AI/ML training, and do not state a deletion-on-disconnect duty [C: absent].
- Not read: Discogs' image database guidelines and the monthly data-dump page (blocked by the sandbox permission prompt). Treat CC0 dump status and image licensing details as [U].

## B. Competitive landscape

| Product | Relevant to Crates | Source |
|---|---|---|
| Discogs app | Search incl. barcode, collection, wantlist, value; latest update adds collection search by catno, notes, custom fields. 4.8 from 67K ratings. No physical shelf model. | [App Store](https://apps.apple.com/app/id1036449551) |
| CLZ Music | Camera barcode scan (claims 95% success), "One-by-One" scan mode, location field and folders, cloud sync; $1.99/mo or $19.99/yr. Users praise duplicate avoidance. Sync gaps and post-v11 duplicate bugs in changelog. Discogs is a data source, not a sync. | [App Store](https://apps.apple.com/us/app/clz-music-cd-vinyl-database/id317997093) |
| GruKit DJ Vinyl Scanner | Closest rival: Discogs import (collection and wantlist), barcode scan, physical storage locations, cleaning and sales logs, deck queue. iOS 1.0, 0 ratings. | [listing](https://marlvel.ai/api/llm/apps/music/grukit-dj-vinyl-scanner) |
| Kallax (iOS) | Free, Discogs sync, BPM tagging, BPM/genre/mood playlist generator. 0 reviews. Name overlaps your furniture. | [App Store](https://apps.apple.com/app/kallax/id6758233437) |
| Waxshelf | Record "which shelf or crate it lives on"; Pro adds barcode duplicate check; no Discogs mention. | [AppGoblin](https://appgoblin.info/apps/6787195420) |
| crates.app | Name collision. Desktop and mobile library with YouTube/Bandcamp playback, BPM/key analysis, Discogs import; EUR 39 one-time Supporter license. Digital-library focus, no physical shelving. | [site](https://crates.app/) |
| DiscoDOS | CLI for DJs: mixes, transition ratings, set history, Marketplace listing edits. Key/BPM via AcousticBrainz is deprecated. | [GitHub](https://github.com/joj0/discodos) |
| Record Shelf | Reports (xlsx/csv/html) per Discogs folder; folders as "shelves". | [docs](https://discogs-record-shelf.readthedocs.io/en/latest/quickstart.html) |
| RUNOUT. | Look up matrix/runout, barcode or catno via Discogs; shows all candidates and lets you choose. | [about](https://runout-finder.lovable.app/about) |
| Shelf-laser project | Author stored shelf position in Discogs records and drove a laser pointer at the spot. Position entry was manual; automating it was future work. Shows the "where is it" need is real. | [Raspberry Pi](https://www.raspberrypi.com/news/vinyl-shelf-finder/) |
| Rekordbox/Serato | Crates, smart crates, playlists with BPM/key/cues: the mental model DJs already hold. Not deeply researched. | [Bonedo](https://www.bonedo.de/artikel/smart-crates-und-playlists-in-serato-rekordbox-und-co-einsetzen/) |

Gap Crates can own: photo-first physical addressing (furniture, slot, bag) plus "play it now", for DJs. GruKit has storage locations but no photo-based furniture model and no playback evidence.

**User sentiment: thin evidence.** Reddit and Discogs forum threads would not load (anti-bot wall) or were not surfaced by search. What I have: a Cd_collectors thread says scanning one barcode returns many pressings and checking each is tedious ([mirror](https://nyc1.lr.ggtyler.dev/r/Cd_collectors/comments/1hfw4nm/how_to_make_discogs_less_painful)); a vinyl-room article frames the core pain as "do I already own this?" and retrieval ([article](https://vinylroom.substack.com/p/put-them-in-their-place)); CLZ reviewers praise duplicate prevention. Treat feature demand below as inference, not measured. Worth 5 minutes of the owner's own pain list.

## C. Identification from photos and barcodes

- Barcode via Discogs `barcode=` search: strongest path for post-1979 releases ("a release with a barcode generally cannot have been made before 1979" [C]). Discogs entries may hold several barcodes with differing formatting and sticker-derived values, so misses and multi-pressing hits happen. Plan for a candidate picker, filtered by format=Vinyl, country, year.
- iOS Safari lacks the Barcode Detection API, so use a WASM decoder (ZBar or ZXing). Reported near-native speed on modern iPhones, but tilted codes (25-30 degrees) can be missed without extra passes ([source](https://eringen.substack.com/p/barcode-scanning-on-ios-the-missing)). Vinyl shrink-wrap glare and small stickers are likely worse [U].
- Catalog number and matrix/runout: Discogs says matrix/runout is entered verbatim per side, with variants. RUNOUT. calls matrix "the single most reliable clue" and returns all candidates. OCR of etched runout is hard [U, no source tested it]; offer manual typing with `catno=` search.
- Cover image recognition: App Store has many "AI record scanner" apps; I found no published accuracy figures [U]. Discogs' public API has no image-search endpoint [U, none listed]. Practical approach: vision-LLM reads artist/title/catno text from the photo, then verify via Discogs search and show candidates. Never auto-commit; require one tap to confirm.
- The "photograph furniture" step needs no recognition: user-assigned labels and photo as cover.

## D. Ranked feature ideas (effort S/M/L)

### Must-have v1
1. Discogs import via personal token (collection, instance ids, folders): everything else hangs off this. M
2. Furniture model: type presets (Kallax 2x2, 2x4, 4x4, crate, bag, DJ rack) with customizable grid; each with ID, name, cover photo. M
3. Slot addressing "Kallax 2 / B2" plus bag names ("Crater"); keep A1 style but show human name first. S
4. Search record to answer "Kallax 2, shelf B2" (typeahead on artist/title/label/catno). S
5. Browse container, slot or All; flip through covers (Kallax view). M
6. Move one record: 2-tap flow (search/select, pick destination) and undo. S
7. Whole-bag reconcile: photo or scan the bag, diff against expected, one-tap confirm. L
8. Add record by barcode with candidate picker; catno/title manual fallback. M
9. Add record by cover photo: vision read, Discogs verify, confirm. L
10. Player: playlist with large font, YouTube from release `videos`, redundant fallbacks and timeout skip (reuse discogs-stream). M
11. Own data in Neon: location, bag membership, history, keyed by Discogs `instance_id`; stores no mirrored Discogs content beyond what ToS allows. M
12. Discogs attribution, disclaimer and rate-limit-aware request queue with backoff. S

### Next
13. Duplicate warning at scan time ("you own this; it's in Kallax 1 A3"). S
14. Write-back of location to a Discogs custom field "Location" (portable backup, searchable in Discogs app). M
15. Move log / history and "where was this last?" S
16. BPM and key fields (manual first, optional analysis later), plus cue/transition notes. M
17. Played-at set history with date/venue; "not played in a year" digging filter. M
18. Gig bag packing list: build from crates, check off at load-out, reconcile on return. M
19. Condition grading (Media/Sleeve, Goldmine scale) mapped to Discogs default fields. S
20. Wantlist/digging list with barcode "do I own it" check in the shop. M
21. Shelf-full and capacity hints per cube; label printing (QR per furniture). M
22. Offline-tolerant PWA mode for gigs and record fairs. L

### Later
23. Lending tracker (who, when, reminder). S
24. Value and insurance report from collection value and price suggestions, with condition-aware PDF. M
25. Smart crates by BPM, key, genre, "not played" (Rekordbox/Serato mental model). M
26. Export to Rekordbox/Serato-friendly CSV playlists or Discogs CSV. M
27. Photo-sweep re-inventory: photograph a shelf, identify spines, flag missing or misplaced. L
28. Cleaning and play-count log, sleeve-replacement notes. S
29. Multi-user / OAuth for other collectors. L
30. Nearby-shop mode: wantlist alerts with marketplace stats. L

## E. Risks and mitigations

| Risk | Detail | Mitigation |
|---|---|---|
| Rate limit | 60/min; per-release fetch for videos at scale; images also count | Import in background with queue, persist progress; lazy-fetch release detail on first play; read `X-Discogs-Ratelimit-Remaining` |
| Caching ToS | Cannot store Content longer than needed; 6-hour freshness cap | Store IDs plus user-authored data in Neon; cache Discogs fields short-term (under 6 h) or refetch; confirm interpretation with Discogs if public |
| Image licensing | Images are Restricted Data, signed URLs, auth required; no third-party passing, no commercial use | Use user's own photos for covers and furniture; fetch Discogs art via authenticated server proxy only for display, do not mirror to storage or CDN; read image guidelines (not fetched) |
| Commercial path | Restricted Data barred from commercial use; Discogs may revoke API | Keep v1 personal or free; any paid tier needs written permission and a design that works without Discogs images |
| Token exposure | Personal token grants full account access | Keep it server-side in env; never in the client bundle |
| Barcode misses/multi-pressing | Old pressings lack barcodes; formats vary; many matches | Candidate picker, catno fallback, "match on format+year+country" shortcut |
| iOS camera | No BarcodeDetector in Safari; WASM cost on old phones | ZBar/ZXing WASM, scan-rate throttle, manual entry |
| YouTube links | Discogs `videos` may be dead, region-blocked or embed-disabled | Reuse redundant-link and timeout-skip scheme; allow manual link per record |
| Data divergence | Neon locations vs Discogs folders/fields drift | Neon is source of truth; optional write-back; reconcile on import by `instance_id` |
| Name clash | crates.app, Kallax (iOS), IKEA trademark "Kallax" | Check naming before public launch; use "cube shelf" in UI copy if public |
| Unverified evidence | Reddit/forum demand data not retrieved; two Discogs pages blocked | Re-check before building anything above "Must-have" |
