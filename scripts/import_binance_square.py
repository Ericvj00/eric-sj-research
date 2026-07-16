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

SUBSECTION_CATEGORY_LABELS = {
    "sector": "板块研究",
    "thesis": "逻辑拆解",
    "company": "个股研究",
    "earnings": "财报分析",
}

DEFAULT_CATEGORY_ROUTE = ("articles", "", "未分类")

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
    STRONG_OPEN = "\ue000"
    STRONG_CLOSE = "\ue001"

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.current = None
        self.links = []
        self.images = []
        self.strong_depth = 0
        self.list_stack = []

    def render_inline(self, parts):
        text = "".join(parts)
        strong_pattern = re.compile(
            re.escape(self.STRONG_OPEN) + r"(.*?)" + re.escape(self.STRONG_CLOSE),
            flags=re.S,
        )

        def replace_strong(match):
            content = match.group(1).strip()
            return f"**{content}**" if content else ""

        while strong_pattern.search(text):
            text = strong_pattern.sub(replace_strong, text)
        return text.replace(self.STRONG_OPEN, "").replace(self.STRONG_CLOSE, "")

    def finish(self):
        if not self.current:
            return
        text = re.sub(r"[ \t]+", " ", self.render_inline(self.current[1])).strip()
        if text:
            self.blocks.append((self.current[0], text))
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"ul", "ol"}:
            start = numeric_attr(attrs.get("start", "")) if tag == "ol" else 0
            self.list_stack.append({"tag": tag, "counter": max(start - 1, 0)})
        elif tag == "li":
            self.finish()
            if self.list_stack and self.list_stack[-1]["tag"] == "ol":
                self.list_stack[-1]["counter"] += 1
                self.current = [f"ol-li:{self.list_stack[-1]['counter']}", []]
            else:
                self.current = ["li", []]
        elif tag in self.BLOCKS:
            self.finish()
            self.current = [tag, []]
        elif tag == "br" and self.current:
            self.current[1].append("\n")
        elif tag == "a" and self.current:
            self.links.append(attrs.get("href", ""))
            self.current[1].append("[")
        elif tag in {"strong", "b"} and self.current:
            self.current[1].append(self.STRONG_OPEN)
            self.strong_depth += 1
        elif tag == "img":
            self.finish()
            src = attrs.get("src", "")
            if src.startswith("data:image/"):
                self.images.append((src, attrs.get("data-src", "")))
                self.blocks.append(("img", str(len(self.images) - 1)))

    def handle_endtag(self, tag):
        if tag == "li":
            self.finish()
        elif tag in {"ul", "ol"}:
            if self.list_stack:
                self.list_stack.pop()
        elif tag in self.BLOCKS:
            self.finish()
        elif tag == "a" and self.current and self.links:
            href = self.links.pop()
            self.current[1].append(f"]({href})" if href else "]")
        elif tag in {"strong", "b"} and self.current and self.strong_depth:
            self.current[1].append(self.STRONG_CLOSE)
            self.strong_depth -= 1

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


def data_image_extension(data_uri):
    match = re.match(r"data:image/([a-zA-Z0-9.+-]+)", data_uri)
    if not match:
        return ".png"
    extension = match.group(1).lower().replace("jpeg", "jpg")
    return f".{extension}"


def data_image_bytes(data_uri):
    header, encoded = data_uri.split(",", 1)
    if ";base64" not in header:
        return b""
    return base64.b64decode(encoded)


def image_dimensions(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data.startswith(b"\xff\xd8"):
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            index += 2
            if marker in {0xD8, 0xD9}:
                continue
            if index + 2 > len(data):
                break
            size = int.from_bytes(data[index:index + 2], "big")
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF} and index + 7 <= len(data):
                return int.from_bytes(data[index + 5:index + 7], "big"), int.from_bytes(data[index + 3:index + 5], "big")
            index += max(size, 2)
    return 0, 0


def img_attrs(tag):
    attrs = {}
    pattern = r"([:\w-]+)(?:\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+))?"
    for key, value in re.findall(pattern, tag):
        value = value or ""
        if len(value) >= 2 and value[0] in {"'", '"'} and value[-1] == value[0]:
            value = value[1:-1]
        attrs[key.lower()] = html_module.unescape(value)
    return attrs


