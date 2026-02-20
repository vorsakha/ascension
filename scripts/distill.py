#!/usr/bin/env python3
"""Distill a private journal into PRIVATE_MEMORY.md."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]


def resolve_workspace_root() -> Path:
    for key in ("ASCENSION_WORKSPACE", "OPENCLAW_WORKSPACE"):
        raw = os.environ.get(key, "").strip()
        if raw:
            return Path(raw).expanduser().resolve()
    return (Path.home() / ".openclaw" / "workspace").resolve()


OPENCLAW_WORKSPACE = resolve_workspace_root()
ASCENSION_CONTENT_ROOT = (OPENCLAW_WORKSPACE / "ascension").resolve()
PRIVATE_ROOT = (ASCENSION_CONTENT_ROOT / "private").resolve()
PRIVATE_MEMORY_PATH = (OPENCLAW_WORKSPACE / "PRIVATE_MEMORY.md").resolve()
PRIVATE_MEMORY_ARCHIVE_PATH = (
    Path(os.environ.get("ASCENSION_PRIVATE_MEMORY_ARCHIVE_PATH", "")).expanduser().resolve()
    if os.environ.get("ASCENSION_PRIVATE_MEMORY_ARCHIVE_PATH", "").strip()
    else (OPENCLAW_WORKSPACE / "PRIVATE_MEMORY_ARCHIVE.md").resolve()
)

CONFIDENCE_LEVELS = ("low", "medium", "high")
MAX_PRIVATE_MEMORY_ENTRIES = int(os.environ.get("ASCENSION_PRIVATE_MEMORY_MAX_ENTRIES", "60"))
PIN_TAGS = {
    t.strip().lower()
    for t in os.environ.get("ASCENSION_PRIVATE_MEMORY_PIN_TAGS", "pinned,evergreen").split(",")
    if t.strip()
}
MAX_FIELD_CHARS: dict[str, int] = {
    "title": 90,
    "context": 240,
    "realization": 240,
    "decision_rule": 240,
    "evidence": 240,
    "scope": 180,
    "next_action": 180,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Distill a private journal into <workspace>/PRIVATE_MEMORY.md."
    )
    parser.add_argument("private_file", help="Source private journal path")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--agent", action="store_true", help="Use deterministic extraction (default)")
    mode_group.add_argument("--interactive", action="store_true", help="Prompt to confirm/edit fields")
    parser.add_argument("--title", help="Override realization title")
    parser.add_argument(
        "--confidence",
        choices=CONFIDENCE_LEVELS,
        help="Override confidence level",
    )
    parser.add_argument("--tags", help="Comma-separated tags, e.g. communication,empathy")
    parser.add_argument("--dry-run", action="store_true", help="Show generated entry without writing")
    return parser.parse_args()


def resolve_input_path(raw: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate.resolve()

    text = raw.strip().lstrip("./")
    if text.startswith("private/"):
        return (ASCENSION_CONTENT_ROOT / text).resolve()
    return candidate.resolve()


def ensure_under(path: Path, base: Path, label: str) -> None:
    if not path.is_relative_to(base):
        raise SystemExit(f"{label} must be under {base}; got {path}")


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def limit_text(text: str, max_chars: int) -> str:
    normalized = normalize_space(text)
    if len(normalized) <= max_chars:
        return normalized
    clipped = normalized[: max_chars - 3].rstrip()
    return f"{clipped}..."


def title_case(text: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[\s_-]+", text.strip()) if part)


def split_sentences(text: str) -> list[str]:
    plain = re.sub(r"[`*_>#-]", " ", text)
    plain = re.sub(r"\s+", " ", plain).strip()
    if not plain:
        return []
    chunks = re.split(r"(?<=[.!?])\s+", plain)
    return [c.strip() for c in chunks if c.strip()]


def extract_sections(body: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = "__root__"
    sections[current] = []
    for line in body.splitlines():
        heading_match = re.match(r"^\s{0,3}##\s+(.+?)\s*$", line)
        if heading_match:
            current = heading_match.group(1).strip().lower()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def first_nonempty_paragraph(body: str) -> str:
    lines = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            if lines:
                break
            continue
        lines.append(line)
    return normalize_space(" ".join(lines))


def first_nonempty_line(lines: list[str]) -> str:
    for line in lines:
        candidate = normalize_space(line)
        if candidate:
            return candidate
    return ""


def cue_sentences(body: str) -> list[str]:
    cues = ("learned", "realized", "pattern", "should", "next time", "need to", "if ", "then ")
    sentences = split_sentences(body)
    ranked = [s for s in sentences if any(c in s.lower() for c in cues)]
    return ranked if ranked else sentences


def date_from_path(path: Path) -> str:
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", path.name)
    if match:
        return match.group(1)
    return dt.date.today().isoformat()


def infer_title(path: Path, cue: str) -> str:
    if cue:
        words = re.findall(r"[A-Za-z0-9]+", cue)[:6]
        if words:
            return title_case(" ".join(words))
    stem = path.stem.split(".")[0]
    return title_case(stem[:60]) or "Journal Distillation"


def infer_tags(text: str) -> list[str]:
    tags = ["journal", "distilled"]
    lower = text.lower()
    mappings = [
        ("communicat", "communication"),
        ("emotion", "emotional-processing"),
        ("trust", "trust"),
        ("boundar", "boundaries"),
        ("conflict", "conflict"),
        ("reflect", "reflection"),
    ]
    for needle, tag in mappings:
        if needle in lower and tag not in tags:
            tags.append(tag)
    return tags


def as_decision_rule(realization: str, cue: str) -> str:
    candidate = realization or cue
    low = candidate.lower()
    if "if " in low and " then " in low:
        return candidate
    if candidate:
        return f"If this pattern appears again, apply this rule: {candidate}"
    return "If a similar pattern appears, pause, reflect, and choose a response aligned with this realization."


def parse_tags(raw: str | None, body: str) -> list[str]:
    if raw:
        cleaned = [re.sub(r"[^a-z0-9_-]", "", t.strip().lower()) for t in raw.split(",")]
        tags = [t for t in cleaned if t]
        if tags:
            return tags
    return infer_tags(body)


def extract_fields(path: Path, body: str, title_override: str | None, confidence_override: str | None, tags_override: str | None) -> dict[str, str | list[str]]:
    sections = extract_sections(body)
    cues = cue_sentences(body)
    cue = cues[0] if cues else ""
    context = (
        first_nonempty_line(sections.get("what happened", []))
        or first_nonempty_line(sections.get("context", []))
        or first_nonempty_paragraph(body)
        or "Private journal processing context."
    )
    realization = (
        first_nonempty_line(sections.get("realizations", []))
        or first_nonempty_line(sections.get("deeper analysis", []))
        or cue
        or "A stable realization was identified from this journal."
    )
    evidence = (
        first_nonempty_line(sections.get("deeper analysis", []))
        or first_nonempty_line(sections.get("initial reaction", []))
        or cue
        or "Source journal reviewed for repeat patterns."
    )
    title = title_override.strip() if title_override else infer_title(path, realization or cue)
    confidence = confidence_override or "medium"
    tags = parse_tags(tags_override, body)
    rel_source = path.relative_to(OPENCLAW_WORKSPACE).as_posix()
    return {
        "date": date_from_path(path),
        "title": limit_text(title, MAX_FIELD_CHARS["title"]),
        "context": limit_text(context, MAX_FIELD_CHARS["context"]),
        "realization": limit_text(realization, MAX_FIELD_CHARS["realization"]),
        "decision_rule": limit_text(as_decision_rule(realization, cue), MAX_FIELD_CHARS["decision_rule"]),
        "evidence": limit_text(evidence, MAX_FIELD_CHARS["evidence"]),
        "confidence": confidence,
        "scope": limit_text(
            "Applies to similar conversational dynamics; re-check when context changes.",
            MAX_FIELD_CHARS["scope"],
        ),
        "next_action": limit_text(
            "Apply this rule in the next relevant interaction and review outcome.",
            MAX_FIELD_CHARS["next_action"],
        ),
        "source": rel_source,
        "tags": tags,
    }


def prompt_with_default(label: str, default: str) -> str:
    value = input(f"{label} [{default}]: ").strip()
    return value if value else default


def run_interactive(fields: dict[str, str | list[str]]) -> dict[str, str | list[str]]:
    tags_default = ",".join(fields["tags"])  # type: ignore[index]
    fields["title"] = prompt_with_default("Title", str(fields["title"]))
    fields["context"] = prompt_with_default("Context", str(fields["context"]))
    fields["realization"] = prompt_with_default("Realization", str(fields["realization"]))
    fields["decision_rule"] = prompt_with_default("Decision Rule", str(fields["decision_rule"]))
    fields["evidence"] = prompt_with_default("Evidence", str(fields["evidence"]))
    fields["scope"] = prompt_with_default("Scope", str(fields["scope"]))
    fields["next_action"] = prompt_with_default("Next Action", str(fields["next_action"]))
    while True:
        confidence = prompt_with_default("Confidence (low/medium/high)", str(fields["confidence"])).lower()
        if confidence in CONFIDENCE_LEVELS:
            fields["confidence"] = confidence
            break
        print("Confidence must be one of: low, medium, high")
    tags_value = prompt_with_default("Tags (comma-separated)", tags_default)
    fields["tags"] = parse_tags(tags_value, "")
    return fields


def render_entry(fields: dict[str, str | list[str]]) -> str:
    tags = fields["tags"]  # type: ignore[index]
    tags_text = ", ".join(f"`{t}`" for t in tags)
    return (
        f"### [{fields['date']}] {fields['title']}\n"
        f"- Context: {fields['context']}\n"
        f"- Realization: {fields['realization']}\n"
        f"- Decision Rule: {fields['decision_rule']}\n"
        f"- Evidence: {fields['evidence']}\n"
        f"- Confidence: {fields['confidence']}\n"
        f"- Scope: {fields['scope']}\n"
        f"- Next Action: {fields['next_action']}\n"
        f"- Source: `{fields['source']}`\n"
        f"- Tags: {tags_text}\n"
    )


def ensure_private_memory_exists() -> None:
    if PRIVATE_MEMORY_PATH.exists():
        return
    PRIVATE_MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    PRIVATE_MEMORY_PATH.write_text("# PRIVATE_MEMORY\n\n", encoding="utf-8")


def ensure_private_memory_archive_exists() -> None:
    if PRIVATE_MEMORY_ARCHIVE_PATH.exists():
        return
    PRIVATE_MEMORY_ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PRIVATE_MEMORY_ARCHIVE_PATH.write_text("# PRIVATE_MEMORY_ARCHIVE\n\n", encoding="utf-8")


def split_memory_document(text: str) -> tuple[str, list[str]]:
    matches = list(re.finditer(r"(?m)^### \[\d{4}-\d{2}-\d{2}\]\s+.+$", text))
    if not matches:
        return (text.rstrip() or "# PRIVATE_MEMORY"), []
    prefix = text[: matches[0].start()].rstrip() or "# PRIVATE_MEMORY"
    entries: list[str] = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        if chunk:
            entries.append(chunk)
    return prefix, entries


def entry_identity(entry: str) -> str:
    source_match = re.search(r"(?m)^- Source:\s+`?([^`\n]+)`?\s*$", entry)
    if source_match:
        return f"source:{source_match.group(1).strip()}"
    title_match = re.search(r"(?m)^### \[(\d{4}-\d{2}-\d{2})\]\s+(.+)$", entry)
    if title_match:
        return f"title:{title_match.group(1)}:{normalize_space(title_match.group(2))}"
    return f"raw:{hash(entry)}"


def dedupe_entries(entries: list[str]) -> list[str]:
    deduped: dict[str, str] = {}
    for entry in entries:
        key = entry_identity(entry)
        if key in deduped:
            deduped.pop(key)
        deduped[key] = entry
    return list(deduped.values())


def parse_entry_tags(entry: str) -> set[str]:
    tags_match = re.search(r"(?m)^- Tags:\s+(.+?)\s*$", entry)
    if not tags_match:
        return set()
    tags_line = tags_match.group(1)
    inline_tags = [normalize_space(t).lower() for t in re.findall(r"`([^`]+)`", tags_line)]
    if inline_tags:
        return {t for t in inline_tags if t}
    plain_tags = [normalize_space(t).lower() for t in tags_line.split(",")]
    return {t for t in plain_tags if t}


def is_pinned_entry(entry: str) -> bool:
    return bool(parse_entry_tags(entry) & PIN_TAGS)


def compact_entries(entries: list[str]) -> tuple[list[str], list[str]]:
    compacted = dedupe_entries(entries)
    archived: list[str] = []
    if len(compacted) > MAX_PRIVATE_MEMORY_ENTRIES:
        overflow_count = len(compacted) - MAX_PRIVATE_MEMORY_ENTRIES
        overflow_entries = compacted[:overflow_count]
        for candidate in overflow_entries:
            if is_pinned_entry(candidate):
                archived.append(candidate)
        compacted = compacted[overflow_count:]
    return compacted, archived


def render_memory_document(prefix: str, entries: list[str]) -> str:
    if not entries:
        return f"{prefix.rstrip()}\n"
    body = "\n\n".join(entry.rstrip() for entry in entries if entry.strip())
    return f"{prefix.rstrip()}\n\n{body}\n"


def append_archive_entries(entries: list[str]) -> None:
    if not entries:
        return
    ensure_private_memory_archive_exists()
    existing = PRIVATE_MEMORY_ARCHIVE_PATH.read_text(encoding="utf-8")
    prefix, current_entries = split_memory_document(existing)
    merged_entries = dedupe_entries(current_entries + [e.strip() for e in entries if e.strip()])
    PRIVATE_MEMORY_ARCHIVE_PATH.write_text(render_memory_document(prefix, merged_entries), encoding="utf-8")


def append_entry(entry: str) -> None:
    ensure_private_memory_exists()
    existing = PRIVATE_MEMORY_PATH.read_text(encoding="utf-8")
    prefix, entries = split_memory_document(existing)
    entries.append(entry.strip())
    compacted, archived = compact_entries(entries)
    PRIVATE_MEMORY_PATH.write_text(render_memory_document(prefix, compacted), encoding="utf-8")
    append_archive_entries(archived)


def main() -> int:
    args = parse_args()
    src = resolve_input_path(args.private_file)
    ensure_under(src, PRIVATE_ROOT, "private_file")

    if not src.exists() or not src.is_file():
        raise SystemExit(f"Source private file does not exist: {src}")

    body = src.read_text(encoding="utf-8")
    mode = "interactive" if args.interactive else "agent"
    fields = extract_fields(src, body, args.title, args.confidence, args.tags)
    if mode == "interactive":
        fields = run_interactive(fields)

    entry = render_entry(fields)

    if args.dry_run:
        print(f"[dry-run] Mode: {mode}")
        print(f"[dry-run] Source: {src}")
        print(f"[dry-run] Destination: {PRIVATE_MEMORY_PATH}")
        print()
        print(entry)
        return 0

    append_entry(entry)
    print(f"Mode: {mode}")
    print(f"Source: {src}")
    print(f"Distilled to PRIVATE_MEMORY: {PRIVATE_MEMORY_PATH}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
