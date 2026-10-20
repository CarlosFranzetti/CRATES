# Crates: Player Port Spec

Source: the owner's Discogs stream app at `/home/claude/carlosfranzetti/discogs-stream` (read 2026-10-20). Citations are `file:line` against that tree. "Observed" means read from code; "inference" means reasoned from code but not run. Items marked **Hazard** should not be ported as-is.

## 1. Source map

| Concern | File |
|---|---|
| IFrame wrapper | `src/components/YouTubePlayer.tsx` |
| Orchestration: resolve window, errors, duration guard, prefetch, quota row | `src/components/MobilePlayer.tsx` |
| Search client, quota detection, caches, throttle | `src/hooks/useYouTubeSearch.ts` |
| Queue, skip, seek, 100ms time poll | `src/hooks/usePlayer.ts` |
| Background resolver | `src/hooks/useBackgroundVerifier.ts` |
| Spinning vinyl | `src/components/MobileAlbumCover.tsx` |
| Playlist rows, dimming | `src/components/MobilePlaylistSheet.tsx` |
| Server search chain and duration filter | `supabase/functions/youtube-search/index.ts` |

## 2. Concept mapping to Crates

| discogs-stream `Track` | Crates |
|---|---|
| `youtubeId` | `media_links` rank 0 for the track (or its record) |
| `youtubeCandidates` = `[youtube1, youtube2]` (`MobilePlayer.tsx:350`) | `media_links` rank 0 and rank 1 |
| `workingStatus` working / non_working / pending | `media_links.status` working / non_working / pending |
| `duration` with placeholder `240` (`:346`, `:555`) | `tracks.duration_s`, **null when unknown** (no sentinel) |
| `discogsTrackPosition` | `tracks.position` |

## 3. Playback chain (observed)

```
select track
 |- has a link          -> load it, status = working                       (MobilePlayer.tsx:713-715)
 '- no link -> RESOLVING: start 3s window, resolve in parallel             (:716-798)
      |- found              -> load, status = working, clear window
      '- none, or window ends while NOT playing/buffering -> non_working + skip

playing, onError:
   100 | 2 | 5     -> non_working + skip, no recovery                      (:880-885)
   150 | 101      -> A) cached alternate (rank 1), once per track          (:891-901)
                     B) one forced re-search per track (maxResults 8)      (:903-918)
                     C) still nothing -> non_working + skip                (:920-922)
   duration < 30s  -> same recovery as 150, once per track                (:933-947)
```

### 3.1 Engine (`YouTubePlayer.tsx`)

- IFrame API script injected once (`:33-38`). Host `https://www.youtube-nocookie.com`; `playerVars`: `autoplay 0, controls 0, disablekb 1, modestbranding 1, rel 0, iv_load_policy 3, playsinline 1, origin` (`:47-61`).
- `onReady` unmutes and sets volume 100 (`:64-67`). A new `videoId` calls `loadVideoById` (`:91-100`). Unmount calls `destroy()` (`:82-88`).
- State handling (`MobilePlayer.tsx:823-827`): `0` ended -> `skipNext`; `1` -> playing; `2` -> paused.
- `usePlayer` polls `getCurrentTime`/`getDuration` every 100ms while playing (`usePlayer.ts:181-190`). `skipNext/Prev/select` update the index, then after 100ms call `playVideo()` and set playing (`:210-232`, `:293-304`).
- Autoplay enforcement (`MobilePlayer.tsx:527-546`): after a skip, every 300ms up to 10 attempts (about 3s) call `playVideo()` unless the player state is 1 (playing) or 3 (buffering). It exists because the iframe may still be remounting.

### 3.2 Uniform 3s resolve window (`MobilePlayer.tsx:708-798`)

- Applies only to a track with **no** link. Every such track gets the same `skipDelay = 3000` (`:733`). There is deliberately no fast path for previously non_working tracks (`:729-732`).
- On expiry (`:734-749`): do nothing if cancelled, or if the user has not started listening (`:736`); **do nothing if `getPlayerState()` is 1 or 3** (`:738-744`, "never interrupt audio that's already producing sound"); else mark non_working, clear the video id, `skipNext()`.
- Resolution order inside the window (`:751-765`): saved mapping and Discogs videos via `resolveMediaForTrack`, then `searchForVideo`. A hit clears the timer and loads the video (`:768-777`). A miss before expiry marks non_working and skips (`:779-784`), but only if the user is listening; on the title screen it marks only (`:785-789`).
- Cleanup sets `cancelled` and clears the timer (`:793-796`), so a result arriving after a skip is dropped. The verifier retries the track later.

