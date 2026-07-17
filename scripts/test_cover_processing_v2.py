import io
import unittest
from unittest.mock import patch

from PIL import Image

import sync_content as sync


def image_bytes(size, color=(30, 90, 180), image_format="PNG"):
    output = io.BytesIO()
    Image.new("RGB", size, color).save(output, format=image_format)
    return output.getvalue()


class CoverProcessingV2Tests(unittest.TestCase):
    def test_singlefile_css_variable_resolves_embedded_image(self):
        source = image_bytes((1280, 720))
        embedded = "data:image/png;base64," + sync.base64.b64encode(source).decode("ascii")
        document = (
            f"<style>:root{{--sf-img-15:url(\"{embedded}\")}}</style>"
            "<h1>测试标题</h1><div class='article-header'>"
            "<img style='background-image:var(--sf-img-15)' "
            "src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22/%3E'>"
            "</div><div class=richtext-container><p>正文</p></div>"
        )
        result = sync.select_cover(
            document,
            document.find("class=richtext-container"),
            "测试标题",
            "项目分析",
            sync.Path("test.html"),
        )
        self.assertEqual(result.source_kind, "inline-css")
        self.assertTrue(result.needs_normalization)
        self.assertEqual((result.output_width, result.output_height), (1280, 512))
        self.assertFalse(result.used_remote)

    def test_picture_srcset_embedded_resource_is_available_offline(self):
        source = image_bytes((1920, 1080))
        embedded = "data:image/jpeg;base64," + sync.base64.b64encode(source).decode("ascii")
        parser = sync.ArticleParser()
        parser.feed(
            f"<picture><source srcset='{embedded}'><img src='blob:singlefile-placeholder'></picture>"
        )
        parser.finish()
        sources = sync.attribute_image_sources(parser.images[0], {}, sync.Path("test.html"))
        self.assertEqual(sources[0][1], "picture-source-data-uri")
        data = sync.read_image_source(*sources[0], sync.Path("test.html"), allow_remote=False)
        self.assertEqual(sync.image_info(data)[:2], (1920, 1080))

    def test_contain_1280x720(self):
        result = sync.normalize_cover_contain(image_bytes((1280, 720)))
        with Image.open(io.BytesIO(result)) as image:
            self.assertEqual(image.size, (1280, 512))
            self.assertEqual(image.getpixel((0, 0)), (250, 245, 240))
            self.assertNotEqual(image.getpixel((640, 256)), (250, 245, 240))

    def test_contain_1920x1080(self):
        result = sync.normalize_cover_contain(image_bytes((1920, 1080)))
        with Image.open(io.BytesIO(result)) as image:
            self.assertEqual(image.size, (1280, 512))
            self.assertEqual(image.getpixel((100, 256)), (250, 245, 240))
            self.assertNotEqual(image.getpixel((640, 256)), (250, 245, 240))

    def test_contain_other_horizontal_ratio(self):
        result = sync.normalize_cover_contain(image_bytes((1000, 600)))
        with Image.open(io.BytesIO(result)) as image:
            self.assertEqual(image.size, (1280, 512))
            self.assertEqual(image.getpixel((100, 256)), (250, 245, 240))
            self.assertNotEqual(image.getpixel((640, 256)), (250, 245, 240))

    def test_native_five_two_is_used_without_reencoding(self):
        source = image_bytes((1280, 512))
        embedded = "data:image/png;base64," + sync.base64.b64encode(source).decode("ascii")
        document = (
            "<html><head><meta property='og:image' content='https://example.test/og.png'>"
            f"</head><body><h1>测试标题</h1><img src='{embedded}'>"
            "<div class=richtext-container><p>正文</p></div></body></html>"
        )
        article_start = document.find("class=richtext-container")
        result = sync.select_cover(
            document,
            article_start,
            "测试标题",
            "项目分析",
            sync.Path("test.html"),
        )
        self.assertEqual(result.region, "文章标题之后、正文内容之前的顶部主视觉")
        self.assertTrue(result.is_true_top_visual)
        self.assertFalse(result.needs_normalization)
        self.assertEqual(result.output_data, source)

    def test_body_first_image_is_never_a_cover_candidate(self):
        source = image_bytes((1280, 720))
        document = (
            "<html><head><meta property='og:image' content='https://example.test/og.jpg'>"
            "</head><body><h1>测试标题</h1><div class=richtext-container>"
            "<img src='https://example.test/data-chart.jpg'><p>正文</p></div></body></html>"
        )
        article_start = document.find("class=richtext-container")
        with patch.object(sync, "fetch_bytes", return_value=source):
            result = sync.select_cover(
                document,
                article_start,
                "测试标题",
                "项目分析",
                sync.Path("test.html"),
            )
        self.assertEqual(result.candidate_count, 1)
        self.assertEqual(result.source, "")
        self.assertEqual(result.region, "HTML 内无可用顶部主视觉")
        self.assertFalse(result.is_true_top_visual)
        self.assertTrue(result.is_placeholder)
        self.assertFalse(result.used_remote)
        self.assertEqual((result.output_width, result.output_height), (1280, 512))


if __name__ == "__main__":
    unittest.main()
