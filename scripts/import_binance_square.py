"""Import SingleFile-saved Binance Square posts into the Hugo site.

The importer can process explicit HTML files or every HTML file in a directory.
It always uses the original article time found inside the HTML for front matter
`date`; filesystem timestamps and the current date are never used for sorting.
"""

import argparse
import base64
import html as html_module
import json
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


CATEGORY_ROUTES = {
    "板块研究": ("web3", "sector"),
    "链上财报": ("web3", "onchain-financials"),
    "项目分析": ("web3", "projects"),
    "逻辑拆解": ("web3", "thesis"),
    "财报分析": ("stocks", "earnings"),
    "个股研究": ("stocks", "company"),
    "产业报告": ("stocks", "industry"),
    "未分类": ("articles", ""),
}

STOPWORDS = {
    "一个",
    "不是",
    "以及",
    "已经",
    "真正",
    "可能",
    "什么",
    "这个",
    "这些",
    "如果",
    "因为",
    "所以",
    "通过",
    "我们",
    "https",
    "http",
    "www",
    "binance",
    "com",
    "square",
    "post",
    "zh",
    "cn",
    "en",
    "stocks",
    "web3",
    "eq",
    "futures",
    "trade",
}

TOPIC_KEYWORDS = [
    "Web3",
    "Base",
    "Coinbase",
    "Perp DEX",
    "RWA",
    "Solana",
    "Hyperliquid",
    "Tether",
    "USDT",
    "USDC",
    "Ethena",
    "Aave",
    "Ethereum",
    "稳定币",
    "交易所",
    "商业模式",
    "现金流",
    "收入",
    "护城河",
    "分发",
    "入口垄断",
    "生态资产",
    "估值",
    "Nike",
    "NIKE",
    "美光",
    "Micron",
    "MU",
    "SpaceX",
    "英伟达",
    "分销",
    "直营",
]


