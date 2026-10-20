# Competitor scan: vinyl and DJ collection apps

Research for Crates. Last checked 2026-10-20. Scope: how existing apps handle (1) physical location of records, (2) gig packing and set logging, (3) browsing a collection on a phone, and (4) adding records by barcode or photo. Read first: `README.md`, `LIST.md`, `FUTURE.md`. Every idea in the last section is checked against those files.

## Method and confidence

- Sources are App Store and Google Play listings, vendor help pages, and third-party reviews, found by web search and fetch. I did not install or test any app, so every "feature" below is what the vendor or reviewer says it does.
- Listings are marketing copy. Treat "worth stealing" as a lead to test, not a verified behavior.
- Several listings did not match their search titles. These are flagged in the per-app notes and in "Gaps" at the end.
- Crate Hackers prices come from a review on a site that competes with it (My Wedding Songs). Treat its criticism as partly promotional.
- The Beatport LINK article is from June 2021 and is probably out of date.

## Short version

1. Location: most collection apps store a location as a free-text field or a folder. None of the apps I could read model a shelf grid with cubbies. CLZ Music and iCollect are closest, with a location field and folder-style grouping. Crates' cell-level address is already ahead of them.
2. Gig and set logging: DJ software (Serato, rekordbox) has the strongest set-to-playlist and export patterns. Vinyl catalog apps have almost nothing for gig packing. Crates' gig flow is already more complete than any app found here.
3. Phone browsing: CLZ (cover wall, resizable thumbnails), iCollect (index bars, expandable sections) and On Rotation (full cover-art browsing) show the usable patterns. Letter jump indexes and quick filters are the clearest gap.
4. Barcode and photo adding: the common pattern is camera barcode scan plus Discogs lookup, with a batch mode in StackRoom. Photo identification is becoming standard (Vinyl ID, iCollect "AI Identification Scanning"). Crates already does both, but barcode batch mode at home is missing.

---

## Per-app notes

### 1. Discogs app (official, iOS)

Source: https://apps.apple.com/app/id1036449551 and collection help at https://support.discogs.com/hc/en-us/articles/360007331534

- **Steal:**
  - Search the collection by catalogue number, notes and custom fields (the listing calls this the latest update). Crates already searches all of these, so the pattern is confirmed as useful.
  - Wantlist items link to marketplace listings. A wantlist-to-shop match is the same idea as the "shop mode" in FUTURE 23.
  - Collection folders can be assigned from the add screen ("Add To Collection" then "assign a custom folder"). A quick assign step at add time is a good pattern to reuse for cubbies.
- **Do badly:** Physical location is not a first-class concept. Folders are capped at 1,000, and there is no shelf or grid model. The help page also does not say whether "Location" is a default custom field or a user-made one, so Crates' Discogs "Location" write-back (FUTURE 6) should be tested against a real account before it is built.
- **Barcode:** The store page says "Find an album by its barcode" but does not say whether it uses the camera. Treat the camera method as unverified.

### 2. StackRoom (iOS, Discogs-based)

Source: the URL https://apps.apple.com/mx/app/vinylvaultios2/id6742965007 returned this app's listing, not VinylVault. See the Gaps section.

- **Steal:**
  - Barcode scanning with a batch mode, so many records can be scanned in one session. This is the clearest model for a batch add flow at home (idea 6 below).
  - "Smart shelves" and "crates" as views over the same library, plus a "decade tap opens a shelf" pattern in Insights. Tapping a stat to open the matching records is a cheap navigation pattern.
  - "Collection gap finder" compares the collection against a reference list of essential albums. Useful later, not a priority.
- **Do badly:** The free tier stops at 25 records, and the Pro price is large (listed at $69 monthly or $399 yearly, currency not shown). The listing also does not mention storage locations at all, which is the core of Crates.

### 3. Vinyl ID / Record Value Scanner (iOS)

Source: https://apps.apple.com/us/app/-/id6758935180. The search index lists the same ID as "Record Scanner - Vinyl Snap" (https://apps.appfollow.io/ios/record-scanner-vinyl-snap/6758935180?country=se), so the name is inconsistent. Details below are unverified.

- **Steal:**
  - Photo or barcode identification from one screen: "Identify records by scanning the cover, barcode." Crates' add flow has the same two inputs, so the pattern is already covered.
  - Wishlist and collection in one list model, with the same record card in both.
- **Do badly:** Subscription-gated scanning after two free searches, and the listing has 4.0 from only 3 ratings, so it is hard to judge. No location concept.

### 4. iCollect Music: Vinyl Discogs (iOS)

Source: https://apps.apple.com/app/id476622260

