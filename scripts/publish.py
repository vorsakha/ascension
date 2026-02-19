#!/usr/bin/env python3
"""Publish private growth content into local public content."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
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
PUBLIC_ROOT = (ASCENSION_CONTENT_ROOT / "public").resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish private content into <workspace>/ascension/public."
    )
    parser.add_argument("private_file", help="Source private file path")
    parser.add_argument("public_file", help="Destination public file path")
    parser.add_argument("--force", action="store_true", help="Overwrite destination if it exists")
    parser.add_argument("--open", action="store_true", help="Open destination file in $EDITOR after copy")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without copying")
    return parser.parse_args()


def resolve_input_path(raw: str, kind: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate.resolve()

    text = raw.strip().lstrip("./")
    if text.startswith("private/"):
        return (ASCENSION_CONTENT_ROOT / text).resolve()
    if text.startswith("public/"):
        return (ASCENSION_CONTENT_ROOT / text).resolve()
    return candidate.resolve()


def ensure_under(path: Path, base: Path, label: str) -> None:
    if not path.is_relative_to(base):
        raise SystemExit(f"{label} must be under {base}; got {path}")


def maybe_open_in_editor(path: Path) -> None:
    editor = os.environ.get("EDITOR")
    if not editor:
        print("Copied. Set $EDITOR and use --open to launch editor automatically.")
        return

    try:
        subprocess.run([editor, str(path)], check=False)
    except OSError as exc:
        print(f"Failed to launch editor '{editor}': {exc}")


def main() -> int:
    args = parse_args()

    src = resolve_input_path(args.private_file, kind="private")
    dst = resolve_input_path(args.public_file, kind="public")

    ensure_under(src, PRIVATE_ROOT, "private_file")
    ensure_under(dst, PUBLIC_ROOT, "public_file")

    if not src.exists() or not src.is_file():
        raise SystemExit(f"Source private file does not exist: {src}")

    if dst.exists() and not args.force:
        raise SystemExit(f"Destination already exists: {dst}. Use --force to overwrite.")

    if args.dry_run:
        print(f"[dry-run] Would copy '{src}' -> '{dst}'")
        print("[dry-run] Private source would be preserved.")
        return 0

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

    print(f"Published locally: {dst}")
    print(f"Private source kept: {src}")
    print("Next: polish local public language and remove sensitive details before Telegram delivery.")

    if args.open:
        maybe_open_in_editor(dst)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