class ArticleParser(HTMLParser):
    BLOCKS = {"p", "h1", "h2", "h3", "h4", "li", "blockquote"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.current = None
        self.links = []
        self.images = []

    def finish(self):
        if not self.current:
            return
        text = re.sub(r"[ \t]+", " ", "".join(self.current[1])).strip()
        if text:
            self.blocks.append((self.current[0], text))
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in self.BLOCKS:
            self.finish()
            self.current = [tag, []]
        elif tag == "br" and self.current:
            self.current[1].append("\n")
        elif tag == "a" and self.current:
            self.links.append(attrs.get("href", ""))
            self.current[1].append("[")
        elif tag == "img":
            self.finish()
            src = attrs.get("src", "")
            if src.startswith("data:image/"):
                self.images.append((src, attrs.get("data-src", "")))
                self.blocks.append(("img", str(len(self.images) - 1)))

    def handle_endtag(self, tag):
        if tag in self.BLOCKS:
            self.finish()
        elif tag == "a" and self.current and self.links:
            href = self.links.pop()
            self.current[1].append(f"]({href})" if href else "]")

    def handle_data(self, data):
        if self.current:
            self.current[1].append(data)


class MetadataParser(HTMLParser):
    def __init__(self, key):
        super().__init__()
        self.key = key
        self.value = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and (attrs.get("property") == self.key or attrs.get("name") == self.key):
            self.value = attrs.get("content", "")


@dataclass
class ImportResult:
    source_file: str
    article: str = ""
    published_at: str = ""
    category: str = ""
    tags: list[str] | None = None
    cover: str = ""
    body_images: int = 0
    status: str = "ok"
    error: str = ""


def meta(html, key):
    head_end = html.find("</head>")
    parser = MetadataParser(key)
    parser.feed(html[: head_end + 7 if head_end >= 0 else min(len(html), 100000)])
    return html_module.unescape(parser.value)


def published_at(html):
    for pattern in (
        r'"datePublished"\s*:\s*"([^"]+)',
        r'"publishedTime"\s*:\s*"([^"]+)',
        r'<time[^>]+datetime=["\']([^"\']+)',
    ):
        match = re.search(pattern, html, flags=re.I)
        if not match:
            continue
        parsed = datetime.fromisoformat(match.group(1).replace("Z", "+00:00"))
        return parsed.astimezone(ZoneInfo("Asia/Shanghai"))
    return None


def save_data_image(data_uri, path):
    header, encoded = data_uri.split(",", 1)
    if ";base64" not in header:
        raise ValueError("Only base64 SingleFile images are supported")
    path.write_bytes(base64.b64decode(encoded))


def yaml_string(value):
    return json.dumps(value or "", ensure_ascii=False)


def clean_text(value):
    value = html_module.unescape(value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def plain_blocks(parser):
    return [clean_text(value) for kind, value in parser.blocks if kind != "img" and clean_text(value)]


def render_markdown(parser, image_urls):
    output = []
    for kind, value in parser.blocks:
        if kind == "img":
            output.append(f"![文章配图]({image_urls[int(value)]})")
        elif kind in {"h1", "h2", "h3", "h4"}:
            level = max(2, int(kind[1]))
            output.append(f"{'#' * level} {value}")
        elif kind == "li":
            output.append(f"- {value}")
        elif kind == "blockquote":
            output.append(f"> {value}")
        else:
            output.append(value)
    markdown = "\n\n".join(output)
    return strip_binance_links(markdown)


def strip_binance_links(markdown):
    return re.sub(
        r"\[([^\]]+)\]\(https?://[^\s)]*binance\.com[^\s)]*\)",
        r"\1",
        markdown,
        flags=re.I,
    )


def slugify(title):
    title_lower = title.lower()
    overrides = [
        ("coinbase", "coinbase-distribution-base-entry-monopoly"),
        ("perp dex", "perp-dex-next-exchange-war"),
        ("rwa", "rwa-narrative-growth-cycle"),
        ("solana", "solana-new-cycle-ecosystem-assets"),
        ("spacex", "spacex-valuation-debate"),
        ("nike", "nike-direct-to-consumer-retreat-distribution"),
        ("美光", "micron-mu-changed"),
        ("micron", "micron-mu-changed"),
        ("交易费", "web3-revenue-drivers-moats"),
        ("稳定币", "web3-revenue-drivers-moats"),
        ("hyperliquid", "web3-verified-cash-flow-models"),
    ]
    for needle, slug in overrides:
        if needle in title_lower or needle in title:
            return slug

    normalized = unicodedata.normalize("NFKD", title)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug[:80].strip("-") or "binance-square-post"


def keywords_from_text(title, text):
    keywords = []
    haystack = f"{title}\n{text}"
    for word in TOPIC_KEYWORDS:
        if word.lower() in haystack.lower() and word not in keywords:
            keywords.append(word)
    for token in re.findall(r"[\u4e00-\u9fffA-Za-z0-9$]{2,24}", haystack):
        token = token.strip("$")
        if token.lower() in STOPWORDS or token.lower().startswith("http"):
            continue
        if token and token not in STOPWORDS and token not in keywords:
            keywords.append(token)
        if len(keywords) >= 10:
            break
    return keywords[:10]


def classify_article(title, text):
    title_lower = title.lower()
    haystack = f"{title}\n{text}".lower()

    if any(word in title_lower for word in ["coinbase", "base", "商业模式", "护城河", "入口垄断", "分发权"]):
        return "逻辑拆解"
    if any(word in title_lower for word in ["perp dex", "rwa", "solana", "赛道", "周期", "生态资产"]):
        return "板块研究"
    if any(word in title_lower for word in ["交易费", "稳定币", "收入驱动力", "现金流表", "链上财报"]):
        return "链上财报"

    if any(word in haystack for word in ["nike", "美光", "micron", "$mu", "spacex", "英伟达"]):
        if any(word in title_lower for word in ["财报", "earnings"]) or (
            "美光" in title and any(word in haystack for word in ["财报", "q1", "q2", "q3", "q4", "eps", "营收", "利润"])
        ):
            return "财报分析"
        return "个股研究"

    if any(word in haystack for word in ["链上财报", "现金流表", "协议收入", "费用收入", "收入驱动"]):
        return "链上财报"
    if any(word in haystack for word in ["rwa", "perp dex", "solana", "赛道", "生态", "周期"]):
        return "板块研究"
    if any(word in haystack for word in ["base", "coinbase", "项目", "估值", "代币", "生态资产"]):
        return "项目分析"
    if any(word in haystack for word in ["商业模式", "护城河", "逻辑", "入口垄断", "分发权"]):
        return "逻辑拆解"
    return "未分类"


def meta_description_from_blocks(blocks):
    text = clean_text("".join(block for block in blocks if len(block) > 12))
    if not text:
        return ""
    return text[:160]


def summary_from_blocks(title, blocks):
    candidates = [block for block in blocks if 20 <= len(block) <= 180]
    if candidates:
        return candidates[0].rstrip("。") + "。"
    return f"{title} 的核心观点与数据归档。"


def key_points_from_blocks(blocks):
    candidates = []
    for block in blocks:
        if len(block) < 18:
            continue
        if any(marker in block for marker in ["：", "?", "？", "核心", "第一", "第二", "第三", "收入", "增长", "估值", "护城河"]):
            candidates.append(block)
        if len(candidates) >= 5:
            break
    if len(candidates) < 3:
        candidates.extend(block for block in blocks if len(block) >= 24 and block not in candidates)
    return [point[:180] for point in candidates[:5]]


def faq_from_content(title, category, tags, summary):
    main_tag = next((tag for tag in tags if tag not in {"Web3", "美股"}), title)
    faq = [
        (f"{title} 的核心结论是什么？", summary),
        (f"为什么说 {main_tag} 值得关注？", f"文章从收入、增长、分发或护城河等角度分析 {main_tag} 的长期价值与主要变量。"),
    ]
    if category in {"板块研究", "产业报告"}:
        faq.append((f"{main_tag} 所在赛道的关键变化是什么？", "关键变化主要来自需求结构、竞争格局、商业模式和资金关注度的重新定价。"))
    elif category in {"逻辑拆解", "项目分析"}:
        faq.append((f"{main_tag} 的护城河主要来自哪里？", "护城河通常来自入口、流动性、用户习惯、协议收入、品牌信任或生态网络效应。"))
    elif category in {"财报分析", "个股研究"}:
        faq.append((f"这篇文章关注哪些投资变量？", "文章主要关注营收、利润、渠道结构、估值预期和未来增长弹性的变化。"))
    return faq[:4]


def find_article_html(html):
    start = html.find("class=richtext-container")
    end = html.find('class="bottom-component-group', start)
    if start < 0:
        raise ValueError("Could not locate Binance rich-text article container")
    if end < 0:
        end = html.find('class="comment', start)
    if end < 0:
        end = len(html)
    return html[start:end]


def download_file(url, destination):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=8) as response:
        destination.write_bytes(response.read())


def mirror_to_static(source, static_dir):
    static_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, static_dir / source.name)


