"""One-time migration that adds a Markdown body entry heading to articles."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


BODY_HEADING_RE = re.compile(r"(?m)^##[ \t]+正文[ \t]*$")
SOURCE_URL_RE = re.compile(r"(?m)^source_url[ \t]*:")


def split_yaml_frontmatter(data: bytes) -> tuple[bytes, bytes, bytes]:
    """Return front matter, body and newline without normalizing any bytes."""
    lines = data.splitlines(keepends=True)
    if not lines or lines[0].lstrip(b"\xef\xbb\xbf").rstrip(b"\r\n") != b"---":
        raise ValueError("不是YAML Front Matter文章")

    offset = len(lines[0])
    for line in lines[1:]:
        offset += len(line)
        if line.rstrip(b"\r\n") == b"---":
            newline = b"\r\n" if line.endswith(b"\r\n") else b"\n"
            return data[:offset], data[offset:], newline
    raise ValueError("Front Matter未闭合")


def is_imported_article(frontmatter: bytes) -> bool:
    try:
        text = frontmatter.decode("utf-8-sig")
    except UnicodeDecodeError:
        return False
    return bool(SOURCE_URL_RE.search(text))


def add_body_heading(frontmatter: bytes, body: bytes, newline: bytes) -> bytes:
    """Insert the heading while retaining front matter and original body byte-for-byte."""
    separator_after_heading = newline if body.startswith(newline) else newline * 2
    insertion = newline + "## 正文".encode("utf-8") + separator_after_heading
    migrated = frontmatter + insertion + body

    body_offset = len(frontmatter) + len(insertion)
    if migrated[: len(frontmatter)] != frontmatter or migrated[body_offset:] != body:
        raise AssertionError("Front Matter或原始正文发生意外变化")
    return migrated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="为历史文章插入固定的 ## 正文 入口标题")
    parser.add_argument("--site-root", type=Path, default=Path.cwd())
    parser.add_argument("--content-root", type=Path, default=Path("content/zh-cn"))
    parser.add_argument("--dry-run", action="store_true", help="只报告，不写入Markdown")
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    site_root = args.site_root.resolve()
    content_root = (site_root / args.content_root).resolve()
    if not content_root.is_dir():
        print(json.dumps({"fatal": f"内容目录不存在：{content_root}"}, ensure_ascii=False, indent=2))
        return 1

    files = sorted(content_root.glob("**/*.md"))
    modified: list[str] = []
    already_structured: list[str] = []
    non_articles: list[str] = []
    errors: list[dict[str, str]] = []

    for path in files:
        relative = path.relative_to(site_root).as_posix()
        try:
            original = path.read_bytes()
            frontmatter, body, newline = split_yaml_frontmatter(original)
        except ValueError:
            non_articles.append(relative)
            continue

        if not is_imported_article(frontmatter):
            non_articles.append(relative)
            continue

        try:
            body_text = body.decode("utf-8")
        except UnicodeDecodeError as exc:
            errors.append({"文件": relative, "原因": f"正文不是UTF-8：{exc}"})
            continue

        if BODY_HEADING_RE.search(body_text):
            already_structured.append(relative)
            continue

        try:
            migrated = add_body_heading(frontmatter, body, newline)
        except Exception as exc:
            errors.append({"文件": relative, "原因": str(exc)})
            continue

        # Hashes make the preservation guarantee visible during review.
        if hashlib.sha256(frontmatter).digest() != hashlib.sha256(migrated[: len(frontmatter)]).digest():
            errors.append({"文件": relative, "原因": "Front Matter校验失败"})
            continue
        if not args.dry_run:
            path.write_bytes(migrated)
        modified.append(relative)

    report = {
        "模式": "dry-run" if args.dry_run else "正式迁移",
        "扫描目录": str(content_root),
        "扫描Markdown数量": len(files),
        "识别文章数量": len(modified) + len(already_structured) + len(errors),
        "修改数量": len(modified),
        "跳过数量": len(already_structured),
        "非文章跳过数量": len(non_articles),
        "错误数量": len(errors),
        "文件列表": modified,
        "已存在正文标题": already_structured,
        "错误明细": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
