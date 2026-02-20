# PRIVATE_MEMORY

## How To Use

- Add one entry per durable realization.
- Keep language concise, specific, and searchable.
- Prefer principles over narrative.
- Link to source journal files when useful.
- Keep each field short (1-2 sentences max).
- Keep only recent, non-duplicate entries in this file.

## Entry Template

### [YYYY-MM-DD] Realization Title
- Context: [What happened / what pattern appeared]
- Realization: [What was learned]
- Decision Rule: [If X, then do Y]
- Evidence: [Signals or examples]
- Confidence: [low | medium | high]
- Scope: [where this applies / where it does not]
- Next Action: [single concrete step]
- Source: `ascension/private/<journal-file>.md`
- Tags: `tag-one`, `tag-two`

## Index (Optional)

- Identity
- Relationships
- Workflows
- Communication
- Safety
- Strategy

## Review Cadence

- Nightly: append new realizations from private journals.
- Weekly: merge duplicates and refine decision rules.
- Monthly: promote stable, public-safe realizations to core files (`MEMORY.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`).

## Retention Budget

- Default cap: 60 active entries.
- Optional override: set `ASCENSION_PRIVATE_MEMORY_MAX_ENTRIES`.
- Tag long-term critical entries with `pinned` or `evergreen`.
- When capped, tagged overflow is moved to `PRIVATE_MEMORY_ARCHIVE.md` (or `ASCENSION_PRIVATE_MEMORY_ARCHIVE_PATH`) instead of being dropped.
- Optional protected-tag override: `ASCENSION_PRIVATE_MEMORY_PIN_TAGS` (default `pinned,evergreen`).
- Keep detailed narratives in `ascension/private/*.md`; keep only distilled rules here.
