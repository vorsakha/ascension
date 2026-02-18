#!/usr/bin/env python3
"""Deterministic Telegram delivery for Ascension public content."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_FALLBACK = SKILL_ROOT.parents[1]

ALLOWED_EXTENSIONS = {"md"}
TOPIC_LABELS = {
    "ascension_journal": "Journal",
    "music_log": "Music",
    "ascension_x": "Scroll",
}
TOPIC_ALIASES = {
    "journal": "ascension_journal",
    "ascension_journal": "ascension_journal",
    "music": "music_log",
    "music_log": "music_log",
    "scroll": "ascension_x",
    "ascension_x": "ascension_x",
    "x": "ascension_x",
}


@dataclass
class ContentItem:
    path: Path
    rel_path: Path
    title: str
    topic: str
    ext: str
    mtime_utc: dt.datetime


def resolve_repo_root() -> Path:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(SKILL_ROOT), "rev-parse", "--show-toplevel"],
            text=True,
        ).strip()
        if out:
            return Path(out).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return WORKSPACE_FALLBACK.resolve()


def humanize(text: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[_\-\s]+", text.strip()) if part)


def strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_item(path: Path, root: Path) -> ContentItem | None:
    rel_path = path.relative_to(root)
    parts = path.name.split(".")
    if len(parts) < 3:
        return None

    title_raw = ".".join(parts[:-2])
    topic = parts[-2].strip().lower()
    ext = parts[-1].strip().lower()

    if not title_raw or not topic or ext not in ALLOWED_EXTENSIONS:
        return None

    stat = path.stat()
    return ContentItem(
        path=path,
        rel_path=rel_path,
        title=humanize(title_raw),
        topic=topic,
        ext=ext,
        mtime_utc=dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc),
    )


def collect_items(root: Path) -> list[ContentItem]:
    if not root.exists():
        return []

    items: list[ContentItem] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        item = parse_item(path, root)
        if item:
            items.append(item)

    items.sort(key=lambda i: (i.mtime_utc, i.path.name), reverse=True)
    return items


def topic_count(items: list[ContentItem]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item.topic] = counts.get(item.topic, 0) + 1
    return counts


def latest_for_topic(items: list[ContentItem], topic: str) -> ContentItem | None:
    for item in items:
        if item.topic == topic:
            return item
    return None


def read_excerpt(path: Path, max_chars: int = 420) -> str:
    body = path.read_text(encoding="utf-8")
    plain = strip_markdown(body)
    if len(plain) <= max_chars:
        return plain
    return plain[: max_chars - 1].rstrip() + "…"


def menu_payload(items: list[ContentItem]) -> dict[str, Any]:
    counts = topic_count(items)
    lines = ["Ascension topics"]
    keyboard: list[list[dict[str, str]]] = []

    for topic, label in TOPIC_LABELS.items():
        count = counts.get(topic, 0)
        latest = latest_for_topic(items, topic)
        latest_label = latest.mtime_utc.date().isoformat() if latest else "none"
        lines.append(f"- {label}: {count} posts (latest {latest_label})")
        keyboard.append(
            [
                {
                    "text": f"{label} ({count})",
                    "callback_data": f"ascension:topic:{topic}",
                }
            ]
        )

    return {
        "text": "\n".join(lines),
        "reply_markup": {"inline_keyboard": keyboard},
    }


def content_payload(items: list[ContentItem], topic: str) -> dict[str, Any]:
    label = TOPIC_LABELS.get(topic, humanize(topic))
    item = latest_for_topic(items, topic)
    if not item:
        return {
            "text": f"No public {label.lower()} content available yet.",
            "reply_markup": {"inline_keyboard": [[{"text": "Back", "callback_data": "ascension:menu"}]]},
        }

    excerpt = read_excerpt(item.path)
    stamp = item.mtime_utc.strftime("%Y-%m-%d %H:%M UTC")
    text = (
        f"Ascension {label}\\n"
        f"Title: {item.title}\\n"
        f"Updated: {stamp}\\n"
        f"Path: content/public/{item.rel_path.as_posix()}\\n\\n"
        f"{excerpt}"
    )

    return {
        "text": text,
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "Back", "callback_data": "ascension:menu"}],
            ]
        },
    }


def print_payload(payload: dict[str, Any], output_format: str) -> int:
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    print(payload.get("text", ""))
    markup = payload.get("reply_markup", {})
    inline_keyboard = markup.get("inline_keyboard", [])
    if inline_keyboard:
        print("\nButtons:")
        for row in inline_keyboard:
            for button in row:
                print(f"- {button['text']} => {button['callback_data']}")
    return 0


def resolve_callback_topic(data: str) -> str | None:
    data = data.strip()
    if data == "ascension:menu":
        return "__menu__"

    prefix = "ascension:topic:"
    if not data.startswith(prefix):
        return None
    maybe_topic = data[len(prefix) :].strip().lower()
    return TOPIC_ALIASES.get(maybe_topic, maybe_topic)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ascension Telegram deterministic content delivery")
    subparsers = parser.add_subparsers(dest="command", required=True)

    menu_parser = subparsers.add_parser("menu", help="Return topic menu payload")
    menu_parser.add_argument("--content-root", help="Override content/public root path")
    menu_parser.add_argument("--format", choices=["text", "json"], default="text")

    latest_parser = subparsers.add_parser("latest", help="Return latest payload for a topic")
    latest_parser.add_argument("--topic", required=True, help="Topic alias or canonical topic")
    latest_parser.add_argument("--content-root", help="Override content/public root path")
    latest_parser.add_argument("--format", choices=["text", "json"], default="text")

    callback_parser = subparsers.add_parser("callback", help="Resolve Telegram callback data")
    callback_parser.add_argument("--data", required=True, help="Callback payload string")
    callback_parser.add_argument("--content-root", help="Override content/public root path")
    callback_parser.add_argument("--format", choices=["text", "json"], default="text")

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    repo_root = resolve_repo_root()
    content_root = Path(args.content_root).resolve() if args.content_root else (repo_root / "content" / "public")

    items = collect_items(content_root)

    if args.command == "menu":
        return print_payload(menu_payload(items), args.format)

    if args.command == "latest":
        topic = TOPIC_ALIASES.get(args.topic.strip().lower(), args.topic.strip().lower())
        return print_payload(content_payload(items, topic), args.format)

    if args.command == "callback":
        resolved = resolve_callback_topic(args.data)
        if resolved is None:
            return print_payload({"text": "Unknown callback action."}, args.format)
        if resolved == "__menu__":
            return print_payload(menu_payload(items), args.format)
        return print_payload(content_payload(items, resolved), args.format)

    raise SystemExit(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
