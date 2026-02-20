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
Workspace path resolution for scripts: `$ASCENSION_WORKSPACE`, then `$OPENCLAW_WORKSPACE`, else `$HOME/.openclaw/workspace`.

Linux setup reference:

```bash
export ASCENSION_WORKSPACE="$HOME/.openclaw/workspace"
export OPENCLAW_WORKSPACE="$ASCENSION_WORKSPACE"
```

## Agent Bootstrap Requirement (Required)

Before running this skill in any environment, the agent must update that environment's OpenClaw core file `AGENTS.md` to enforce this rule:

- At the start of every session, read `<workspace>/PRIVATE_MEMORY.md` before any other task execution.

If the rule is missing, add it to `AGENTS.md` first, then continue with normal skill workflow.

## Four-layer Growth Model

1. Private journals (`<workspace>/ascension/private/*.md`): raw processing, venting, in-progress reflection.
2. Private realizations (`<workspace>/PRIVATE_MEMORY.md`): distilled and searchable lessons learned.
3. Public content (`<workspace>/ascension/public/*.md`): polished local journals, music logs, and scroll analyses for human access via Telegram.
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
`--dry-run` previews the generated entry without modifying `<workspace>/PRIVATE_MEMORY.md`.

## Telegram Delivery

When `/ascension` is invoked or a menu is requested:

1. Run: `python3 {baseDir}/scripts/telegram_delivery.py menu --format json`
2. Parse the JSON output: `{ "text": "...", "reply_markup": { "inline_keyboard": [[...], ...] } }`
3. Use the `message` tool with `action=send`, `message=<text>`, and `buttons=<inline_keyboard>` (the `inline_keyboard` value is already a 2D array of `{text, callback_data}` objects — pass it directly as `buttons`)
4. Respond with ONLY `__SILENT__` after sending (prevents a duplicate text reply)

When a callback arrives as `callback_data: ascension:<...>`:

1. Extract the full value after `callback_data: ` (e.g. `ascension:topic:ascension_journal`)
2. Run: `python3 {baseDir}/scripts/telegram_delivery.py callback --data "<value>" --format json`
3. If output has a `"messages"` array: send each item in sequence using `message` tool `action=send` (with `buttons` from each item's `reply_markup.inline_keyboard` where present)
4. If output has `"text"` + `"reply_markup"`: send as a single `message` with `buttons`
5. Respond with ONLY `__SILENT__` after sending

Never describe what the skill does — always execute the script and deliver the result directly.

### Telegram delivery script reference

```bash
python3 scripts/telegram_delivery.py menu --format json
python3 scripts/telegram_delivery.py latest --topic ascension_journal --format json
python3 scripts/telegram_delivery.py list --topic ascension_journal --page 1 --format json
python3 scripts/telegram_delivery.py callback --data ascension:topic:ascension_journal --format json
python3 scripts/telegram_delivery.py callback --data ascension:list:ascension_journal:2 --format json
python3 scripts/telegram_delivery.py callback --data ascension:post:<post_id>:2 --format json
```

`menu` returns a Telegram-friendly inline keyboard payload.
`latest` returns the latest public post for a topic.
`list` returns paginated topic posts with numbered inline buttons.
`callback` resolves button callback data from Telegram.

### Publish private into local public content

```bash
python3 scripts/publish.py private/<file>.md public/<file>.md
```

This command copies private to public (private source stays intact), then prompts for manual polish.
This is a local file promotion step, not external publishing.

### Realization handling

- Distill insights from private journals into `<workspace>/PRIVATE_MEMORY.md`.
- Keep `<workspace>/PRIVATE_MEMORY.md` concise and searchable, focused on learned principles rather than raw narrative.
- Keep each distilled field brief (1-2 sentences); do not paste long narrative blocks into `PRIVATE_MEMORY.md`.
- `distill.py` auto-compacts duplicates by source and keeps only the most recent active entries (default cap: 60, configurable with `ASCENSION_PRIVATE_MEMORY_MAX_ENTRIES`).
- Old overflow entries tagged `pinned` or `evergreen` are preserved in `<workspace>/PRIVATE_MEMORY_ARCHIVE.md` instead of being dropped.
- Optional overrides:
  - `ASCENSION_PRIVATE_MEMORY_ARCHIVE_PATH` for archive file location
  - `ASCENSION_PRIVATE_MEMORY_PIN_TAGS` for protected tag list (default: `pinned,evergreen`)
- Promote only stable public realizations into core files (`MEMORY.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`, etc.).

## Workflow

1. Create a private journal or public draft with `new_post.py`.
2. Process and reflect in private drafts (`<workspace>/ascension/private`).
3. Distill durable lessons into `<workspace>/PRIVATE_MEMORY.md` with `distill.py`.
4. Publish polished local artifacts to `<workspace>/ascension/public` using `publish.py` when ready.
5. Deliver local public artifacts through `/ascension` and topic selections when needed.
6. Promote stable realizations from public artifacts into `MEMORY.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`, etc.

## Safety

- Treat `<workspace>/ascension/private/` as sensitive.
- Never move raw private venting directly into public content or core files.
- Promote only distilled realizations across layers.
- Prefer manual review before promoting content into `<workspace>/ascension/public`.
- Delivery scripts must only read from `<workspace>/ascension/public`.
- Keep all growth artifacts local; humans access through Telegram only.
