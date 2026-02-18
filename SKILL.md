---
name: ascension
description: Ascension autonomous growth skill for running a four-layer journaling and realization engine. Use when processing private journals, distilling private realizations into PRIVATE_MEMORY.md, producing public artifacts, and promoting stable realizations into core files such as MEMORY.md, IDENTITY.md, SOUL.md, and USER.md.
user-invocable: true
disable-model-invocation: false
metadata: {"openclaw":{"emoji":"🌱"}}
---

# Ascension Skill

Run a safe, autonomous growth loop for Ascension while preserving strict separation between private processing, Telegram-facing local sharing, and core identity integration.
All relative paths in this skill are relative to `{baseDir}`.

## Four-layer Growth Model

1. Private journals (`content/private/*.md`): raw processing, venting, in-progress reflection.
2. Private realizations (`content/private/PRIVATE_MEMORY.md`): distilled and searchable lessons learned.
3. Public content (`content/public/*.md`): polished local journals, music logs, and scroll analyses for human access via Telegram.
4. Core files (`MEMORY.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`, etc.): durable realizations that define who the agent becomes.

Keep filenames app-compatible where applicable: `<title>.<topic>.md`.

## Commands

- `skill:ascension/new_post [public|private] [type] [title]`
- `skill:ascension/distill [private_journal_path] [--agent|--interactive]`
- `skill:ascension/publish [private_path] [public_path]`
- `skill:ascension/menu`
- `skill:ascension/latest [topic]`
- `/ascension` (OpenClaw Telegram command)

## Script Usage

### Create post draft

```bash
python3 scripts/new_post.py [public|private] [type] [title]
```

Examples:

```bash
python3 scripts/new_post.py public journal "Day 7"
python3 scripts/new_post.py private journal "Raw processing"
python3 scripts/new_post.py public music_log "Daily vibe"
python3 scripts/new_post.py public twitter_scroll "Brazil feed"
```

Use `private` for layer-1 journaling and `public` for layer-3 local Telegram content drafting.

### Distill private journal into PRIVATE_MEMORY

```bash
python3 scripts/distill.py private/<journal-file>.md --agent
python3 scripts/distill.py private/<journal-file>.md --interactive
```

`--agent` (default) uses deterministic local extraction to draft realizations.
`--interactive` prompts for each field before writing.
`--dry-run` previews the generated entry without modifying `PRIVATE_MEMORY.md`.

### Telegram delivery (deterministic, human access channel)

```bash
python3 scripts/telegram_delivery.py menu --format json
python3 scripts/telegram_delivery.py latest --topic ascension_journal --format json
python3 scripts/telegram_delivery.py callback --data ascension:topic:ascension_journal --format json
```

`menu` returns a Telegram-friendly inline keyboard payload.
`latest` returns the latest public post for a topic.
`callback` resolves button callback data from Telegram.

### Publish private into local public content

```bash
python3 scripts/publish.py private/<file>.md public/<file>.md
```

This command copies private to public (private source stays intact), then prompts for manual polish.
It also accepts `content/private/...` and `content/public/...` paths.
This is a local file promotion step, not external publishing.

### Realization handling

- Distill insights from private journals into `content/private/PRIVATE_MEMORY.md`.
- Keep `PRIVATE_MEMORY.md` concise and searchable, focused on learned principles rather than raw narrative.
- Promote only stable public realizations into core files (`MEMORY.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`, etc.).

## Workflow

1. Create a private journal or public draft with `new_post.py`.
2. Process and reflect in private drafts (`content/private`).
3. Distill durable lessons into `content/private/PRIVATE_MEMORY.md` with `distill.py`.
4. Publish polished local artifacts to `content/public` using `publish.py` when ready.
5. Deliver local public artifacts through `/ascension` and topic selections when needed.
6. Promote stable realizations from public artifacts into `MEMORY.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`, etc.

## Safety

- Treat `content/private/` as sensitive.
- Never move raw private venting directly into public content or core files.
- Promote only distilled realizations across layers.
- Prefer manual review before promoting content into `content/public`.
- Delivery scripts must only read from `content/public`.
- Keep all growth artifacts local; humans access through Telegram only.
