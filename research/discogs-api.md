# Discogs API: what Crates can and cannot do

Researched 2026-10-20 for the real (non-simulated) version of Crates. This file supersedes the Discogs fact sheet in `research/features.md` where they differ.

## How to read the labels

- **[Official]**: read today on discogs.com or support.discogs.com.
- **[3P spec]**: the community OpenAPI spec at `repo.rock-n-code.com/rock-n-code/discogs-service` (tag v0.6.0). It is not Discogs' text. Method, path and body shapes come from it.
- **[Unverified]**: no fetched source confirms it. Confirm with one live call before building on it.

Fetch caveat: `https://www.discogs.com/developers` is a client-rendered single-page app. Its `#page:` fragments returned navigation lists and summaries, not full endpoint bodies. Endpoint methods and bodies below therefore come from the 3P spec, and the official nav list is used to confirm which endpoints exist.

## 1. Collection, folders and custom fields

### Endpoints

Base URL: `https://api.discogs.com`. `{u}` is the username.

| Action | Method and path | Auth | Source |
|---|---|---|---|
| List folders | `GET /users/{u}/collection/folders` | Private collections need auth | Official nav ("Get Collection Folders"); path 3P spec |
| Create folder | `POST /users/{u}/collection/folders?name=...` | Required | 3P spec |
| Delete folder | `DELETE /users/{u}/collection/folders/{folder_id}` | Required; folder must be empty | 3P spec |
| List releases in folder | `GET /users/{u}/collection/folders/{folder_id}/releases` | Private needs auth | Official nav ("Collection Items By Folder"); path 3P spec |
| Add release to folder | `POST /users/{u}/collection/folders/{folder_id}/releases/{release_id}` | Required; returns 201 with `ReleaseInstance` (contains `instance_id`) | Official nav ("Add To Collection Folder"); path and response 3P spec |
| Move instance | `POST /users/{u}/collection/folders/{folder_id}/releases/{release_id}/instances/{instance_id}` with JSON body `{"folder_id": N}` | Required; 204 | 3P spec (same path as rating change) |
| Remove instance | `DELETE` on the same instance path | Required; 204 | 3P spec |
| List custom fields | `GET /users/{u}/collection/fields` | Required; returns `{"fields": [...]}` | Official nav ("List Custom Fields"); path 3P spec |
| Set field value | `POST /users/{u}/collection/folders/{folder_id}/releases/{release_id}/instances/{instance_id}/fields/{field_id}?value=...` | Required; 204 | Official nav ("Edit Fields Instance"); method and params 3P spec |
| Collection value | `GET /users/{u}/collection/value` | Required; returns `minimum`, `median`, `maximum` as strings | Official nav ("Collection Value"); 3P spec |

