#!/usr/bin/env python3
"""Deterministic Telegram delivery for Ascension public content."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
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
PAGE_SIZE = 6
TELEGRAM_CHUNK_SIZE = 3900


@dataclass
class ContentItem:
    path: Path
    rel_path: Path
    title: str
    topic: str
    ext: str
    mtime_utc: dt.datetime
    post_id: str


def resolve_workspace_root() -> Path:
    for candidate in (SKILL_ROOT, *SKILL_ROOT.parents):
        if (candidate / "content").exists():
            return candidate.resolve()
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
    rel_posix = rel_path.as_posix()
    post_id = hashlib.sha1(rel_posix.encode("utf-8")).hexdigest()[:12]
    return ContentItem(
        path=path,
        rel_path=rel_path,
        title=humanize(title_raw),
        topic=topic,
        ext=ext,
        mtime_utc=dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc),
        post_id=post_id,
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


def items_for_topic(items: list[ContentItem], topic: str) -> list[ContentItem]:
    return [item for item in items if item.topic == topic]


def find_post_by_id(items: list[ContentItem], post_id: str) -> ContentItem | None:
    for item in items:
        if item.post_id == post_id:
            return item
    return None


def read_excerpt(path: Path, max_chars: int = 420) -> str:
    body = path.read_text(encoding="utf-8")
    plain = strip_markdown(body)
    if len(plain) <= max_chars:
        return plain
    return plain[: max_chars - 1].rstrip() + "…"


def read_full_content(path: Path) -> str:
    return strip_markdown(path.read_text(encoding="utf-8"))


def paginate(items: list[ContentItem], page: int, page_size: int) -> tuple[list[ContentItem], int, int]:
    if page_size <= 0:
        page_size = PAGE_SIZE
    total_pages = max(1, math.ceil(len(items) / page_size))
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], page, total_pages


def split_text_for_telegram(text: str, chunk_size: int = TELEGRAM_CHUNK_SIZE) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    rest = text
    while len(rest) > chunk_size:
        split_at = rest.rfind("\n", 0, chunk_size)
        if split_at <= 0:
            split_at = chunk_size
        chunk = rest[:split_at].rstrip()
        if not chunk:
            chunk = rest[:chunk_size]
            split_at = chunk_size
        chunks.append(chunk)
        rest = rest[split_at:].lstrip("\n")
    if rest:
        chunks.append(rest)
    return chunks


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


def topic_list_payload(
    items: list[ContentItem], topic: str, page: int = 1, page_size: int = PAGE_SIZE
) -> dict[str, Any]:
    label = TOPIC_LABELS.get(topic, humanize(topic))
    topic_items = items_for_topic(items, topic)
    if not topic_items:
        return {
            "text": f"No public {label.lower()} content available yet.",
            "reply_markup": {"inline_keyboard": [[{"text": "Back", "callback_data": "ascension:menu"}]]},
        }

    page_items, page, total_pages = paginate(topic_items, page, page_size)
    lines = [
        f"Ascension {label}",
        f"Posts: {len(topic_items)}",
        f"Page {page}/{total_pages}",
        "",
    ]
    keyboard: list[list[dict[str, str]]] = []
    for idx, item in enumerate(page_items, start=1):
        date_label = item.mtime_utc.date().isoformat()
        lines.append(f"{idx}. {date_label} - {item.title}")
        keyboard.append(
            [
                {
                    "text": f"{idx}. {item.title}",
                    "callback_data": f"ascension:post:{item.post_id}:{page}",
                }
            ]
        )

    nav_row: list[dict[str, str]] = []
    if page > 1:
        nav_row.append(
            {
                "text": "Prev",
                "callback_data": f"ascension:list:{topic}:{page - 1}",
            }
        )
    if page < total_pages:
        nav_row.append(
            {
                "text": "Next",
                "callback_data": f"ascension:list:{topic}:{page + 1}",
            }
        )
    if nav_row:
        keyboard.append(nav_row)
    keyboard.append([{"text": "Back to topics", "callback_data": "ascension:menu"}])

    return {
        "text": "\n".join(lines),
        "reply_markup": {"inline_keyboard": keyboard},
    }


def post_payload(items: list[ContentItem], post_id: str, return_page: int = 1) -> dict[str, Any]:
    item = find_post_by_id(items, post_id)
    if not item:
        return {
            "text": "Post not found.",
            "reply_markup": {"inline_keyboard": [[{"text": "Back to topics", "callback_data": "ascension:menu"}]]},
        }

    body = read_full_content(item.path)
    stamp = item.mtime_utc.strftime("%Y-%m-%d %H:%M UTC")
    text = (
        f"Title: {item.title}\n"
        f"Updated: {stamp}\n"
        f"Path: content/public/{item.rel_path.as_posix()}\n\n"
        f"{body}"
    )
    chunks = split_text_for_telegram(text)
    keyboard = {
        "inline_keyboard": [
            [{"text": "Back to list", "callback_data": f"ascension:list:{item.topic}:{max(1, return_page)}"}],
            [{"text": "Back to topics", "callback_data": "ascension:menu"}],
        ]
    }
    if len(chunks) == 1:
        return {"text": chunks[0], "reply_markup": keyboard}

    messages = [{"text": chunk} for chunk in chunks]
    messages[-1]["reply_markup"] = keyboard
    return {"messages": messages}


def latest_payload(items: list[ContentItem], topic: str) -> dict[str, Any]:
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
        f"Ascension {label}\n"
        f"Title: {item.title}\n"
        f"Updated: {stamp}\n"
        f"Path: content/public/{item.rel_path.as_posix()}\n\n"
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

    messages = payload.get("messages")
    if isinstance(messages, list):
        for index, message in enumerate(messages, start=1):
            print(f"[Message {index}]")
            print(message.get("text", ""))
            markup = message.get("reply_markup", {})
            inline_keyboard = markup.get("inline_keyboard", [])
            if inline_keyboard:
                print("\nButtons:")
                for row in inline_keyboard:
                    for button in row:
                        print(f"- {button['text']} => {button['callback_data']}")
            if index != len(messages):
                print()
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


def resolve_callback_action(data: str) -> tuple[str, Any] | None:
    data = data.strip()
    if data == "ascension:menu":
        return ("menu",)

    parts = data.split(":")
    if len(parts) < 3 or parts[0] != "ascension":
        return None

    if parts[1] == "topic" and len(parts) == 3:
        topic = TOPIC_ALIASES.get(parts[2].strip().lower(), parts[2].strip().lower())
        return ("list", topic, 1)

    if parts[1] == "list" and len(parts) == 4:
        topic = TOPIC_ALIASES.get(parts[2].strip().lower(), parts[2].strip().lower())
        try:
            page = int(parts[3].strip())
        except ValueError:
            return None
        return ("list", topic, max(1, page))

    if parts[1] == "post" and len(parts) == 4:
        post_id = parts[2].strip().lower()
        try:
            return_page = int(parts[3].strip())
        except ValueError:
            return None
        return ("post", post_id, max(1, return_page))

    return None


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

    list_parser = subparsers.add_parser("list", help="Return paginated post list for a topic")
    list_parser.add_argument("--topic", required=True, help="Topic alias or canonical topic")
    list_parser.add_argument("--page", type=int, default=1, help="1-based page number")
    list_parser.add_argument("--content-root", help="Override content/public root path")
    list_parser.add_argument("--format", choices=["text", "json"], default="text")

    callback_parser = subparsers.add_parser("callback", help="Resolve Telegram callback data")
    callback_parser.add_argument("--data", required=True, help="Callback payload string")
    callback_parser.add_argument("--content-root", help="Override content/public root path")
    callback_parser.add_argument("--format", choices=["text", "json"], default="text")

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    workspace_root = resolve_workspace_root()
    content_root = (
        Path(args.content_root).resolve()
        if args.content_root
        else (workspace_root / "content" / "public")
    )

    items = collect_items(content_root)

    if args.command == "menu":
        return print_payload(menu_payload(items), args.format)

    if args.command == "latest":
        topic = TOPIC_ALIASES.get(args.topic.strip().lower(), args.topic.strip().lower())
        return print_payload(latest_payload(items, topic), args.format)

    if args.command == "list":
        topic = TOPIC_ALIASES.get(args.topic.strip().lower(), args.topic.strip().lower())
        return print_payload(topic_list_payload(items, topic, page=max(1, args.page)), args.format)

    if args.command == "callback":
        action = resolve_callback_action(args.data)
        if action is None:
            return print_payload({"text": "Unknown callback action."}, args.format)
        if action[0] == "menu":
            return print_payload(menu_payload(items), args.format)
        if action[0] == "list":
            _, topic, page = action
            return print_payload(topic_list_payload(items, topic, page=page), args.format)
        if action[0] == "post":
            _, post_id, return_page = action
            return print_payload(post_payload(items, post_id, return_page=return_page), args.format)
        return print_payload({"text": "Unknown callback action."}, args.format)

    raise SystemExit(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