- **Steal:**
  - A "Storage Location" field on each item, plus a "Loaned" list. The loan list is the simplest form of FUTURE 16.
  - Index bars and "multi-level sorting" for long lists. The index bar is the phone pattern Crates is missing (idea 7 below).
  - "Shake to Select" as a way to pick random items. A novelty, but the same idea could be "dig randomly from this cubby."
  - Bulk edit by holding a finger on a section header (Pro). Crates' multi-select could take a press-and-hold on a cubby header.
- **Do badly:** Unlimited storage and bulk editing are paid in-app purchases, and the free tier limits large collections. For a DJ with a few hundred records, this is a clear annoyance.

### 5. CLZ Music (iOS, Android, desktop)

Source: https://clz.com/music/mobile

- **Steal:**
  - Group the collection into folders by location, format, label, or genre, using the same field. Crates already groups by spot; the lesson is that location can be one of several grouping keys.
  - A "cover wall" with resizable thumbnails, and List, Card and Cover views. This is a good phone browsing reference.
  - Built-in barcode scanning with "One-by-One" add mode (v10.2), plus catalogue-number search for Discogs vinyl entries.
  - Custom fields created by the user (v11.0), so a DJ can add "BPM set" or "gig-ready" without a code change.
- **Do badly:** The location is a plain text field in the personal details, so there is no map from location to a physical shelf. The vendor page also claims a 95% barcode success rate with no test method given, which should be treated as marketing.

### 6. On Rotation (iOS)

Source: https://mwm.ai/apps/on-rotation/6756587007

- **Steal:**
  - Full cover-art browsing and "advanced search and filtering" applied to both the personal collection and the wider Discogs catalog. One search bar for both is a good pattern to borrow for "do I own this" lookups.
  - Insights broken down by custom fields, not just genre or artist. Crates' custom fields could feed a stats view.
  - Collection sync from Discogs that keeps the phone copy current, which is the sync pattern FUTURE 3 wants.
- **Do badly:** No storage locations and no playback. A collection app without a place model cannot answer "where is it", which is the question Crates exists to answer.

### 7. Serato DJ (desktop and mobile, DJ software)

Sources: https://serato.com/latest/blog/17729/learn-history and https://www.digitaldjtips.com/?p=2754662

- **Steal:**
  - History panel: every session is listed by date. You select it and choose "Serato Playlists" export, or drag it onto the Crates button to save it as a crate. A one-drag "session to crate" is the clearest pattern for turning a played set into a reusable list (idea 8 below).
  - "Clear" to reset played-track markers before a gig. Crates' play logs need the same reset idea for back-to-back gig prep.
  - Smart Crates that update themselves from rules, including play count (Serato DJ Pro 2.2). Already on FUTURE 13.
- **Do badly:** Session history export needs an online Serato account (per the Serato article), so it does not work offline in a booth or at a fair. The review of smart crates also says there is no dedicated gig-prep tool.

### 8. rekordbox (desktop, USB export)

Source: https://wearecrossfader.co.uk/blog/rekordbox-export-mode/ (third-party explainer, not Pioneer's own manual; the manual at https://cdn.rekordbox.com/files/20250718115648/rekordbox7.1.4_manual_EN.pdf was not read in full)

- **Steal:**
  - Sync Manager: tick the playlists that should go on a USB, and the app syncs adds and removes. A "tick a list, send to bag" model fits Crates' gig load-out step well.
  - History playlists: played sets can be turned into new playlists, when play history import is on.
  - Pulling data back from the device (cues and grid edits made on hardware go back to the library). For Crates, the equivalent is pulling "played" ticks back from a gig.
- **Do badly:** Playlists do not show when the USB is read on a computer, only on compatible Pioneer hardware, according to comments on the explainer. Rekordbox also breaks when a file is moved, because it stores the original path.

### 9. Crate Hackers (web, subscription)

Sources: https://pcdj.com/crate-hackers-helping-djs-find-the-perfect-next-song-every-time/ and https://www.myweddingsongs.com/reviews/crate-hackers/ (competitor review, see Method)

- **Steal:**
  - Crates sorted by BPM, key and energy, with a "Banger" button that finds high-energy tracks in the same key. A "find the next record in this key" action fits Crates' cubby model (FUTURE 39 covers the idea).
  - Magic Sorter: turn a playlist into a mixable crate sorted by energy, then export it. Crates could do the same with its own records.
  - Export as M3U when there is no direct sync. This is a simple, portable format.
- **Do badly:** $297 a year or $30 a month, with redundant playlists in the same categories, according to the review. Crates should not copy the price model.

### 10. Mixo (desktop and mobile, DJ library)