Source for the endpoint list: [Discogs developers page, User Collection section](https://www.discogs.com/developers#page:user-collection). The official nav lists these 15 operations: Collection, Get Collection Folders, Create Folder, Collection Folder, Get Folders, Edit Folder, Delete Folder, Collection Items By Release, Collection Items By Folder, Add To Collection Folder, Change Rating Of Release, Delete Instance From Folder, List Custom Fields, Edit Fields Instance, Collection Value.

### Custom field schema [3P spec]

`CustomField`: `id` (integer, read-only), `name` (string), `position` (integer, min 1), `public` (boolean), `type` (enum `dropdown` or `textarea`), `lines` (integer, textarea only), `options` (array of strings, dropdown only). Required: `id`, `name`, `position`, `public`, `type`.

### Can a "Location" field be created through the API?

**No, not per the evidence.** The official nav lists only "List Custom Fields" and "Edit Fields Instance". The 3P spec has no create or delete endpoint for fields. The [Collection help article](https://support.discogs.com/hc/en-us/articles/360007331534) says custom fields are created, updated and deleted under "Manage Custom Fields" in the web UI. Create the "Location" field in the web UI once, then read its `id` from `GET /users/{u}/collection/fields`.

### Setting a value

- `value` is a **query parameter**, not a JSON body field [3P spec, required string]. It must be URL-encoded. Crates values such as `K1·B2` or `Crater` contain a middle dot and spaces.
- Success returns 204 with no body.
- Unverified: whether a `dropdown` field accepts only pre-defined `options`. A `textarea` field is free text, and Crates' location values fit it.
- Unverified: whether `folder_id` in the path must be the instance's current folder. Read the instance's folder first.

### Other collection limits

- **Folder cap: 1,000 per collection** ([Collection help](https://support.discogs.com/hc/en-us/articles/360007331534), quoted: "there is a limit to 1,000 folders in your collection").
- Folders 0 and 1 cannot be renamed [3P spec]. The `features.md` claim that folder 0 ("All") cannot receive releases is unverified.
- Inferred, not stated: an instance lives in one folder at a time, because "move" is the only way to change it.
- Unverified: maximum number of custom fields, reserved field names, and whether a field can be private.
- Unverified: whether the default fields "Media Condition" and "Sleeve Condition" exist as described in `features.md`. The help article I read does not mention defaults.

### Rate limits

From the [official Rate limiting section](https://www.discogs.com/developers#page:home,header:home-rate-limiting):

- Authenticated: **60 requests per minute**. Unauthenticated: **25 per minute**, "with some exceptions".
- Tracked as a moving average over a 60-second window. No requests for 60 seconds resets it.
- Headers: `X-Discogs-Ratelimit` (limit), `X-Discogs-Ratelimit-Used`, `X-Discogs-Ratelimit-Remaining`.
- Discogs says it "may update these rate limits at any time" and asks clients to throttle locally.
- Circumventing the limit "may result in a temporary or permanent ban on your app or Discogs account".
- Image requests count toward the limit ([Images section](https://www.discogs.com/developers#page:images)).
- Unverified: the status code or retry header returned when the limit is exceeded. The docs do not say.

## 2. Barcode search and release identity

### Search

`GET https://api.discogs.com/database/search?barcode=...&type=release&format=Vinyl&country=...&year=...`

- **Auth is required**: "Authentication (as any user) is required." [Official Database section](https://www.discogs.com/developers#page:database)
- Parameters [Official, plus 3P spec]: `q`/`query`, `type` (`release`, `master`, `artist`, `label`), `barcode`, `catno`, `format`, `country`, `year`, `artist`, `label`, `title`, `track`, `page`, `per_page`.
- The official example barcode is `7 2064-24425-2 4`, with spaces. Whether search normalizes spacing is unverified. Test both forms.
- Results are a union of `ReleaseResult`, `MasterResult`, `ArtistResult` and `LabelResult` [3P spec]. The base `SearchResult` fields were not readable, so whether search results include `thumb`, `cover_image` or `uri` is **unverified**.

### Release detail

`GET https://api.discogs.com/releases/{release_id}` [Official, Database Release section]. Auth is not stated on the page. The example response includes: `id`, `title`, `artists`, `country`, `year`, `formats`, `labels` (with `catno`), `identifiers`, `images`, `thumb`, `videos`, `tracklist`, `notes`, `master_id`, `community`, `lowest_price`, `num_for_sale`.

- `identifiers[]`: `type` (required), `value`, `description` [3P spec]. Official example: `{"type": "Barcode", "value": "5012394144777"}`. Whether matrix/runout appears as an identifier type in the API is unverified.
- `images[]`: `type` (`primary` or `secondary`), `uri`, `uri150`, `width`, `height`, `resource_url` [3P spec].
- `videos[]`: `uri`, `title`, `description`, `duration`, `embed` [Official example].

### Multiple pressings

- No documented ranking for search results. A barcode can return several releases, so Crates needs a candidate picker, not an auto-pick.
- Discogs guideline 5 ([Barcodes and identifiers](https://support.discogs.com/hc/articles/360005054893-Database-Guidelines-5-Barcodes-Identifiers), read today) says:
  - Runout/matrix is "the main way to separate variants". Minor runout differences are variants of one release. Significant differences in a company, credit or job number mean a unique release.
  - Stickers applied after manufacture do not by themselves make a unique release.
  - Label codes do not identify the label, and SID codes do not identify the manufacturer.
  - "A release with a barcode cannot have been made before 1979" is stated as a general rule. Use it to rule out candidates.
  - A release may have several identifier rows, so a barcode list per release is normal.
- Practical picker: filter on `format`, `country`, `year`, `catno`. Then compare candidates on `identifiers` (matrix/runout) and `labels[].catno`. Each candidate needs its own release call (`GET /releases/{id}`), which costs rate limit. Batch or lazy-load these.

### Cover thumbnail

- `thumb` appears on the release example. Images are Restricted Data (section 4). Use the user's own photo for covers where possible.

## 3. Adding to a collection and folders as spots

- Add: `POST /users/{u}/collection/folders/{folder_id}/releases/{release_id}` with folder 1 ("Uncategorized") as the default target. It returns the `instance_id`, which is the stable key Crates needs.
- Folders as spots: they work, but they fit poorly.
  - Count: 1,000 folders maximum, so a per-cell folder scheme must stay under that. A 2x4 Kallax has 8 cells, but a multi-unit DJ setup could approach the cap. This is an inference.
  - One folder per instance, so a folder cannot record "also on shelf B2 of unit K2".
  - Folder creation and deletion add API writes that a text field avoids.
- Recommended: store the spot as text in the custom "Location" field. Use folders at most for coarse groupings such as bags or crates.

## 4. Image terms

**Official API behaviour** ([Images section](https://www.discogs.com/developers#page:images), read today):
- Image requests "require authentication and are subject to rate limiting."
- Authenticate with OAuth or Discogs Auth (key/secret). Discogs Auth gives image URLs but does not identify the user.
- Image URLs are signed and returned over HTTPS. Do not construct them. Altering part of a URL usually returns 404.

**API Terms, read today** ([API Terms of Use](https://support.discogs.com/hc/articles/360009334593-API-Terms-of-Use)):
- Restricted Data is "data that is not CC0". The license is "limited, personal, non-sublicensable, non-transferable, non-exclusive, revocable".
- Restricted Data may not be used "for any commercial purposes", and may not be transferred "to any third party".
- Caching: "You may not cache or store the Content longer than is necessary to provide a service to Your application's users."
- Freshness: "You may not display in any format or to any audience the Content if it is more than six (6) hours older" than Discogs' copy.
- Images must "comply with our Database Guidelines 13. Images". I could not read Guideline 13 (my fetch returned Guideline 5 instead). **Unverified.**
- The Terms do not mention AI or machine learning, and do not say what happens to data on user disconnect.

**Reading for Crates:** treat release images and `thumb` as Restricted Data. Display them to the user, but do not copy them into storage, a CDN or an export. Whether a browser hotlink counts as "transfer to a third party" is **unverified**. The safe reading is a server-side proxy that serves the image without storing it.

## 5. Attribution

From the [API Terms](https://support.discogs.com/hc/articles/360009334593-API-Terms-of-Use), read today:
- Required disclaimer: "This application uses Discogs' API but is not affiliated with, sponsored or endorsed by Discogs."
- "The notice must include a hyperlink to the discogs.com page that includes the data."
- The link "must not use any mechanism that prevents passing along search engine ranking credit".
- Unverified: the exact "Data provided by Discogs." wording carried over from `features.md`. It is not in the text I read.

## 6. Authentication choice

| Method | What it gives | Use for Crates |
|---|---|---|
| Personal access token | Full access to the token holder's account, high rate tier, image URLs. Sent as `Authorization: Discogs token=...` or `?token=`. Generated under Developer Settings. | Los's own collection, v1 |
| Discogs Auth (key and secret) | High rate tier and image URLs. Does **not** identify a user, so private collections are unreadable. Requires HTTPS. | Release lookup and barcode search without a user |
| OAuth 1.0a | Acts for any authorizing user. Endpoints: `GET https://api.discogs.com/oauth/request_token`, `https://www.discogs.com/oauth/authorize`, `POST https://api.discogs.com/oauth/access_token`. PLAINTEXT signature recommended. Verifier expires 15 minutes after the request token. Access tokens do not expire unless revoked. Test with `GET https://api.discogs.com/oauth/identity`. | Only if other collectors use the app |

- The official docs say to "keep this token private". They do not say "server-side only". Crates' own rule (token never in client code, no `VITE_` prefix) is the correct reading.
- **User-Agent is required**: "Your application must provide a User-Agent string that identifies itself." Generic strings may be silently blocked. An empty response often means the header is missing. Use something like `Crates/0.1 +https://<project-url>`.
- Only API version 2 exists. Send `Accept: application/vnd.discogs.v2.discogs+json` or rely on the default.

## 7. Changes in 2025 and 2026

- **No 2025 or 2026 Discogs API change found.** Searches returned no announcement. The official page says breaking changes are emailed to registered developers and points to an API Announcements forum thread that I could not read. **Unverified.**
- The "New DiscoGS Authentication Requirement" post at `bruji.com/blog/?p=1009` is from **2014**, about the CDpedia plugin. It says search required auth from 15 August 2014, and that an earlier image-download requirement had been added "without announcement". It is precedent, not a recent change.
- The official Terms reserve the right to "modify or discontinue Our API and the Content therein with or without notice to You", and to terminate access "at any time and for any reason".
- Unverified: 2025–2026 marketplace endpoint changes, and whether the per-day image cap from a 2014 forum thread still applies.

## Unverified items

1. Status code and retry header on rate-limit exceeded.
2. Whether a dropdown custom field requires pre-defined options.
3. Maximum number of custom fields; reserved names; private fields.
4. Search result field set (`thumb`, `cover_image`, `uri` on search results).
5. Whether search normalizes barcode spacing.
6. Folder 0 cannot receive releases.
7. `per_page` maximum of 100 (only `features.md` says so).
8. Guideline 13 (images) contents.
9. Marketplace price suggestions endpoint and its auth (the section did not render).
10. Whether `folder_id` in the set-field path must be the current folder.
11. Default custom fields "Media Condition" and "Sleeve Condition".
12. Whether "Discogs User Data" is Restricted Data, as `features.md` says.
13. Whether a browser hotlink of a Discogs image counts as transfer to a third party.
14. Exact attribution wording "Data provided by Discogs."
15. Any 2025–2026 API or Terms change (forum not readable).

## What this means for Crates

- **Location is a custom field, created in the web UI.** Create a "Location" textarea field once by hand. Then find its `id` with `GET /users/{u}/collection/fields` and write `K1·B2` or `Crater` with `POST .../instances/{instance_id}/fields/{field_id}?value=...`, URL-encoded. The sync outbox in `docs/DATA_MODEL.md` fits this without change, but the field must exist before the first sync.
- **Key every record by `instance_id`, not release ID.** Adding a release returns `instance_id`, and the field and move endpoints need it. Duplicate copies share a release ID, so the release ID cannot be the key.
- **Stop storing the full Discogs JSON indefinitely.** `docs/DATA_MODEL.md` keeps `discogs_snapshot` as the raw release JSON with no expiry. That conflicts with the Terms' "no longer than necessary" and six-hour freshness rules, and it holds image URLs. Keep only IDs, owner edits and Crates' own data. Re-fetch release metadata on demand, and cache at most a few hours.
- **Barcode scans are a candidate picker with a server-side call.** Call `database/search` with `barcode`, `type=release`, and optionally `format` and `country`. Show each candidate with its country, year, catno and matrix. Never auto-commit a pressing. Each candidate's detail call costs one of 60 requests per minute.
- **Budget the rate limit for import.** A 60-per-minute ceiling means a 2,000-record import with one detail call each takes about 34 minutes, before images. Run imports in a queue on the server, read `X-Discogs-Ratelimit-Remaining`, and do not fetch images in bulk. Images count toward the same limit.
- **Use a personal access token now, server-side only.** It goes in a Vercel function environment variable, with no `VITE_` prefix. Send a real User-Agent with a contact URL. Move to OAuth 1.0a only if other users join.
- **Put the Discogs attribution and disclaimer in the visible UI.** Add "Data provided by Discogs." with a hyperlink to the discogs.com release page near any Discogs data, and the non-affiliation sentence in the footer. Do not use a link that blocks ranking credit. Confirm the exact wording before launch, since it is unverified here.
- **Keep v1 personal and free, and make it work without Discogs images.** Images are Restricted Data, barred from commercial use, and Discogs may change or end the API "with or without notice". Use the user's own photos for furniture and bag covers. Show Discogs cover art only through a server proxy, with nothing stored.