def import_one(html_file, site_root, import_date, dry_run=False):
    html = html_file.read_text(encoding="utf-8")
    title = clean_text(meta(html, "og:title") or re.sub(r"\s*\|.*$", "", meta(html, "twitter:title")))
    if not title:
        title = html_file.stem.split(" ｜ ")[0]
    source_url = meta(html, "og:url")
    cover_url = meta(html, "og:image")
    published = published_at(html)
    date_text = published.isoformat(timespec="seconds") if published else ""
    date_prefix = published.date().isoformat() if published else "undated"

    parser = ArticleParser()
    parser.feed(find_article_html(html))
    parser.finish()
    blocks = plain_blocks(parser)
    joined_text = "\n".join(blocks)
    category = classify_article(title, joined_text)
    section, subsection = CATEGORY_ROUTES[category]
    slug = slugify(title)
    tags = keywords_from_text(title, joined_text)
    if section == "web3" and "Web3" not in tags:
        tags.insert(0, "Web3")
    if section == "stocks" and "美股" not in tags:
        tags.insert(0, "美股")
    summary = summary_from_blocks(title, blocks)
    meta_description = meta_description_from_blocks(blocks)
    key_points = key_points_from_blocks(blocks)
    seo_keywords = tags[:10]
    faqs = faq_from_content(title, category, tags, summary)

    site = site_root.resolve()
    posts_dir = site / "assets/images/posts"
    covers_dir = site / "assets/images/covers"
    static_posts_dir = site / "static/images/posts"
    static_covers_dir = site / "static/images/covers"
    content_dir = site / "content/zh-cn" / section
    if subsection:
        content_dir /= subsection
    if not dry_run:
        posts_dir.mkdir(parents=True, exist_ok=True)
        covers_dir.mkdir(parents=True, exist_ok=True)
        content_dir.mkdir(parents=True, exist_ok=True)

    image_urls = []
    saved_body_images = []
    for index, (data_uri, _) in enumerate(parser.images, 1):
        extension = re.match(r"data:image/([a-zA-Z0-9.+-]+)", data_uri).group(1).replace("jpeg", "jpg")
        filename = f"{date_prefix}-{slug}-image-{index:02d}.{extension}"
        destination = posts_dir / filename
        if not dry_run:
            save_data_image(data_uri, destination)
            mirror_to_static(destination, static_posts_dir)
        saved_body_images.append(destination)
        image_urls.append(f"/images/posts/{filename}")

    cover_path = ""
    if cover_url:
        extension = Path(urlparse(cover_url).path).suffix or ".png"
        filename = f"{date_prefix}-{slug}-cover{extension}"
        destination = covers_dir / filename
        if not dry_run:
            try:
                if not destination.exists():
                    download_file(cover_url, destination)
                mirror_to_static(destination, static_covers_dir)
            except Exception:
                if saved_body_images:
                    shutil.copy2(saved_body_images[0], destination)
                    mirror_to_static(destination, static_covers_dir)
                else:
                    raise
        cover_path = f"/images/covers/{filename}"
    elif saved_body_images:
        extension = saved_body_images[0].suffix
        filename = f"{date_prefix}-{slug}-cover{extension}"
        destination = covers_dir / filename
        if not dry_run:
            shutil.copy2(saved_body_images[0], destination)
            mirror_to_static(destination, static_covers_dir)
        cover_path = f"/images/covers/{filename}"

    lines = [
        "---",
        f"title: {yaml_string(title)}",
        f"date: {yaml_string(date_text)}",
        f"importDate: {yaml_string(import_date)}",
        f"updated: {yaml_string(import_date)}",
        f"category: {yaml_string(category)}",
        "categories:",
        f"  - {yaml_string(category)}",
        "tags:",
        *[f"  - {yaml_string(tag)}" for tag in tags],
        f"cover: {yaml_string(cover_path)}",
        'source: "Binance Square"',
        f"source_url: {yaml_string(source_url)}",
        f"meta_description: {yaml_string(meta_description)}",
        f"summary: {yaml_string(summary)}",
        "key_points:",
        *[f"  - {yaml_string(point)}" for point in key_points],
        "seo_keywords:",
        *[f"  - {yaml_string(word)}" for word in seo_keywords],
        "faq:",
    ]
    for question, answer in faqs:
        lines += [f"  - question: {yaml_string(question)}", f"    answer: {yaml_string(answer)}"]
    lines += [
        "---",
        "",
        render_markdown(parser, image_urls),
        "",
        "---",
        "",
        "更多 Crypto、Web3 与美股研究更新，欢迎关注我的 X：",
        "",
        "@sjbtc9",
        "",
        "[前往 X 主页](https://x.com/sjbtc9)",
        "",
        "---",
        "",
    ]

    article_path = content_dir / f"{date_prefix}-{slug}.md"
    if not dry_run:
        article_path.write_text("\n".join(lines), encoding="utf-8")

    return ImportResult(
        source_file=str(html_file),
        article=str(article_path),
        published_at=date_text,
        category=category,
        tags=tags,
        cover=cover_path,
        body_images=len(parser.images),
    )