def is_noise_image(attrs, src):
    marker = " ".join([attrs.get("alt", ""), attrs.get("class", ""), attrs.get("aria-label", ""), src[:120]]).lower()
    if src.startswith("data:image/svg"):
        return True
    return any(word in marker for word in (
        "avatar",
        "logo",
        "binance square",
        "language",
        "icon",
        "certified",
        "switch",
        "profile",
        "emoji",
    ))


def numeric_attr(value):
    match = re.search(r"\d+", value or "")
    return int(match.group(0)) if match else 0


def find_top_cover_candidate(html, title, article_start):
    title_pos = html.find(title) if title else -1
    if title_pos < 0:
        title_pos = 0
    start = title_pos + (len(title) if title else 0)
    if article_start <= start:
        return None
    segment = html[start:article_start]
    for match in re.finditer(r"<img\b[^>]*>", segment, flags=re.I):
        attrs = img_attrs(match.group(0))
        src = attrs.get("src") or attrs.get("data-src") or ""
        if not src or is_noise_image(attrs, src):
            continue
        width = numeric_attr(attrs.get("width", ""))
        height = numeric_attr(attrs.get("height", ""))
        if src.startswith("data:image/"):
            data = data_image_bytes(src)
            detected_width, detected_height = image_dimensions(data)
            width = detected_width or width
            height = detected_height or height
        elif not src.startswith(("http://", "https://")):
            continue

        if not width or not height:
            continue
        ratio = width / height
        if width < 480 or height < 180:
            continue
        if ratio < 1.25:
            continue
        return {"src": src}
    return None


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
            image_url = image_urls[int(value)]
            if image_url:
                output.append(f"![文章配图]({image_url})")
        elif kind in {"h1", "h2", "h3", "h4"}:
            level = max(2, int(kind[1]))
            output.append(f"{'#' * level} {value}")
        elif kind == "li":
            output.append(f"- {value}")
        elif kind.startswith("ol-li:"):
            output.append(f"{kind.split(':', 1)[1]}. {value}")
        elif kind == "blockquote":
            output.append(f"> {value}")
        else:
            output.append(value)
    markdown = "\n\n".join(output)
    return strip_binance_links(markdown)


def strip_binance_links(markdown):
    markdown = re.sub(
        r"\[([^\]]+)\]\(https?://[^\s)]*binance\.com[^\s)]*\)",
        r"\1",
        markdown,
        flags=re.I,
    )
    return re.sub(r"https?://[^\s)]*binance\.com[^\s)]*", "", markdown, flags=re.I)


def clean_generated_text(value):
    value = strip_binance_links(value or "")
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def standard_article_body(summary, key_points, body_markdown):
    cleaned_summary = clean_generated_text(summary)
    cleaned_points = [clean_generated_text(point) for point in key_points if clean_generated_text(point)]
    cleaned_body = strip_binance_links(body_markdown).strip()
    lines = [
        "## 文章摘要",
        "",
        cleaned_summary,
        "",
        "## 核心观点",
        "",
    ]
    lines.extend(f"- {point}" for point in cleaned_points[:5])
    lines.extend([
        "",
        "## 正文",
        "",
        cleaned_body,
    ])
    return "\n".join(lines).strip()


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


def generated_summary_from_signals(title, blocks, category="", tags=None):
    tags = tags or []
    haystack = clean_text("\n".join([title, category, " ".join(tags), *blocks])).lower()
    title_text = clean_text(title)
    title_haystack = title_text.lower()

    if any(word in title_haystack for word in ["nike", "nke", "直营", "直營", "分销", "分銷"]):
        return "Nike正由直营扩张转向渠道再平衡，收入结构、分销效率与品牌溢价将共同决定复苏空间。"

    if any(word in title_haystack for word in ["美光", "micron", "$mu", "mu"]):
        return "美光正由传统周期存储股转向AI算力资产，收入弹性、利润率修复与HBM需求构成重估主线。"

    if any(word in title_haystack for word in ["spacex", "马斯克", "火箭", "星链"]):
        return "SpaceX估值分歧持续放大，商业模式兑现、现金流潜力与马斯克信仰溢价决定其定价边界。"

    if any(word in title_haystack for word in ["coinbase", "base"]):
        return "Base的核心优势并非单纯技术领先，Coinbase入口、分发效率与生态转化才是护城河关键。"

    if any(word in title_haystack for word in ["perp dex", "perp", "永续", "衍生品"]):
        return "Perp DEX竞争已进入新阶段，流动性深度、交易体验与费用结构正在重塑下一代交易所格局。"

    if any(word in title_haystack for word in ["rwa", "real world asset"]):
        return "RWA正从概念叙事迈向真实采用，资产上链、稳定币需求与可持续收益共同驱动新增长周期。"

    if any(word in title_haystack for word in ["solana"]):
        return "Solana生态进入新一轮重估窗口，资金流向、应用落地与风险偏好变化正在筛选率先定价的资产。"

    if any(word in title_haystack for word in ["web3", "稳定币", "穩定幣", "商业模式", "商業模式", "现金流", "現金流"]):
        return "Web3收入模型正在接受现金流检验，交易费、稳定币与基础设施收入决定商业模式的质量和壁垒。"

    keywords = [tag for tag in tags if tag not in {"Web3", "美股"}][:3]
    focus = "、".join(keywords) if keywords else title_text
    return f"{focus}正处于关键变化阶段，商业模式、竞争格局与市场预期将共同决定其长期价值和发展空间。"


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