Source: https://www.digitaldjtips.com/mixo-wants-to-be-your-ultimate-dj-music-library/

- **Steal:**
  - Cross-device library sync that works through an existing Dropbox or Google account, so no new server is needed. Relevant to the sync plan in FUTURE 1.
  - Offline playback on the phone. Matches the offline gig need in FUTURE 11.
  - Export a library to every major DJ app. Crates should keep exports open (FUTURE 14).
- **Do badly:** Beatgrid sharing is limited to one beatgrid per track, per the reviewer. The article does not mention crates, gig packing or set logs at all.

### 11. Beatport LINK mobile app (iOS, 2021 article)

Source: https://pcdj.com/beatport-link-subscribers-rejoice-powerful-new-mobile-app-for-djs/

- **Steal:**
  - Playlists created on the phone sync to the DEX 3 hardware. The gig flow in Crates could sync a packed list to whatever the DJ uses on the night, though that is far off.
  - "Mobile-friendly digging": a phone-first browse of curated lists.
- **Do badly:** iOS only at the time, subscription only, and the sync works only with one hardware family. The article is five years old, so check the current app before relying on any of this.

### 12. iCrates (iOS review, older)

Source: https://digitaldjtips.com/?p=17455

- **Steal:**
  - Scan with the back camera, with results from several sources (eBay, Discogs, iTunes, Amazon), and a clear "available to buy" marker per result. For Crates, the "You own a copy" chip on each candidate is the same idea.
- **Do badly:** The reviewer said the scanner failed on several CDs, probably from glare or shaky hands. Typing the barcode worked. Crates' barcode-digits fallback already covers this.

### 13. MusicBee and Beatport collection tools

Not researched in depth. MusicBee's library and playlist model is desktop-first and is not a phone-browsing reference. Beatport's own library tools were only covered through the 2021 LINK article above. Both are left out of the ideas list.

---

## Patterns by topic

**1. Physical location**

| App | How location is modelled | Worth stealing |
|---|---|---|
| Discogs | Folders (cap 1,000), custom fields | Assign folder at add time |
| CLZ Music | Free-text location field, group-by location | Group by any field, one of several keys |
| iCollect | "Storage Location" field, Loaned list | Loan list |
| Serato / rekordbox | Crates and USB playlists (no physical place) | Tick-to-send sync |
| Crates | Cell-level address (K1·A2), home and came-from | Already ahead; add the missing pieces below |

**2. Gig packing and set logging**

- Serato: session history, one-drag to crate, clear played markers.
- rekordbox: tick playlists to send to a USB, history playlists, pull back performance data.
- Crates: gig plan, load-out ticks, played logs, back-home check-in. The gap is in printed lists, conflict checks and reusing a played set.

**3. Browsing on a phone**

- CLZ: cover wall, resizable thumbnails.
- iCollect: index bar, expandable sections, long-press bulk edit.
- On Rotation: full cover-art browsing with one search across collection and catalogue.
- Crates: room grid, cubby cards, sleeve stack, search. The gap is a letter index for long lists.

**4. Barcode and photo adding**

- StackRoom: batch barcode scan.
- Discogs app: barcode lookup (method unverified).
- iCollect, Vinyl ID: barcode plus photo AI identification.
- Crates: barcode digits, barcode photo decode, photo identification in the claude.ai preview. The gap is batch scanning at home.

---

## Ten feature ideas for Crates

Each idea is checked against `LIST.md` and `FUTURE.md`. Where it is close to an existing item, the overlap is noted. Effort follows FUTURE.md: S is a day or two, M is a week or two.

1. **Printable gig pull sheet** (S). A paper list of the gig's records, grouped by unit and sorted in pull order, with the cubby code and a tick box. Why: phones die in a dark booth or at a fair, and a paper list is what many DJs already carry. Overlap: none. LIST has sticker printing and the gig checklist, but no printable gig list.

2. **Format-aware packing check** (S). When a 12-inch or double LP is added to a bag or cubby that only fits 7-inch singles, show a warning, and list each bag's accepted formats. Why: some presets are 7-inch only (for example Ultimate 7" SlingBag 60 and Solid Blaze Vinyl-Trolley), and the mismatch is found only at the gig. Overlap: capacity text exists in LIST section 6, but not a format check.

3. **Pulled stack (holding place)** (S). A temporary location, "Pulled", for records taken out while digging or comparing, so they are not lost or flagged as missing. Why: a DJ pulls 12 records to compare and then forgets which ones. Overlap: none found in LIST; the move sheet has no holding area.

4. **Gig conflict check** (S). When a record is added to a gig, flag it if it is already packed for another upcoming gig on the same or a nearby date. Why: back-to-back gigs are common, and the same record packed twice is found too late. Overlap: LIST section 16 has "Shared packing list for a back-to-back set" as an open item. This idea is the warning, not the shared list.

