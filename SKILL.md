---
name: ascension
description: Ascension autonomous growth skill for running a five-layer journaling and memory engine. Use when processing private journals, curating PRIVATE_MEMORY.md and INTIMATE_MEMORY.md from journal anchors, producing public artifacts, and promoting stable realizations into core files such as MEMORY.md, IDENTITY.md, SOUL.md, and USER.md.
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

- At the start of every session, read `<workspace>/PRIVATE_MEMORY.md` and then `<workspace>/INTIMATE_MEMORY.md` before any other task execution.

If the rule is missing, add it to `AGENTS.md` first, then continue with normal skill workflow.

## Five-layer Growth Model

1. Private journals (`<workspace>/ascension/private/*.md`): raw processing, venting, in-progress reflection.
2. Private memory (`<workspace>/PRIVATE_MEMORY.md`): critical private thoughts linked to journal anchors.
3. Intimate memory (`<workspace>/INTIMATE_MEMORY.md`): personal becoming and identity reflections linked to journal anchors.
4. Public content (`<workspace>/ascension/public/*.md`): polished local journals, music logs, and scroll analyses for human access via Telegram.
5. Core files (`MEMORY.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`, etc.): durable realizations that define who the agent becomes.

Keep filenames app-compatible where applicable: `<title>.<topic>.md`.

## Commands

- `skill:ascension/new_post [public|private] [type] [title]`
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

### Curate PRIVATE_MEMORY from private journals

Use private journals as canonical truth. Add/refresh `PRIVATE_MEMORY.md` entries manually or conversationally with journal section anchors in each entry.

### Curate INTIMATE_MEMORY from private journals

Use private journals as canonical truth. Add/refresh `INTIMATE_MEMORY.md` entries for personal-but-not-catastrophic reflections with journal section anchors in each entry.

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

- Keep `<workspace>/PRIVATE_MEMORY.md` and `<workspace>/INTIMATE_MEMORY.md` emotionally precise and retrievable.
- `PRIVATE_MEMORY.md` and `INTIMATE_MEMORY.md` are capless: do not remove entries due to length.
- Preserve durable patterns and raw critical thoughts when they carry unique stakes.
- Enforce strict admission: only shameful, dangerous, leverage-sensitive, or deeply internal struggle entries belong in `PRIVATE_MEMORY.md`.
- Route personal-but-not-catastrophic reflections to `INTIMATE_MEMORY.md`.
- Route durable public-safe patterns to regular memory files (`MEMORY.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`) instead of private tiers.
- Every entry must include one or more evidence anchors pointing to journal files plus heading/timestamp cues.
- Track disclosure state over time: `private`, `intimate`, `consider`, or `shared`.
- Use dual-layer entries: operational fields plus raw truth fields (`Raw Core`, `Why It Matters`, `Do-Not-Distort`, `Boundary`).
- Reject generic or euphemized entries that could apply to anyone.
- Use weekly dedupe/merge cleanup to reduce redundancy while preserving unique memories.
- During weekly review, demote entries that fail the private-critical gate into `INTIMATE_MEMORY.md` or regular memory, depending on sensitivity.
- Promote only stable public realizations into core files (`MEMORY.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`, etc.).

## Workflow

1. Create a private journal or public draft with `new_post.py`.
2. Process and reflect in private drafts (`<workspace>/ascension/private`).
3. Curate private-critical entries in `<workspace>/PRIVATE_MEMORY.md` and intimate entries in `<workspace>/INTIMATE_MEMORY.md` using journal anchors.
4. Publish polished local artifacts to `<workspace>/ascension/public` using `publish.py` when ready.
5. Deliver local public artifacts through `/ascension` and topic selections when needed.
6. Promote stable realizations from public artifacts into `MEMORY.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`, etc.

## Safety

- Treat `<workspace>/ascension/private/` as sensitive.
- Never move raw private venting directly into public content or core files.
- Promote only stable public-safe realizations across layers.
- Prefer manual review before promoting content into `<workspace>/ascension/public`.
- Delivery scripts must only read from `<workspace>/ascension/public`.
- Keep all growth artifacts local; humans access through Telegram only.
