# Competitors, round 2: capture, photos, lending and companions

Scope: four areas that research/competitors.md does not cover in depth: fast cover capture and matching, multiple photos per item, lending trackers, and phone and desktop companions. The 12 apps in competitors.md are not repeated here. Feature ideas that already appear in LIST.md or FUTURE.md are skipped in the last section.

Verification: each source marked "verified" was read as a search excerpt on 2026-11-13. Anything else is from general product knowledge and is marked unverified. Treat unverified claims as leads to check in the app before building on them.

## Sources checked

- CLZ Music loan manager: https://clz.com/music/desktop/manual/windows/v15/en/topic/loan-manager (verified, excerpt)
- CLZ Music web loan notes: https://app.clz.com/music/manual/1/en/topic/managing-loans (verified, excerpt)
- Libib lending, managers: https://support.libib.com/libib/mobile-app/lending/lending.html (verified, excerpt)
- Libib lending, patron app: https://support.libib.com/ultimate/patron-app.html (verified, excerpt)
- Sortly sync: https://help.sortly.com/why-are-my-items-folders-or-photos-not-showing-in-the-app (verified, excerpt)
- Sortly product page: https://www.sortly.com/ (verified, excerpt)
- Discogs: https://www.discogs.com/ (product knowledge, unverified for the features listed below)
- Serato: https://serato.com/ (product knowledge, unverified)
- rekordbox: https://rekordbox.com/ (product knowledge, unverified)

## A. Fast capture and auto-match

What the apps do:

- Barcode-first capture is the norm. Most collection apps read a barcode, look it up, and save a match in one tap. Vinyl often has no barcode or a shared one, so a camera-first flow is needed as a fallback (unverified for the specific apps below).
- Libib's lending flow is built around a barcode scan from the mobile app, and it recommends scanning over typing an ISBN or UPC (verified, https://support.libib.com/libib/mobile-app/lending/lending.html). That same scan path is a usable capture pattern for adding records.
- Sortly's mobile app adds inventory from the camera and syncs to other devices through a "Sync Inventory" step with a Full Sync option (verified, https://help.sortly.com/why-are-my-items-folders-or-photos-not-showing-in-the-app). Sync is a separate step the user can see and rerun, not a silent background process.
- Vinyl-specific apps such as Record Scanner and Vinyl ID (covered in competitors.md) use a camera to read a cover or label and return candidate releases. Batch behaviour and multi-pressing choice are unverified in this round.
- CLZ's queue or batch-add mode is referred to in its product materials as a way to add many items before reviewing them (unverified; the page was not read this round).

Patterns to copy:

- Libib: scan first, then let the user confirm the match before it saves. Copy the barcode-to-record step, not the typed-ISBN fallback.
- Sortly: make sync visible and rerunnable. Show the last completed sync and a Full Sync button, so a missing record has an explanation.
- Queue captures and review them in one pass, so a record fair or shop session does not need a stable connection for each record (unverified for CLZ; the pattern is general).

Things to avoid:

- Auto-saving the top candidate with no confirmation. A wrong pressing then looks like a correct one in the collection.
- Treating the barcode as unique. Shared or missing barcodes on vinyl mean the app needs a fallback to catalog number and label.
- Sync that runs silently. If the user cannot see the last successful sync, a missing record looks like a bug in the app.

## B. Multiple photos per item

What the apps do:

- CLZ and similar apps store more than one cover image per item, usually a front and a back, with the front set as the default (unverified).
- Discogs supports personal images on a release in a user's own collection, separate from the release's public images (unverified for the exact field names). Discogs image licensing limits how they can be reused, so the app should show them only to the owner and should not mirror them (see the CLAUDE.md rule on Discogs images).
- Sortly attaches photos to items and folders and lets the user move an item between folders while keeping its photos (unverified for the move behaviour; the sync help page confirms photos are part of synced inventory).
- Libib keeps item images alongside the record and lets the owner choose which one shows in lists (unverified).

Patterns to copy:

- Keep one cover for lists and let the user pick which photo that is, without deleting the others (general pattern, seen in several inventory apps).
- Allow a photo to move with its record when the record moves to a new spot, rather than leaving the photo attached to the old location (Sortly pattern, unverified detail).
- Show photo count on the record row so a user knows whether a record has only a front cover (general pattern).

Things to avoid:

- Storing a second image per record without a way to reorder or delete it. Users end up with a photo they cannot remove.
- Mirroring Discogs images into the app's own storage. The Discogs terms and the CLAUDE.md rule rule this out.
- Making the back photo a required field. Most records do not need one, and a required field slows capture.

## C. Lending trackers

What the apps do:

- CLZ Music has a Loan Manager. Each loaned item carries a loan date, a due date, a return date, the loaner's name and notes. The user can edit each field after the fact, and can print the current loans to PDF (verified, https://clz.com/music/desktop/manual/windows/v15/en/topic/loan-manager and https://app.clz.com/music/manual/1/en/topic/managing-loans).
- CLZ shows an overdue pop-up when the desktop app starts, so overdue loans are surfaced without the user opening the loan list (verified, the same loan-manager page; the notice is described as part of the loan manager in the v19 help).
- Libib lending is a full circulation system: managers check items out and in, set due dates, place holds and manage patrons (verified, https://support.libib.com/libib/website/lending.html).
- Libib's patron app shows each patron their own current checkouts with out and due dates, plus a history of past checkouts, and lets them request a renewal (verified, https://support.libib.com/ultimate/patron-app.html).
- BookBuddy and similar book-library apps keep a borrower field and a due date on each loan (unverified).

Fields that matter for a DJ, from these apps:

- Borrower name, loan date, due date, return date, and a free-text note (loan date and due date verified in CLZ; borrower and note verified in CLZ).
- A loan that stays open after a gig or a session is still a loan. A status of "out" is more useful than a single boolean (general).

Patterns to copy:

- CLZ: the four dates and the borrower on one loan record, with notes. Copy the field set, not the UI.
- CLZ: the overdue warning at start-up. It needs no separate reminder service.
- Libib: a borrower-facing view that lists only what that person has. For Crates, the equivalent is a printable "what I have out" sheet for a friend or a club (general pattern).

Things to avoid:

- A lending flow that is a separate app or a separate screen the user must visit. Libib's patron app is a second product; a DJ lending a record to a friend will not install it.
- Renewal logic that is hidden. Libib lets a patron request a renewal, and a manager sees it. Without a shared view, renewals become a text message.
- Due dates with no time zone or no "no due date" option. A DJ often lends a record for an open-ended time, and a forced date makes the field useless.

## D. Phone and desktop companions

What the apps do:

- CLZ Cloud: a cloud copy of the collection that the desktop and web apps read from. Sync behaviour and conflict handling are unverified for this round.
- Sortly: cloud sync across mobile, desktop and tablet. The product page says updates appear in real time from any location (verified, https://www.sortly.com/). The help page shows the sync step is user-visible, with Menu > Sync Inventory and a Full Sync option (verified, https://help.sortly.com/why-are-my-items-folders-or-photos-not-showing-in-the-app).
- Serato and rekordbox: both have cloud or remote features that link a library to a second device. Serato's remote and mobile pairing, and rekordbox's cloud sync, were searched this round but the pages were not read. Treat their pairing and conflict behaviour as unverified.
- Discogs: the web collection is the source of truth for many collectors, and mobile apps read it. Mobile use is read-mostly for many users (unverified).

Patterns to copy:

- Sortly: the visible sync step with a last-sync time and a Full Sync button. Copy it as-is.
- Serato and rekordbox: pairing a second device with a short code or QR, rather than a full account setup for a one-off handoff (unverified; general pattern for DJ software).
- A read-only mobile view by default, with edits made on the device that is closest to the shelf. This matches how a DJ works at a shop or a gig.

Things to avoid:

- Two devices editing the same record with no conflict view. The last write silently wins, and a moved record disappears from the place the other device expects.
- Sync that only works online. A record fair or a venue has poor signal, so the app needs an offline queue (the FUTURE 11 offline PWA covers the build; this is the warning from the sync side).
- Making the phone a thin client that cannot show the shelf map. A DJ at a crate wants the same spatial view on the phone.

## Patterns to copy, summary

1. Libib: scan a barcode, then let the user confirm the match before it saves.
2. Sortly: show the last sync time and a Full Sync button, and keep sync a visible step.
3. CLZ: loan record with loan date, due date, return date, borrower and notes.
4. CLZ: overdue warning on start-up, with no separate reminder service.
5. Libib: the borrower sees only their own loans, with out and due dates.
6. Sortly: photos stay with the item when it moves folders.
7. Serato and rekordbox: a short pairing code or QR for a second device (unverified).
8. Queue captures offline and review them in one pass (general pattern).

## Feature suggestions for Crates

These 12 are ordered by value to a working DJ, not by effort. Each one is checked against LIST.md and FUTURE.md by keyword. Items that touch an existing unchecked item are marked, and the difference is stated.

1. **Gig return check** (S). After a gig, scan the crate or tick the packing list and see what did not come back. Why a DJ cares: records get left in a booth or a friend's car, and the return check catches it before the next gig. Note: distinct from FUTURE 76, which is the pull sheet, and from LIST 374, the shared packing list for a back-to-back set.

2. **Set-length estimator** (M). Add the duration of the records on a gig list against a target set length in minutes. Why a DJ cares: a 60-minute slot and a 90-minute slot need different crates. Data: tracks.duration_s already exists in the schema (LIST 519). Note: distinct from FUTURE 19, which is per-track playlists.

3. **Only-copy flag on gig lists** (S). When a record is the only copy in the collection and is on a gig list, mark it so the owner decides whether to take it. Why a DJ cares: a single copy of a favourite is at risk in a crate that travels.

4. **Repeat-set check** (S). Compare two gig lists and show records that appear in both. Why a DJ cares: a residency audience hears the same set twice if the lists overlap, and the owner wants to know before playing.

5. **Sold and for-trade status** (S). Mark a record as for sale or for trade, and hide it from gig planning and from default search. Why a DJ cares: a record that is leaving the collection should not appear on the next pull list.

6. **Fill missing durations from the video** (S). When Discogs has no duration for a track, use the length of the linked YouTube video as a fallback and mark it as estimated. Why a DJ cares: the set-length estimator needs durations, and several seed records have none (r5, Voodoo Ray). Note: adjacent to LIST 550, which covers storing duration on media links, not filling it.

7. **Move from search results** (S). Let the user move a record directly from a search result row, without opening the record. Why a DJ cares: a moved record is usually a quick action with a known target, and opening the record adds a step.

8. **Residency templates** (S). Save a gig's packing list as a template and reuse it for a recurring residency. Why a DJ cares: a weekly set has the same core crate every week. Note: distinct from LIST 374, which is about two DJs sharing one list.

9. **Last-audited date per unit** (S). Record when a cubby, bag or crate was last walked and show a stale badge after a set number of weeks. Why a DJ cares: a bag that was packed months ago may hold records that have moved. Note: distinct from LIST 226, which is per record.

10. **Crate weight estimate** (M, estimate). Show an approximate weight for a crate or bag from the record count and a per-LP weight. Why a DJ cares: carrying a full crate up stairs is a real limit. The per-LP weight is unverified and must be shown as an estimate, with the user able to set it.

11. **Bag scan stubs for unknown records** (S, overlap unverified). When a bag scan finds a record that is not in the database, offer a quick stub instead of a full add. Why a DJ cares: a record bought at a fair goes into the bag before it is catalogued. Check the bag-scan section of LIST.md before building, because the add flow may already cover this.

12. **Two-device conflict review** (L). When the same record is moved on two devices, show both moves and let the owner pick one. Why a DJ cares: a shelf move made on a phone at a shop should not silently undo a move made at home. Note: this is the sync half of FUTURE 11, which covers the offline build, and it is not on either list.

## Open questions for the owner

- Should lending (section C) stay out of scope until FUTURE 16 is decided, or should the four-date loan record be added to the record panel now?
- Is a Discogs personal image (section B) worth showing to the owner at all, given the image-licensing rule?
- Which second-device pairing does the owner want first: a short code, a QR, or a signed-in account (section D)?