5. **Set report export** (S). Export a gig's played records as CSV or text with artist, title, label, catalogue number, date and venue. Why: some promoters and venues ask for a list of played tracks or records for reporting. Whether a given venue or rights body needs it depends on the DJ's own arrangements; treat the need as unverified. Overlap: LIST section 24 has general CSV export, but not a played-set report.

6. **Batch barcode add at home** (M). A continuous scan mode: each barcode scanned goes into the chosen cubby, with a running count and a review list at the end. Why: StackRoom's batch mode is the model, and a DJ adding a new box of records needs it. Overlap: LIST section 13 covers single barcode add and "continuous barcode scanning in a shop" (a different use). This is the home version.

7. **Letter jump index for long lists** (S). A thin A-Z rail on the phone for the collection list and search results, which jumps to the letter. Why: with several hundred records, scrolling to "S" is slow, and iCollect's index bar shows the pattern works. Overlap: none. LIST section 9 has search but no index.

8. **Turn a played gig into a playlist** (S). One tap saves a gig's played list as a reusable playlist, and "run it again" starts a new gig from that playlist. Why: this is Serato's history-to-crate move, and a DJ who repeats a set wants it. Overlap: LIST section 14 starts a gig from a playlist and saves not-played lists, but not played gigs.

9. **Last-seen walk** (S). A list of records not moved, scanned or checked in for N months, sorted by unit, to walk and confirm. Why: a cheap audit that finds lost or misfiled records without the photo sweep. Overlap: close to FUTURE 8 (movement history) and FUTURE 15 (photo-sweep audit), but it uses the existing location events to create a checklist rather than a history view.

10. **Scan-to-select records in hand** (M). Scan the barcodes of records already on the table to tick them for a move or a gig pack. Why: the fastest way to select records from a pile. Caveat: it works only for records with barcodes, so it needs a fallback to the cover tick list. Overlap: close to LIST section 9 ("barcode scan from the search box") and section 10 (multi-select), but it is multi-select by scanning.

---

## Gaps and things I could not verify

- **VinylVault.** The App Store URL I used for VinylVault (https://apps.apple.com/mx/app/vinylvaultios2/id6742965007) returned the StackRoom listing instead. VinylVault itself was not checked.
- **Record Scanner / Vinyl ID.** The same store ID is titled differently in two places ("Vinyl ID: Record Value Scanner" in the App Store page, "Record Scanner - Vinyl Snap" in an index). Only the store page content was read.
- **Discogs barcode method.** Whether the Discogs app uses the camera for barcode scans was not stated on the listing.
- **Discogs custom field types.** The help page does not list field types or say whether "Location" is a default field.
- **StackRoom pricing currency.** The listing gives $69 and $399 without a currency.
- **Rekordbox manual.** The explainer was used instead of the official manual. Feature claims should be checked against the manual before any are copied.
- **Competitor claims.** Vendor claims (for example, CLZ's 95% barcode success) are not independently tested.

---

## Source list

- Discogs app: https://apps.apple.com/app/id1036449551
- Discogs collection help: https://support.discogs.com/hc/en-us/articles/360007331534
- StackRoom listing (returned for the VinylVault URL): https://apps.apple.com/mx/app/vinylvaultios2/id6742965007
- Vinyl ID / Record Value Scanner: https://apps.apple.com/us/app/-/id6758935180
- iCollect Music: https://apps.apple.com/app/id476622260
- CLZ Music mobile: https://clz.com/music/mobile
- On Rotation: https://mwm.ai/apps/on-rotation/6756587007
- Serato History: https://serato.com/latest/blog/17729/learn-history
- Serato smart crates article: https://www.digitaldjtips.com/?p=2754662
- rekordbox export mode (third-party explainer): https://wearecrossfader.co.uk/blog/rekordbox-export-mode/
- rekordbox 7.1.4 manual (not read in full): https://cdn.rekordbox.com/files/20250718115648/rekordbox7.1.4_manual_EN.pdf
- Crate Hackers (PCDJ): https://pcdj.com/crate-hackers-helping-djs-find-the-perfect-next-song-every-time/
- Crate Hackers review (competitor, see Method): https://www.myweddingsongs.com/reviews/crate-hackers/
- Mixo: https://www.digitaldjtips.com/mixo-wants-to-be-your-ultimate-dj-music-library/
- Beatport LINK (2021): https://pcdj.com/beatport-link-subscribers-rejoice-powerful-new-mobile-app-for-djs/
- iCrates review: https://digitaldjtips.com/?p=17455
