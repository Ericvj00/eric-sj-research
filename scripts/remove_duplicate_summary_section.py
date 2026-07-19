"""Remove duplicated Markdown summary sections from article bodies.

The article template renders the summary from Front Matter, so imported body
content should not also contain a ``## 文章摘要`` section.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SUMMARY_SECTION_RE = re.compile(
    r"(?ms)(?:\A|\n)[ \t]*##[ \t]+文章摘要[ \t]*\r?\n.*?(?=(?:\r?\n)?[ \t]*##[ \t]+|\Z)"
)


def split_yaml_frontmatter(data: bytes) -> tuple[bytes, bytes]:
    """Return front matter and body without normalizing any bytes."""
    lines = data.splitlines(keepends=True)
    if not lines or lines[0].lstrip(b"\xef\xbb\xbf").rstrip(b"\r\n") != b"---":
        raise ValueError("not a YAML Front Matter page")

    offset = len(lines[0])
    for line in lines[1:]:
        offset += len(line)
        if line.rstrip(b"\r\n") == b"---":
            return data[:offset], data[offset:]
    raise ValueError("front matter is not closed")


def is_article_page(path: Path, frontmatter: bytes) -> bool:
    if path.name.lower() == "_index.md":
        return False
    try:
        text = frontmatter.decode("utf-8-sig")
    except UnicodeDecodeError:
        return False
    return bool(re.search(r"(?m)^title[ \t]*:", text))


def remove_summary_section(body: str) -> tuple[str, int]:
    new_body, count = SUMMARY_SECTION_RE.subn(_section_replacement, body, count=1)
    return new_body, count


def _section_replacement(match: re.Match[str]) -> str:
    text = match.group(0)
    return "\n" if text.startswith("\n") else ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove body-level ## 文章摘要 sections already rendered from Front Matter."
    )
    parser.add_argument("--site-root", type=Path, default=Path.cwd())
    parser.add_argument("--content-root", type=Path, default=Path("content/zh-cn"))
    parser.add_argument("--dry-run", action="store_true", help="report only; do not write Markdown")
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    site_root = args.site_root.resolve()
    content_root = (site_root / args.content_root).resolve()
    if not content_root.is_dir():
        print(json.dumps({"fatal": f"content directory does not exist: {content_root}"}, ensure_ascii=False, indent=2))
        return 1

    scanned = 0
    article_count = 0
    changed: list[str] = []
    skipped: list[str] = []
    errors: list[dict[str, str]] = []

    for path in sorted(content_root.glob("**/*.md")):
        scanned += 1
        relative = path.relative_to(site_root).as_posix()
        try:
            original = path.read_bytes()
            frontmatter, body_bytes = split_yaml_frontmatter(original)
        except ValueError:
            skipped.append(relative)
            continue

        if not is_article_page(path, frontmatter):
            skipped.append(relative)
            continue

        article_count += 1
        try:
            body = body_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            errors.append({"file": relative, "reason": f"body is not UTF-8: {exc}"})
            continue

        new_body, count = remove_summary_section(body)
        if count == 0:
            skipped.append(relative)
            continue

        changed.append(relative)
        if not args.dry_run:
            path.write_bytes(frontmatter + new_body.encode("utf-8"))

    report = {
        "mode": "dry-run" if args.dry_run else "apply",
        "scanned_markdown_count": scanned,
        "article_page_count": article_count,
        "found_count": len(changed),
        "would_modify_count" if args.dry_run else "modified_count": len(changed),
        "error_count": len(errors),
        "files": changed,
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
