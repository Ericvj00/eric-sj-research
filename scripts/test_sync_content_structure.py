import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from sync_content import (
    generate_tags,
    recover_partial_seo_geo,
    render_structured_article_body,
    synthesis_profile,
)


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


class NewArticleMetadataTests(unittest.TestCase):
    def test_tags_remain_between_three_and_six_without_seo_keywords(self):
        tags = generate_tags("财报分析", [])

        self.assertGreaterEqual(len(tags), 3)
        self.assertLessEqual(len(tags), 6)
        self.assertEqual(tags[:2], ["美股", "财报分析"])

    def test_tags_are_deduplicated_and_capped(self):
        tags = generate_tags(
            "链上财报",
            ["Web3", "链上财报", "Hyperliquid", "Lighter", "edgeX", "ApeX"],
        )

        self.assertEqual(len(tags), len(set(tags)))
        self.assertGreaterEqual(len(tags), 3)
        self.assertLessEqual(len(tags), 6)

    def test_article_specific_profile_requires_exact_title(self):
        result = synthesis_profile(
            "亚马逊下一季度资本开支展望",
            "财报分析",
            ["亚马逊和AWS出现在正文中，但研究问题与十八季增速文章不同。"],
            1,
        )

        self.assertIsNone(result)

    def test_partial_recovery_keeps_failed_status_and_recovers_keywords(self):
        result = recover_partial_seo_geo(
            ["主体业务保持增长，但材料不足以形成完整核心观点。"],
            "Example Protocol经营观察",
            "项目分析",
            "完整SEO质量校验失败",
        )

        self.assertEqual(result["_final_status"], "处理失败")
        self.assertGreaterEqual(len(result["seo_keywords"]), 5)
        self.assertLessEqual(len(result["seo_keywords"]), 8)


if __name__ == "__main__":
    unittest.main()
