# Crates

<!-- Draft of the repo-root README. Copy to the repo root; the links below assume that location. -->

A DJ vinyl-cataloging app. Photograph your furniture and record bags, photograph your records, and Crates knows where every record is. Search a record and it tells you **Kallax 2, shelf B2**, or **bag Crater**. Then play the crate through a spinning-vinyl player and build playlists from what you find.

Built for one owner first (Los), on the same stack as the Discogs stream app: React, Tailwind, Vercel, LLM integrations, with Neon Postgres for data.

> Status (2026-10-20): Phase 0 prototype done, database live on Neon with demo data, no application code yet. Setup commands appear here once Phase 1 lands.

## How it works

1. **Capture furniture.** Pick a preset (Kallax sizes and finishes, other shelving, milk crates, boxes, DJ bags), photograph it, name it. Each unit gets an id: `K1`, `K2`, `B1`.
2. **Capture records shelf by shelf.** Photograph a cubby; a vision model proposes records, Discogs confirms them, you tap to accept.
3. **Find.** Search any record; see its place and whether it is away from its home slot.
4. **Flip and move.** Open a unit, pick a cell or "All", flip through, move a record in one or two taps.
5. **Bags.** Photograph a whole bag; Crates puts the records in and sends the ones it did not see back home, in one atomic step.
6. **Play and organise.** Slide-up player with a spinning vinyl, large-font playlist, redundant YouTube fallbacks, and an editable, drag-reorderable playlist set.
7. **Edit.** Correct Discogs data and add BPM, key, rating, condition, notes, tags and custom fields. The original Discogs snapshot is kept.

## Addressing

Cubbies are row letter plus column number (`A1..A4`, `B1..B4` on a 2x4 Kallax). Shelf codes always include the unit id, **`K2·B2`**, so they never look like a Discogs side or track position.

## Docs

| File | Contents |
|---|---|
| [docs/PRD.md](docs/PRD.md) | Problem, users, goals, flows F1-F9 with acceptance criteria, open questions |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | Tables, addressing, snapshot vs edits, example SQL, schema gaps |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Stack, capture pipeline, API routes, env var names, security |
| [docs/PLAYER.md](docs/PLAYER.md) | Port spec of the discogs-stream player and fallback chain, vinyl UI, playlist editor |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Phases 0-5 and test strategy |
| [docs/INFRA.md](docs/INFRA.md) | Neon project state, Vercel and GitHub blockers |

## Repository layout (planned)

```
app/
  src/      React SPA
  api/      Vercel Functions (the only code that touches the database)
  db/       001_init.sql, 002_seed.sql (exist)
  shared/   Zod schemas, addressing helpers
docs/
crates.html   Phase 0 prototype
```

## Ground rules

- `DATABASE_URL` and all API keys stay on the server. Nothing secret gets a `VITE_` prefix.
- Every query is scoped to the signed-in owner.
- No record is saved from a photo until the owner confirms it.
- Playback behaviour follows [PLAYER.md](docs/PLAYER.md), including fixes for the hazards it lists in the source app.
