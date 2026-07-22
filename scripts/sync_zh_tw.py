"""Safely synchronize published Simplified Chinese articles to Traditional Chinese.

The command writes new files by default. Pass ``--dry-run`` to preview changes.
Existing Traditional Chinese files are never changed unless ``--overwrite`` is
also set. No source file is modified or deleted.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable


ARTICLE_DIRECTORIES = (
    Path("web3/sector"),
    Path("web3/onchain-financials"),
    Path("web3/projects"),
    Path("web3/thesis"),
    Path("stocks/earnings"),
    Path("stocks/company"),
    Path("stocks/industry"),
)

CONVERTED_FRONT_MATTER_FIELDS = {
    "title",
    "description",
    "summary",
    "categories",
    "tags",
    "keywords",
    # The current site uses this SEO-specific alias in imported articles.
    "seo_keywords",
    # Site-specific structured prose shown on article pages or emitted as JSON-LD.
    "meta_description",
    "key_points",
    "faq",
    "category_label",
    "subcategory",
    "disclaimer",
    "updated_note",
}

PRESERVED_FRONT_MATTER_FIELDS = {
    "date",
    "lastmod",
    "draft",
    "featured",
    "cover",
    "slug",
    "aliases",
    "author",
    "layout",
    "weight",
}

EXCLUDED_FILENAMES = {"_index.md", "template.md", "example.md"}
EXCLUDED_TEST_TITLES = {
    "Hyperliquid商业模式分析：一个链上交易所如何捕获现金流",
    "从USDT到USDC：稳定币真正的商业模式是什么",
    "Web3已经验证的五种商业模式",
}
TOOL_TABLES = {"recommended_tools", "research_tools"}
TOP_LEVEL_FIELD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*[:=]")
TABLE_RE = re.compile(r"^\s*\[\[([^]]+)]]\s*(?:#.*)?$")
FENCE_RE = re.compile(
    r"(?ms)^(?P<fence>`{3,}|~{3,})[^\r\n]*(?:\r?\n).*?^(?P=fence)[ \t]*(?:\r?\n|$)"
)
INLINE_CODE_RE = re.compile(r"(`+)([^\r\n]*?)\1")
REFERENCE_URL_RE = re.compile(r"(?m)^(\s*\[[^]]+]:\s*)(\S+)")
HTML_URL_RE = re.compile(
    r"(?i)\b(?:href|src|srcset|poster)\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)"
)
AUTOLINK_RE = re.compile(r"<(?:(?:https?|mailto):[^>]+)>", re.I)
BARE_URL_RE = re.compile(r"(?i)(?:https?://|mailto:)[^\s<>\"']+")


class SyncError(RuntimeError):
    """Raised for a user-facing synchronization validation error."""


@dataclass
class MarkdownDocument:
    marker: str
    front_matter: str
    body: str
    bom: bool = False

    def render(self) -> str:
        prefix = "\ufeff" if self.bom else ""
        return f"{prefix}{self.marker}\n{self.front_matter}{self.marker}\n{self.body}"


@dataclass
class SyncReport:
    mode: str
    source_root: str
    target_root: str
    scanned_count: int = 0
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped_existing: list[str] = field(default_factory=list)
    skipped_draft: list[str] = field(default_factory=list)
    skipped_excluded: list[str] = field(default_factory=list)
    excluded_test_articles: list[dict[str, str]] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    guide_action: str = "not-requested"

    def as_dict(self) -> dict:
        return {
            "mode": self.mode,
            "source_root": self.source_root,
            "target_root": self.target_root,
            "scanned_count": self.scanned_count,
            "created_count": len(self.created),
            "updated_count": len(self.updated),
            "skipped_existing_count": len(self.skipped_existing),
            "skipped_draft_count": len(self.skipped_draft),
            "skipped_excluded_count": len(self.skipped_excluded),
            "excluded_test_article_count": len(self.excluded_test_articles),
            "error_count": len(self.errors),
            "guide_action": self.guide_action,
            "created": self.created,
            "updated": self.updated,
            "skipped_existing": self.skipped_existing,
            "skipped_draft": self.skipped_draft,
            "skipped_excluded": self.skipped_excluded,
            "excluded_test_articles": self.excluded_test_articles,
            "test_article_notice": (
                "检测到残留测试文章；已排除同步。是否删除请人工确认，脚本不会删除。"
                if self.excluded_test_articles
                else "未检测到指定测试文章。"
            ),
            "errors": self.errors,
        }


class Protector:
    """Replace protected substrings with OpenCC-safe ASCII placeholders."""

    def __init__(self, text: str):
        self.text = text
        self.values: list[str] = []
        self.prefix = "__SYNC_ZHTW_PROTECTED_"
        if self.prefix in text:
            raise SyncError("内容包含内部保护标记，无法安全转换")

    def stash(self, value: str) -> str:
        token = f"{self.prefix}{len(self.values):06d}__"
        self.values.append(value)
        return token

    def apply_regex(self, pattern: re.Pattern[str]) -> None:
        self.text = pattern.sub(lambda match: self.stash(match.group(0)), self.text)

    def protect_markdown_destinations(self) -> None:
        """Protect balanced ``](destination)`` segments, including image links."""
        source = self.text
        output: list[str] = []
        cursor = 0
        while cursor < len(source):
            start = source.find("](", cursor)
            if start < 0:
                output.append(source[cursor:])
                break
            output.append(source[cursor : start + 1])
            index = start + 1
            depth = 0
            escaped = False
            end = -1
            while index < len(source):
                char = source[index]
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        end = index + 1
                        break
                index += 1
            if end < 0:
                output.append(source[start + 1 :])
                break
            output.append(self.stash(source[start + 1 : end]))
            cursor = end
        self.text = "".join(output)

    def restore(self, text: str) -> str:
        for index, value in reversed(list(enumerate(self.values))):
            text = text.replace(f"{self.prefix}{index:06d}__", value)
        return text


def protected_convert(text: str, convert: Callable[[str], str]) -> str:
    """Convert prose while preserving code and every URL/path destination."""
    protector = Protector(text)
    protector.apply_regex(FENCE_RE)
    protector.apply_regex(INLINE_CODE_RE)
    protector.protect_markdown_destinations()
    protector.apply_regex(REFERENCE_URL_RE)
    protector.apply_regex(HTML_URL_RE)
    protector.apply_regex(AUTOLINK_RE)
    protector.apply_regex(BARE_URL_RE)
    return protector.restore(convert(protector.text))


def protected_fragments(text: str) -> list[str]:
    """Return code and URL fragments in the exact order used by conversion."""
    protector = Protector(text)
    protector.apply_regex(FENCE_RE)
    protector.apply_regex(INLINE_CODE_RE)
    protector.protect_markdown_destinations()
    protector.apply_regex(REFERENCE_URL_RE)
    protector.apply_regex(HTML_URL_RE)
    protector.apply_regex(AUTOLINK_RE)
    protector.apply_regex(BARE_URL_RE)
    return protector.values


def parse_markdown(text: str) -> MarkdownDocument:
    bom = text.startswith("\ufeff")
    if bom:
        text = text[1:]
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() not in {"---", "+++"}:
        raise SyncError("Markdown 缺少受支持的 Front Matter（--- 或 +++）")
    marker = lines[0].strip()
    closing = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == marker),
        None,
    )
    if closing is None:
        raise SyncError("Front Matter 未闭合")
    return MarkdownDocument(
        marker=marker,
        front_matter="".join(lines[1:closing]),
        body="".join(lines[closing + 1 :]),
        bom=bom,
    )


def convert_front_matter(front_matter: str, convert: Callable[[str], str]) -> str:
    """Convert only approved top-level Front Matter fields without reformatting."""
    lines = front_matter.splitlines(keepends=True)
    result: list[str] = []
    index = 0
    while index < len(lines):
        match = TOP_LEVEL_FIELD_RE.match(lines[index])
        if not match or match.group(1) not in CONVERTED_FRONT_MATTER_FIELDS:
            result.append(lines[index])
            index += 1
            continue
        end = index + 1
        while end < len(lines) and not TOP_LEVEL_FIELD_RE.match(lines[end]):
            end += 1
        result.append(protected_convert("".join(lines[index:end]), convert))
        index = end
    return "".join(result)


def front_matter_field_blocks(front_matter: str) -> dict[str, str]:
    """Extract raw top-level field blocks for preservation validation."""
    lines = front_matter.splitlines(keepends=True)
    blocks: dict[str, str] = {}
    index = 0
    while index < len(lines):
        match = TOP_LEVEL_FIELD_RE.match(lines[index])
        if not match:
            index += 1
            continue
        end = index + 1
        while end < len(lines) and not TOP_LEVEL_FIELD_RE.match(lines[end]):
            end += 1
        blocks[match.group(1)] = "".join(lines[index:end])
        index = end
    return blocks


def is_draft(front_matter: str) -> bool:
    match = re.search(r"(?mi)^draft\s*[:=]\s*(true|false)\b", front_matter)
    return bool(match and match.group(1).lower() == "true")


def front_matter_title(front_matter: str) -> str:
    match = re.search(
        r'(?mi)^title\s*[:=]\s*(?:"([^"\r\n]*)"|\'([^\'\r\n]*)\'|([^\r\n#]+))',
        front_matter,
    )
    if not match:
        return ""
    return next((value.strip() for value in match.groups() if value is not None), "")


def convert_document(text: str, convert: Callable[[str], str]) -> str:
    document = parse_markdown(text)
    document.front_matter = convert_front_matter(document.front_matter, convert)
    document.body = protected_convert(document.body, convert)
    rendered = document.render()
    validate_conversion(text, rendered)
    return rendered


def validate_conversion(source_text: str, target_text: str) -> None:
    """Fail before writing if a technical field, URL, path, or code changed."""
    source = parse_markdown(source_text)
    target = parse_markdown(target_text)
    if source.marker != target.marker:
        raise SyncError("Front Matter 格式标记发生变化")
    source_blocks = front_matter_field_blocks(source.front_matter)
    target_blocks = front_matter_field_blocks(target.front_matter)
    for field_name in PRESERVED_FRONT_MATTER_FIELDS:
        if source_blocks.get(field_name) != target_blocks.get(field_name):
            raise SyncError(f"保留字段发生变化：{field_name}")
    if protected_fragments(source.body) != protected_fragments(target.body):
        raise SyncError("正文中的代码、链接 URL 或图片路径发生变化")


def split_tool_tables(front_matter: str) -> tuple[str, str]:
    """Return front matter without tool arrays and the extracted tool array text."""
    lines = front_matter.splitlines(keepends=True)
    kept: list[str] = []
    extracted: list[str] = []
    active_target = False
    for line in lines:
        match = TABLE_RE.match(line)
        if match:
            active_target = match.group(1) in TOOL_TABLES
        (extracted if active_target else kept).append(line)
    return "".join(kept).rstrip() + "\n", "".join(extracted).strip()


def merge_guide_data(
    source_text: str, target_text: str, convert: Callable[[str], str]
) -> str:
    source = parse_markdown(source_text)
    target = parse_markdown(target_text)
    if source.marker != "+++" or target.marker != "+++":
        raise SyncError("工具页数据合并目前要求 TOML Front Matter（+++）")
    _, source_tools = split_tool_tables(source.front_matter)
    target_skeleton, _ = split_tool_tables(target.front_matter)
    if not source_tools:
        raise SyncError("简体工具页没有 recommended_tools 或 research_tools 数据")
    converted_tools = protected_convert(source_tools, convert)
    target.front_matter = f"{target_skeleton.rstrip()}\n\n{converted_tools}\n"
    return target.render()


def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SyncError(f"文件不是 UTF-8：{path}") from exc


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="", dir=path.parent, delete=False
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def load_converter() -> Callable[[str], str]:
    try:
        from opencc import OpenCC
    except ImportError as exc:
        raise SyncError(
            "缺少 OpenCC。请运行：python -m pip install -r requirements.txt"
        ) from exc
    converter = OpenCC("s2tw")
    return converter.convert


def resolve_roots(args: argparse.Namespace) -> tuple[Path, Path]:
    site_root = args.site_root.resolve()
    source_root = (site_root / args.source_root).resolve()
    target_root = (site_root / args.target_root).resolve()
    if not source_root.is_dir():
        raise SyncError(f"简体内容目录不存在：{source_root}")
    if source_root == target_root:
        raise SyncError("源目录和目标目录不能相同")
    return source_root, target_root


def discover_articles(source_root: Path) -> Iterable[Path]:
    for relative_directory in ARTICLE_DIRECTORIES:
        directory = source_root / relative_directory
        if not directory.is_dir():
            continue
        yield from sorted(directory.glob("*.md"))


def path_selected(path: Path, source_root: Path, requested: set[str]) -> bool:
    if not requested:
        return True
    relative = path.relative_to(source_root).as_posix()
    return relative in requested or path.name in requested or path.stem in requested


def synchronize(args: argparse.Namespace) -> SyncReport:
    source_root, target_root = resolve_roots(args)
    convert = load_converter()
    report = SyncReport(
        mode="dry-run" if args.dry_run else "sync",
        source_root=str(source_root),
        target_root=str(target_root),
    )
    requested = {
        value.strip().replace("\\", "/")
        for value in (args.paths or "").split(",")
        if value.strip()
    }

    for source_path in discover_articles(source_root):
        relative = source_path.relative_to(source_root)
        relative_string = relative.as_posix()
        if not path_selected(source_path, source_root, requested):
            continue
        report.scanned_count += 1
        if source_path.name in EXCLUDED_FILENAMES:
            report.skipped_excluded.append(relative_string)
            continue
        try:
            source_text = read_utf8(source_path)
            source_document = parse_markdown(source_text)
            title = front_matter_title(source_document.front_matter)
            if title in EXCLUDED_TEST_TITLES:
                report.excluded_test_articles.append(
                    {"path": relative_string, "title": title}
                )
                continue
            if is_draft(source_document.front_matter) and not args.include_drafts:
                report.skipped_draft.append(relative_string)
                continue
            target_path = target_root / relative
            exists = target_path.exists()
            if exists and not args.overwrite:
                report.skipped_existing.append(relative_string)
                continue
            converted = convert_document(source_text, convert)
            (report.updated if exists else report.created).append(relative_string)
            if not args.dry_run:
                atomic_write(target_path, converted)
        except Exception as exc:  # Continue processing other articles.
            report.errors.append({"path": relative_string, "error": str(exc)})

    if args.sync_guides:
        source_guide = source_root / "guides/_index.md"
        target_guide = target_root / "guides/_index.md"
        try:
            if not source_guide.is_file() or not target_guide.is_file():
                raise SyncError("简体或繁体 guides/_index.md 不存在")
            merged = merge_guide_data(
                read_utf8(source_guide), read_utf8(target_guide), convert
            )
            report.guide_action = "would-update" if args.dry_run else "update"
            if not args.dry_run:
                atomic_write(target_guide, merged)
        except Exception as exc:
            report.guide_action = "error"
            report.errors.append({"path": "guides/_index.md", "error": str(exc)})

    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将正式简体文章安全同步为台湾繁体 Markdown"
    )
    parser.add_argument("--site-root", type=Path, default=Path.cwd())
    parser.add_argument("--source-root", type=Path, default=Path("content/zh-cn"))
    parser.add_argument("--target-root", type=Path, default=Path("content/zh-tw"))
    parser.add_argument("--dry-run", action="store_true", help="只显示同步计划，不写文件")
    parser.add_argument(
        "--overwrite", action="store_true", help="允许覆盖已存在的繁体文章"
    )
    parser.add_argument(
        "--include-drafts", action="store_true", help="同时同步 draft=true 的文件"
    )
    parser.add_argument(
        "--sync-guides",
        action="store_true",
        help="合并简体工具数据，同时保留繁体 guides 页面骨架",
    )
    parser.add_argument(
        "--paths", help="只处理相对路径、文件名或 stem；多个值用逗号分隔"
    )
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        report = synchronize(parse_args())
    except Exception as exc:
        print(json.dumps({"fatal": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    return 0 if not report.errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