### 3.3 Error recovery (`handlePlayerError`, `:876-925`)

- Codes 100, 2, 5: terminal. 150, 101 (embedding disabled / not found by region): recoverable. Every other code is ignored (`:887`).
- Alternate first (`:891-901`): `candidateTriedRef` allows **one** swap per track; picks the first `youtubeCandidates` id different from the current video. Free, no network.
- Forced re-search (`:903-918`): `fallbackAttemptedRef` allows **one** per track. Calls `searchForVideo(track, { force: true, maxResults: 8 })`, which skips client caches and the in-flight dedupe (`useYouTubeSearch.ts:62-79`, `:152-154`) and sends `refresh: true`. Server-side `refresh` skips the DB and query caches (`index.ts:411`, `:427`), re-ranks, then upserts the new best match over the old row (`:588-600`) and appends the prior id as a last candidate (`:573-586`).
- Exhausted: non_working, `skipNext()` (`:920-922`).

### 3.4 Teaser / bad-duration guard (`:927-947`, `:548-564`)

- Trigger: `playerDuration > 0 && < 30` while the track's expected length is the 240 placeholder or `>= 90`, not yet handled for this track.
- The loaded video must be this track's video (`getVideoData().video_id` equals the expected id, `:939-942`). After a skip, `playerDuration` briefly still holds the previous video's length; without this check the new track is judged by the old one.
- Action: `handlePlayerError(150)`, so alternate then forced re-search. The server also drops results under 60s when the expected length is unknown or `>= 90` (`index.ts:522-529`) and scores duration closeness (`:531-546`) and probes embeddability with one `videos.list` call (`:548-571`).
- Real duration is written back only when `playerDuration >= 30`, the stored value is the placeholder, and the loaded id matches (`:555-561`). Never stamp a sub-30s "duration".

### 3.5 Quota fallback (observed)

- Detection (`useYouTubeSearch.ts`): regex on error text (`:33-35`), HTTP 429 (`:114-116`), or a 200 body `{ error: 'quota_exceeded' }` (`:123-126`). Sets a ref (visible to in-flight loops) and state (`:37-40`).
- A quota failure returns `''` and is **not** cached as "unavailable" (`:117-118`). Only a server answer with `source: 'db'` and no video is cached as unavailable (`:137-142`).
- The server runs the official API strictly last (`index.ts:503-520`), so quota-free tiers (scrape, Invidious, Piped) keep working. `isQuotaExceeded` only drives the banner and never gates a call (`CLAUDE.md`, background verifier notes).
- UI (`MobilePlayer.tsx:1323-1331`): a row "API quota reached - using fallback search" plus **Open in YouTube** that opens `youtube.com/results?search_query=<artist title>` (`handleOpenInYouTube`, `:996-1000`; `getSearchUrl`, `useYouTubeSearch.ts:160-163`). Always mounted with opacity toggled, to avoid layout shift. `QuotaBanner.tsx` is imported (`:26`) but never rendered.
- The server route also returns `quota_exceeded` as a 200 on purpose (`index.ts:508-512`), so it never surfaces as a runtime error.

### 3.6 Background verifier (`useBackgroundVerifier.ts`)

- Priority queue (`:34-86`): 1) current track, 2) next 3 tracks, 3) all pending tracks (skipping non_working), 4) non_working tracks, retried at lowest priority so transient failures heal. A track needs work if it lacks a link or a real cover (`:44`, `:57`, `:69`).
- One at a time (`processingRef`, `:112`). Polls every 3000ms (`:188-192`) and self-reschedules 500ms after each item (`:179`). When the queue empties it clears non_working ids so the next cycle retries them (`:101-108`).
- Per item (`:119-168`): cheap resolve first (saved mapping, Discogs videos), then search. For non_working tracks the search is `force: true, maxResults: 8` (else 5) (`:144-149`). Result sets status working or non_working. `triggerImmediate()` runs a cycle now (`:202-206`).
- Server-side counterpart: `youtube-rescan-weekly` re-checks stored links (`CLAUDE.md`). Crates needs an equivalent Vercel Cron.

### 3.7 Prefetch (`MobilePlayer.tsx:800-821`)

