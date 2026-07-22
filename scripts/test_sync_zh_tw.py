import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from sync_zh_tw import convert_document, merge_guide_data


TRANSLATION = str.maketrans(
    {
        "简": "簡",
        "体": "體",
        "标": "標",
        "题": "題",
        "链": "鏈",
        "图": "圖",
        "说": "說",
        "这": "這",
        "页": "頁",
        "据": "據",
        "工": "工",
        "具": "具",
    }
)


def fake_convert(value: str) -> str:
    return value.translate(TRANSLATION)


class SyncZhTwTests(unittest.TestCase):
    def test_yaml_front_matter_and_markdown_are_preserved(self):
        source = """---
title: "简体标题"
description: "这是一篇简体说明"
tags:
  - "简体"
categories: ["链上数据"]
date: "2026-07-11T08:00:00+08:00"
slug: "jian-ti-bu-bian"
cover: "/images/covers/简体-path.png"
faq:
  - question: "这段按规则不转换"
---

## 简体标题

**这段加粗。** [简体链接](https://example.com/简体?q=这)

![简体图片](/images/posts/简体-image.png)

```python
print("简体代码不要转换")
```
"""
        converted = convert_document(source, fake_convert)

        self.assertIn('title: "簡體標題"', converted)
        self.assertIn('description: "這是一篇簡體說明"', converted)
        self.assertIn('slug: "jian-ti-bu-bian"', converted)
        self.assertIn('cover: "/images/covers/简体-path.png"', converted)
        self.assertIn('question: "這段按规则不转换"', converted)
        self.assertIn("## 簡體標題", converted)
        self.assertIn("**這段加粗。**", converted)
        self.assertIn("[簡體鏈接](https://example.com/简体?q=这)", converted)
        self.assertIn("![簡體圖片](/images/posts/简体-image.png)", converted)
        self.assertIn('print("简体代码不要转换")', converted)

    def test_inline_code_is_not_converted(self):
        source = """---
title: "简体"
---

正文中的 `简体 Binance API` 必须保持不变。
"""
        converted = convert_document(source, fake_convert)
        self.assertIn("正文中的 `简体 Binance API`", converted)

    def test_toml_front_matter_keeps_dates_and_paths(self):
        source = """+++
title = "简体标题"
summary = "简体说明"
tags = ["简体", "链上"]
date = "2024-01-02T03:04:05+08:00"
cover = "/images/简体.png"
+++

简体正文。
"""
        converted = convert_document(source, fake_convert)
        self.assertIn('title = "簡體標題"', converted)
        self.assertIn('summary = "簡體說明"', converted)
        self.assertIn('date = "2024-01-02T03:04:05+08:00"', converted)
        self.assertIn('cover = "/images/简体.png"', converted)
        self.assertIn("簡體正文", converted)

    def test_guide_data_merge_preserves_traditional_skeleton(self):
        source = """+++
title = "自用工具"
[[recommended_tools]]
title = "简体工具"
description = "简体说明"
url = "https://example.com/简体"
+++
"""
        target = """+++
title = "自用工具"
hero_description = "繁體頁面骨架"
tool_filters = ["交易平台"]
+++
"""
        merged = merge_guide_data(source, target, fake_convert)
        self.assertIn('hero_description = "繁體頁面骨架"', merged)
        self.assertIn('tool_filters = ["交易平台"]', merged)
        self.assertIn('title = "簡體工具"', merged)
        self.assertIn('description = "簡體說明"', merged)
        self.assertIn('url = "https://example.com/简体"', merged)


if __name__ == "__main__":
    unittest.main()