def route_from_existing_content(site, date_prefix, slug):
    filename = f"{date_prefix}-{slug}.md"
    content_root = site / "content/zh-cn"
    for path in content_root.glob(f"**/{filename}"):
        subsection = path.parent.name
        section = path.parent.parent.name
        if subsection in SUBSECTION_CATEGORY_LABELS and section in {"web3", "stocks"}:
            return section, subsection, SUBSECTION_CATEGORY_LABELS[subsection]
    return DEFAULT_CATEGORY_ROUTE


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

    article_html = find_article_html(html)
    article_start = html.find("class=richtext-container")
    cover_candidate = find_top_cover_candidate(html, title, article_start)

    parser = ArticleParser()
    parser.feed(article_html)
    parser.finish()
    slug = slugify(title)
    site = site_root.resolve()
    section, subsection, category = route_from_existing_content(site, date_prefix, slug)
    blocks = plain_blocks(parser)
    joined_text = "\n".join(blocks)
    tags = keywords_from_text(title, joined_text)
    if section == "web3" and "Web3" not in tags:
        tags.insert(0, "Web3")
    if section == "stocks" and "美股" not in tags:
        tags.insert(0, "美股")
    summary = generated_summary_from_signals(title, blocks, category, tags)
    meta_description = meta_description_from_blocks(blocks)
    key_points = key_points_from_blocks(blocks)
    seo_keywords = tags[:10]
    faqs = faq_from_content(title, category, tags, summary)
    summary = clean_generated_text(summary)
    meta_description = clean_generated_text(meta_description)
    key_points = [clean_generated_text(point) for point in key_points if clean_generated_text(point)]
    faqs = [(clean_generated_text(question), clean_generated_text(answer)) for question, answer in faqs]

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

    cover_data_uri = cover_candidate["src"] if cover_candidate and cover_candidate["src"].startswith("data:image/") else ""
    image_urls = [None] * len(parser.images)
    saved_body_images = []
    body_image_count = 0
    for original_index, (data_uri, _) in enumerate(parser.images):
        if cover_data_uri and data_uri == cover_data_uri:
            continue
        body_image_count += 1
        extension = data_image_extension(data_uri).lstrip(".")
        filename = f"{date_prefix}-{slug}-image-{body_image_count:02d}.{extension}"
        destination = posts_dir / filename
        if not dry_run:
            save_data_image(data_uri, destination)
            mirror_to_static(destination, static_posts_dir)
        saved_body_images.append(destination)
        image_urls[original_index] = f"/images/posts/{filename}"

    cover_path = ""
    if cover_candidate:
        cover_src = cover_candidate["src"]
        extension = data_image_extension(cover_src) if cover_src.startswith("data:image/") else Path(urlparse(cover_src).path).suffix or ".png"
        filename = f"{date_prefix}-{slug}-cover{extension}"
        destination = covers_dir / filename
        if not dry_run:
            if cover_src.startswith("data:image/"):
                save_data_image(cover_src, destination)
            elif not destination.exists():
                download_file(cover_src, destination)
            mirror_to_static(destination, static_covers_dir)
        cover_path = f"/images/covers/{filename}"
    elif cover_url:
        extension = Path(urlparse(cover_url).path).suffix or ".png"
        filename = f"{date_prefix}-{slug}-cover{extension}"
        destination = covers_dir / filename
        if not dry_run:
            if not destination.exists():
                download_file(cover_url, destination)
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
        f"description: {yaml_string(meta_description)}",
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
        standard_article_body(summary, key_points, render_markdown(parser, image_urls)),
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
        body_images=body_image_count,
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