def collect_html_files(inputs, manifests=None, limit=None):
    files = []
    for manifest in manifests or []:
        manifest_path = Path(manifest)
        for line in manifest_path.read_text(encoding="utf-8-sig").splitlines():
            item = line.strip()
            if item and not item.startswith("#"):
                files.append(Path(item))
    for item in inputs:
        path = Path(item)
        if path.is_dir():
            files.extend(sorted(path.glob("*.html")))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(path)
    deduped = []
    seen = set()
    for file in files:
        resolved = file.resolve()
        if resolved not in seen:
            deduped.append(file)
            seen.add(resolved)
    return deduped[:limit] if limit else deduped


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="*", help="HTML files or directories containing HTML files")
    parser.add_argument("--manifest", action="append", default=[], help="UTF-8 text file with one HTML path per line")
    parser.add_argument("--site-root", type=Path, default=Path.cwd())
    parser.add_argument("--import-date", default=datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat())
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N collected HTML files")
    parser.add_argument("--dry-run", action="store_true", help="Parse and classify without writing files")
    return parser.parse_args()


def main():
    args = parse_args()
    html_files = collect_html_files(args.inputs, args.manifest, args.limit)
    results = []
    failed = 0
    for html_file in html_files:
        try:
            result = import_one(html_file, args.site_root, args.import_date, args.dry_run)
        except Exception as exc:
            failed += 1
            result = ImportResult(source_file=str(html_file), status="failed", error=str(exc))
            print(f"[failed] {html_file}: {exc}", file=sys.stderr)
        results.append(result.__dict__)

    print(json.dumps({"processed": len(results), "failed": failed, "results": results}, ensure_ascii=False, indent=2))
    return 1 if failed and failed == len(results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