- On every index or playlist change, take `playlist.slice(currentIndex + 1, currentIndex + 5)` (the next **4**), drop tracks that already have a link or were prefetched (`prefetchedRef`), and call `prefetchVideos`. Results set working or non_working. `prefetchedRef` is cleared when the track count changes (`:654-656`).
- `prefetchVideos` runs batches of 3 with a 1s pause (`useYouTubeSearch.ts:165-185`); every search is throttled to one per 500ms (`:31`, `:81-87`) and de-duplicated by `artist-title` (`:76-79`).

### 3.8 Dimmed rows (`MobilePlaylistSheet.tsx`)

- `non_working`: `opacity-50`, `cursor-not-allowed`, small Ban badge on the cover (`:320-337`, `:362-366`). **Observed: the click handler returns early, so the row is display-only** (`:157-163`).
- `pending` (no link and not working): `opacity-75` (`:321-323`). `working`: full opacity.
- Current row: `bg-primary/10` plus a left border.

## 4. Hazards: do not port as-is

1. **Drift between docs and code.** `CLAUDE.md` says a non_working row "click once to trigger silent background retry + show spinner badge". The code has `const retryingId = null` (`MobilePlaylistSheet.tsx:63`), no retry, and an orphan comment at `MobilePlayer.tsx:1059`. Crates implements the documented behaviour (section 7).
2. **Effect re-run cancels the window (inference).** The resolve effect depends on `skipNext`, `applyTrackPatch`, etc. and returns early via `lastSearchedTrackId` (`:711-712`). If any dependency changes mid-resolve (for example `skipNext` changes when `playlist.length` changes), cleanup cancels the in-flight resolve and the timer, and the re-run exits early, so the track gets neither result nor skip. Port as an explicit per-track state machine, not an effect with a ref guard.
3. **Old audio can defeat the 3s guard (inference).** `setCurrentVideoId('')` (`:723`) does not stop the iframe because `YouTubePlayer` only reacts to a truthy id (`:93`). The old video can stay in state 1, so the guard's own check (`:741`) sees "playing" and never fires. Port: call `pauseVideo()` when entering RESOLVING, and test "playing" against the **expected** video id.
4. **No dead-list guard.** `skipNext` wraps with modulo (`usePlayer.ts:213`), so a queue of all non_working tracks skips forever. Stop after N consecutive skips (N = queue length) and show "nothing playable".
5. **Re-search can return the failing id.** The client takes `videos[0]` (`useYouTubeSearch.ts:130-131`) and never compares it to the failing id (`MobilePlayer.tsx:912-918`). Send `exclude: [failedIds]` and filter again on the client.
6. **Quota flag never resets** (`useYouTubeSearch.ts:25`, no `setIsQuotaExceeded(false)`). Reset at the next Pacific midnight, and clear on any successful official-API call.
7. **Prefetch marks non_working on any empty result** (`:812-819`), including transient failures. Keep the verifier retry (priority 4), and do not write `non_working` to the database from a prefetch miss; hold it in memory.
8. `YouTubePlayer`'s "Video not linked yet / Search on YouTube" overlay is unreachable (`showVideo` is always false, `MobilePlayer.tsx:1105`, `:1367`). Replace with the quota row's Open in YouTube action on the track.
9. `candidateTriedRef`, `fallbackAttemptedRef`, `badDurationHandledRef` live for the page session only. In Crates, reset per page load; persist the outcome in `media_links`.
10. The 240s placeholder doubles as "unknown". Crates uses null.

Not ported in v1: the direct-audio `<audio>` engine and pitch fader (`MobilePlayer.tsx:567-606`), which need the yt-dlp / Invidious edge functions. Media Session lock-screen controls (`useMediaSession`) are a Phase 5 nice-to-have.

## 5. Crates fallback state machine

```
IDLE -> select(track) -> RESOLVING(window 3s)
RESOLVING --link found--------------------> LOADING(link)
RESOLVING --none | window end, not playing-> DEAD --> skip (count++)
LOADING --state 1 / 3-----------------------> PLAYING  (reset skip count)
LOADING | PLAYING --err 100/2/5------------> DEAD
LOADING | PLAYING --err 150/101 | dur<30---> ALT (once) -> LOADING(rank 1)
ALT fails -> RESEARCH (once, force, exclude failed ids) -> LOADING | DEAD
DEAD: media_links.status = non_working, last_checked_at = now(); verifier retries later
```

