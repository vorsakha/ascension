#!/usr/bin/env python3
"""Create new Ascension growth post files from templates."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_FALLBACK = SKILL_ROOT.parents[1]
TEMPLATES_DIR = SKILL_ROOT / "templates"


def resolve_workspace_root() -> Path:
    for candidate in (SKILL_ROOT, *SKILL_ROOT.parents):
        if (candidate / "content").exists():
            return candidate.resolve()
    return WORKSPACE_FALLBACK.resolve()


CONTENT_DIR = resolve_workspace_root() / "content"

PUBLIC_TYPES = {"journal", "music_log", "twitter_scroll"}
PRIVATE_TYPES = {"journal"}


def slugify(text: str, max_len: int = 48) -> str:
    value = text.strip().lower()
    value = re.sub(r"[^a-z0-9\s_-]", "", value)
    value = re.sub(r"[\s-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        value = "entry"
    return value[:max_len].rstrip("_") or "entry"


def parse_date(raw: str | None) -> dt.date:
    if not raw:
        return dt.date.today()
    try:
        return dt.date.fromisoformat(raw)
    except ValueError as exc:
        raise SystemExit(f"Invalid --date '{raw}'. Expected YYYY-MM-DD.") from exc


def resolve_template(visibility: str, post_type: str) -> Path:
    template_map = {
        ("private", "journal"): "journal.private.md",
        ("public", "journal"): "journal.public.md",
        ("public", "music_log"): "music_log.md",
        ("public", "twitter_scroll"): "twitter_scroll.md",
    }
    key = (visibility, post_type)
    if key not in template_map:
        raise SystemExit(f"Unsupported combination: visibility={visibility}, type={post_type}")
    path = TEMPLATES_DIR / template_map[key]
    if not path.exists():
        raise SystemExit(f"Template not found: {path}")
    return path


def build_filename(visibility: str, post_type: str, date: dt.date, title: str) -> tuple[str, str]:
    date_text = date.isoformat()
    slug = slugify(title)

    if visibility == "private" and post_type == "journal":
        basename = f"journal_{date_text}_{slug}"
        topic = "private_journal"
    elif visibility == "public" and post_type == "journal":
        basename = f"ascension_journal_{date_text}_{slug}"
        topic = "ascension_journal"
    elif visibility == "public" and post_type == "music_log":
        basename = f"daily_music_log_{date_text}_{slug}"
        topic = "music_log"
    elif visibility == "public" and post_type == "twitter_scroll":
        basename = f"ascension_x_scroll_{date_text}_{slug}"
        topic = "ascension_x"
    else:
        raise SystemExit(f"Unsupported combination: visibility={visibility}, type={post_type}")

    return f"{basename}.{topic}.md", slug


def render_template(template_path: Path, date: dt.date, title: str) -> str:
    content = template_path.read_text(encoding="utf-8")
    content = content.replace("YYYY-MM-DD", date.isoformat())
    content = content.replace("{{AGENT_NAME}}", "Ascension")
    content = content.replace("[Topic Name]", title.strip() or "General")
    content = content.replace("[Month DD, YYYY]", date.strftime("%B %d, %Y"))
    content = content.replace("[HH:MM UTC]", dt.datetime.now(dt.timezone.utc).strftime("%H:%M UTC"))
    return content


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a new post from templates.")
    parser.add_argument("visibility", choices=["public", "private"], help="Post visibility")
    parser.add_argument("type", help="Post type, e.g. journal/music_log/twitter_scroll")
    parser.add_argument("title", help="Human title used to build slug/content")
    parser.add_argument("--date", help="Override date in YYYY-MM-DD format")
    parser.add_argument("--force", action="store_true", help="Overwrite destination if it exists")
    parser.add_argument("--dry-run", action="store_true", help="Print result without writing")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    post_type = args.type.strip().lower()

    if args.visibility == "public" and post_type not in PUBLIC_TYPES:
        allowed = ", ".join(sorted(PUBLIC_TYPES))
        raise SystemExit(f"Invalid type '{post_type}' for public. Allowed: {allowed}")

    if args.visibility == "private" and post_type not in PRIVATE_TYPES:
        allowed = ", ".join(sorted(PRIVATE_TYPES))
        raise SystemExit(f"Invalid type '{post_type}' for private. Allowed: {allowed}")

    date = parse_date(args.date)
    template = resolve_template(args.visibility, post_type)
    filename, _ = build_filename(args.visibility, post_type, date, args.title)

    target_dir = CONTENT_DIR / args.visibility
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename

    if target.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing file: {target}. Use --force to overwrite.")

    body = render_template(template, date, args.title)

    if args.dry_run:
        print(f"[dry-run] Would create: {target}")
        return 0

    target.write_text(body, encoding="utf-8")
    print(f"Created: {target}")
    print("Next: review and polish content before local delivery.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
