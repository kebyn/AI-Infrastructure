import tempfile
import unittest
from pathlib import Path

import serve_docs


class RenderDocLayoutTest(unittest.TestCase):
    def test_render_doc_moves_generated_toc_into_sidebar(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            src = tmp_path / "sample.md"
            dst = tmp_path / "sample.html"
            src.write_text(
                "\n".join(
                    [
                        "# Sample",
                        "",
                        "---",
                        "",
                        "## 目录",
                        "",
                        "- [自动生成目录占位](#自动生成目录占位)",
                        "",
                        "---",
                        "",
                        "## 第一章",
                        "",
                        "正文",
                        "",
                        "### 子节",
                        "",
                        "更多正文",
                        "",
                        "## 第二章",
                        "",
                        "结尾",
                    ]
                ),
                encoding="utf-8",
            )

            serve_docs.render_doc(
                {
                    "src": str(src),
                    "dst": str(dst),
                    "title": "测试文档",
                    "hero": "测试文档",
                    "subtitle": "测试副标题",
                    "meta": "测试元信息",
                    "footer": "测试页脚",
                }
            )

            html = dst.read_text(encoding="utf-8")

        self.assertIn('<div class="doc-shell">', html)
        self.assertIn('<aside class="doc-sidebar" aria-label="文档目录">', html)
        self.assertIn('<main class="doc-container">', html)
        self.assertNotIn('<h2 id="目录">目录</h2>', html)
        self.assertRegex(html, r'<a class="toc-chapter" href="#第一章">第一章</a>')
        self.assertRegex(html, r'<a href="#子节">子节</a>')
        self.assertRegex(html, r'<h2 id="第一章">第一章</h2>')
        self.assertRegex(html, r'<h3 id="子节">子节</h3>')
        self.assertNotIn("<hr />\n\n<hr />", html)


if __name__ == "__main__":
    unittest.main()
