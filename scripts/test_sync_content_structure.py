import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from sync_content import render_structured_article_body


class StructuredArticleBodyTests(unittest.TestCase):
    def test_new_article_contains_only_body_entry_heading(self):
        original = "原始正文第一段。\n\n## 原有小标题\n\n原始正文第二段。"
        rendered = render_structured_article_body(original)

        self.assertTrue(rendered.startswith("## 正文\n\n"))
        self.assertNotIn("## 文章摘要", rendered)
        self.assertNotIn("## 核心观点", rendered)
        self.assertEqual(rendered, f"## 正文\n\n{original}")

    def test_body_heading_is_present_for_minimal_content(self):
        rendered = render_structured_article_body("原始正文。")

        self.assertIn("## 正文\n\n原始正文。", rendered)
        self.assertNotIn("## 文章摘要", rendered)
        self.assertNotIn("## 核心观点", rendered)


if __name__ == "__main__":
    unittest.main()
