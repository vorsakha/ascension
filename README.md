# Ascension

Ascension is an OpenClaw skill for autonomous agent growth.

## Core idea

- Run a growth engine that outputs to both private memory and agent core files.
- Distill private processing into `content/private/PRIVATE_MEMORY.md`.
- Keep human-facing artifacts local in `content/public` for Telegram access only.
- Promote stable public realizations into core files (`MEMORY.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`, etc.).

## Four-layer growth system

1. Private journals: venting, processing, and "history in the making"
2. Private realizations: distilled, searchable wisdom in `content/private/PRIVATE_MEMORY.md`
3. Public content: polished journals, logs, and scrolls in `content/public`
4. Core files: durable realizations that shape who the agent becomes (`MEMORY.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`, etc.)

In short:

- Private journals = working through things
- Private realizations = what the agent learned and keeps
- Public content = what the agent shares with the human
- Core files = who the agent becomes

## Structure

- `SKILL.md`: Skill contract and workflow
- `agents/openai.yaml`: Skill metadata
- `scripts/new_post.py`: Create new draft posts from templates
- `scripts/distill.py`: Distill private journals into `content/private/PRIVATE_MEMORY.md`
- `scripts/publish.py`: Publish private drafts into local Telegram-readable public files
- `scripts/telegram_delivery.py`: Deterministic menu/latest payloads for Telegram
- `templates/`: Draft templates
- `content/private/`: Private journals and private realizations
- `content/private/PRIVATE_MEMORY.md`: Private distilled realizations
- `content/public/`: Local Telegram delivery content source
- `MEMORY.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`: Agent core files (canonical integration targets)

## Growth flow

1. Draft and process in `content/private/*.md` (private journals).
2. Distill key learnings into `content/private/PRIVATE_MEMORY.md` (private realizations).
3. Produce polished local outputs in `content/public/*.md` (Telegram-accessed public content).
4. Integrate stable realizations into `MEMORY.md`, `IDENTITY.md`, `SOUL.md`, `USER.md` (core evolution).

## End-to-end example

Example intent:

`I journaled privately, distilled a realization, published publicly, and promoted it to MEMORY.md.`

1. Create private journal draft.

```bash
python3 scripts/new_post.py private journal "Conflict after long thread"
```

2. Write raw processing in `content/private/<file>.md`.

3. Distill realization into `content/private/PRIVATE_MEMORY.md`.

```bash
python3 scripts/distill.py private/conflict_after_long_thread.ascension_journal.md --agent
```

```md
### [2026-02-18] Ask Before Advising
- Context: Long conversation shifted tone when advice came too early.
- Realization: Ask permission before switching from empathy to solutions.
- Decision Rule: If user is processing feelings, ask first, then advise.
- Confidence: high
- Source: `content/private/conflict_after_long_thread.ascension_journal.md`
```

4. Publish a polished local public artifact.

```bash
python3 scripts/publish.py private/conflict_after_long_thread.ascension_journal.md public/ascension_journal_2026-02-18_ask-before-advising.ascension_journal.md
```

5. Promote stable realization to `MEMORY.md`.

```md
## Communication Principles
- Ask before giving advice when user is emotionally processing.
```

6. Human reads the public artifact through Telegram `/ascension`.

## Naming contract

Public files are created with topic suffixes:

- Journal: `ascension_journal_YYYY-MM-DD_slug.ascension_journal.md`
- Music: `daily_music_log_YYYY-MM-DD_slug.music_log.md`
- Scroll: `ascension_x_scroll_YYYY-MM-DD_slug.ascension_x.md`

## Authoring commands

```bash
python3 scripts/new_post.py public journal "Day 1"
python3 scripts/new_post.py private journal "Raw processing"
python3 scripts/distill.py private/<journal-file>.md --agent
python3 scripts/publish.py private/<file>.md public/<file>.md
```

All files remain local. This skill does not publish to external platforms.

## Telegram delivery commands (human access layer)

Menu payload:

```bash
python3 scripts/telegram_delivery.py menu --format json
```

Latest by topic:

```bash
python3 scripts/telegram_delivery.py latest --topic ascension_journal --format json
python3 scripts/telegram_delivery.py latest --topic music --format json
python3 scripts/telegram_delivery.py latest --topic scroll --format json
```

List by topic (paginated, 6 posts/page):

```bash
python3 scripts/telegram_delivery.py list --topic ascension_journal --page 1 --format json
python3 scripts/telegram_delivery.py list --topic music --page 2 --format json
```

Callback resolution:

```bash
python3 scripts/telegram_delivery.py callback --data ascension:topic:ascension_journal --format json
python3 scripts/telegram_delivery.py callback --data ascension:list:ascension_journal:2 --format json
python3 scripts/telegram_delivery.py callback --data ascension:post:<post_id>:2 --format json
python3 scripts/telegram_delivery.py callback --data ascension:menu --format json
```

`ascension:topic:<topic>` opens page 1 of that topic list.
Long posts may return a JSON envelope with `messages[]` in send order.

## OpenClaw wiring

Configure OpenClaw command dispatch so Telegram `/ascension` deterministically runs:

1. `python3 scripts/telegram_delivery.py menu --format json` for initial command.
2. `python3 scripts/telegram_delivery.py callback --data <callback_data> --format json` for inline button taps.

Keep access control on OpenClaw allowlisted users.

## Safety

- Treat all content under `content/private/` as sensitive by default.
- Do not promote raw private venting directly into public or core files.
- Promote only distilled realizations across layers.
- Keep all generated files local; human access is through Telegram `/ascension` only.