- Link candidates: `media_links` for the track, then for the record, ordered by `rank`, skipping `non_working`; then Discogs `snapshot.videos`; then `POST /api/media/resolve` (server search chain, official API last).
- On any success upsert `status = working, last_checked_at = now()`. If the alternate wins, swap ranks 0 and 1 in one statement so the next play starts on the working one.
- Constants: window 3000ms, autoplay retry 300ms x 10, teaser threshold 30s (server drops under 60s), prefetch 4, verifier head 3, search throttle 500ms, poll 3000ms.
- Unit-test with a fake `YT.Player` that emits state/error events and fake timers (see ROADMAP).

## 6. Slide-up player and spinning vinyl

- **Shell.** A bottom sheet over the app. Collapsed: a mini bar (cover, title, artist, play/pause) pinned above the tab bar. Expanded by tap or drag handle; dismissed by dragging down. Content column max 440px, centered (as `MobilePlayer.tsx:1146`). Safe-area padding.
- **Vinyl** (`MobileAlbumCover.tsx`), container `clamp(212px, 33svh, 295px)` with `aspect-ratio: 1/1` (`MobilePlayer.tsx:1255`; width-only clamp avoids Safari oval distortion):
  - Disc: `rounded-full`, `vinyl-black hsl(220 15% 5%)`, `shadow-vinyl` (`:90`; tokens `index.css:49-50`).
  - Grooves: three rings at inset 8%, 16%, 24%, `vinyl-groove` at 30/25/20% opacity (`:93-95`).
  - Dust: 10 white specks in a `100x100` SVG inside the rotating disc. Position from a seeded LCG (`r*1664525+1013904223`) seeded by `hashString(id)`; radius 23-47 (strictly in the groove band), size 0.08-0.26, opacity 0.03-0.09 (`:26-48`). Seed with the record or track id so a record always looks the same.
  - Label: the cover art, inset 28%, circular, 2px groove border; fallback gradient with a disc glyph (`:115-128`). Spindle hole: inset 47%, background color (`:131`).
  - Spin: `animate-spin-slow` = 8s linear infinite while playing (`tailwind.config.ts:127`). **Pause with `animation-play-state: paused`**, not by removing the class (`:90` removes it and the disc snaps to 0deg); `index.css:195-201` already has a `.vinyl-spin.playing` class that does this.
  - Pulse glow: ring at `-inset-1`; outer glow at `-inset-4` using `pulse-slow` (20s, `box-shadow` from `--pulse-color`), or `rainbow-pulse` (16s hue walk plus a 3.7s scale breath) (`:72-87`, `tailwind.config.ts:100-124`). Settings `pulseEnabled` default on, `rainbowPulse` default off. Honor `prefers-reduced-motion` (new): no spin or pulse, static disc.
  - Tap the disc toggles play/pause (`:68`).
- **Below the disc:** track info, timeline (drag seeks), transport (prev, play, next, +/-5s via `seekTo`, shuffle), like. Shuffle defaults **off** in Crates (ordered playlists are the point); the queue source can be a playlist, a shelf (`K2·B2`), a bag, or search results.
- **Status strip** (always mounted, opacity toggled): quota row and "Finding stream..." (`MobilePlayer.tsx:1317-1343`).

## 7. Playlist view and editor

- **Larger font.** discogs-stream rows are `text-sm` title and `text-xs` artist (`text-xs` / `10px` in tight mode, `MobilePlaylistSheet.tsx:371-374`). Crates default: title 18px semibold, artist 15px, cover 48px, row min-height 60px; a "Compact" setting returns to 14/12px. Current row keeps the accent bar. Show shelf code (`K2·B2`) or bag name as a muted third element.
- Search by title/artist, runtime total ("X of Y tracks", h:mm / m:ss), and facet chips (genre, label, decade, country: OR within a facet, AND across; top 12 by frequency; display-only so queue indices are preserved) are ported from the sheet (`:82-125`, `:140-145`).
- **non_working row (fixing hazard 1).** First tap starts a silent forced re-resolve, shows a spinner badge on the cover, no navigation. If it resolves, the row un-dims and a second tap plays. If not, the badge returns to the Ban icon and a toast offers Open in YouTube.
- **Editor.** Create (name, optional color), rename inline, delete with a confirm dialog, duplicate (copies items in order, name "X copy"). Reorder by drag (`@dnd-kit/sortable`, a new dependency; discogs-stream does not use it): drag handle on the left, long-press on touch, keyboard move with space + arrows. Optimistic update, then `PUT /api/playlists/:id/order`; on 409 refetch. Add from a shelf, bag, or search result via multi-select and "Add to playlist", with the last-used playlist as a one-tap target. A `playlist_items` row with null `track_id` means the whole record: expand to its tracks that have links, in tracklist order. The same record may appear twice.
