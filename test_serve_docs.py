import re
import tempfile
import unittest
from pathlib import Path

import serve_docs


class RenderDocLayoutTest(unittest.TestCase):
    def test_lustre_3fs_doc_is_registered(self):
        docs_by_src = {Path(doc["src"]).name: doc for doc in serve_docs.DOCS}

        self.assertIn("Lustre-3FS-Deep-Dive.md", docs_by_src)

        doc = docs_by_src["Lustre-3FS-Deep-Dive.md"]
        self.assertEqual(Path(doc["dst"]).name, "Lustre-3FS-Deep-Dive.html")
        self.assertEqual(doc["href"], "/Lustre-3FS-Deep-Dive.html")
        self.assertIn("Lustre", doc["title"])
        self.assertIn("3FS", doc["title"])

    def test_kubernetes_ai_schedulers_doc_is_registered(self):
        docs_by_src = {Path(doc["src"]).name: doc for doc in serve_docs.DOCS}

        self.assertIn("Kubernetes-AI-Schedulers-Deep-Dive.md", docs_by_src)

        doc = docs_by_src["Kubernetes-AI-Schedulers-Deep-Dive.md"]
        self.assertEqual(
            Path(doc["dst"]).name,
            "Kubernetes-AI-Schedulers-Deep-Dive.html",
        )
        self.assertEqual(doc["href"], "/Kubernetes-AI-Schedulers-Deep-Dive.html")
        self.assertIn("AI 调度器", doc["title"])
        for project in ("Koordinator", "Kueue", "Grove", "KAI-Scheduler", "Volcano"):
            self.assertIn(project, doc["footer"])

    def test_render_index_includes_kubernetes_ai_schedulers_doc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_index = serve_docs.INDEX
            serve_docs.INDEX = str(Path(tmpdir) / "index.html")
            try:
                serve_docs.render_index()
                html = Path(serve_docs.INDEX).read_text(encoding="utf-8")
            finally:
                serve_docs.INDEX = original_index

        self.assertIn("Kubernetes AI 调度器深度对比", html)
        self.assertIn('/Kubernetes-AI-Schedulers-Deep-Dive.html', html)

    def test_volcano_upgrade_compatibility_doc_is_registered(self):
        docs_by_src = {Path(doc["src"]).name: doc for doc in serve_docs.DOCS}

        self.assertIn("Volcano-Upgrade-Compatibility-Deep-Dive.md", docs_by_src)

        doc = docs_by_src["Volcano-Upgrade-Compatibility-Deep-Dive.md"]
        self.assertEqual(
            Path(doc["dst"]).name,
            "Volcano-Upgrade-Compatibility-Deep-Dive.html",
        )
        self.assertEqual(doc["href"], "/Volcano-Upgrade-Compatibility-Deep-Dive.html")
        self.assertIn("Volcano", doc["title"])
        self.assertIn("Cloud Native Colocation", doc["footer"])
        self.assertIn("Queue Resource Management", doc["footer"])
        self.assertIn("Helm Charts", doc["footer"])

    def test_render_index_includes_volcano_upgrade_compatibility_doc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_index = serve_docs.INDEX
            serve_docs.INDEX = str(Path(tmpdir) / "index.html")
            try:
                serve_docs.render_index()
                html = Path(serve_docs.INDEX).read_text(encoding="utf-8")
            finally:
                serve_docs.INDEX = original_index

        self.assertIn("Volcano 升级与 Feature 兼容性", html)
        self.assertIn('/Volcano-Upgrade-Compatibility-Deep-Dive.html', html)

    def test_render_volcano_upgrade_doc_includes_toc_and_mermaid(self):
        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "Volcano-Upgrade-Compatibility-Deep-Dive.md"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            rendered_doc = dict(doc)
            rendered_doc["dst"] = str(Path(tmpdir) / "volcano-upgrade.html")
            serve_docs.render_doc(rendered_doc)
            html = Path(rendered_doc["dst"]).read_text(encoding="utf-8")

        self.assertIn('<a class="toc-chapter" href="#第一章结论与适用范围">', html)
        self.assertIn('<a href="#3-1-主版本变化矩阵">3.1 主版本变化矩阵</a>', html)
        self.assertGreaterEqual(html.count('<div class="mermaid">'), 2)
        self.assertIn("flowchart TB", html)
        self.assertIn("flowchart LR", html)
        self.assertNotIn('class="language-mermaid"', html)

    def test_render_mermaid_blocks_converts_fenced_diagram(self):
        body = (
            '<pre><code class="language-mermaid">'
            'flowchart LR\nA --&gt; B\n'
            '</code></pre>'
        )

        rendered = serve_docs.render_mermaid_blocks(body)

        self.assertEqual(rendered, '<div class="mermaid">\nflowchart LR\nA --> B\n</div>')

    def test_mermaid_blocks_do_not_use_unsupported_reverse_arrows(self):
        docs_dir = Path(__file__).resolve().parent

        for doc_path in docs_dir.glob("*-Deep-Dive.md"):
            markdown_text = doc_path.read_text(encoding="utf-8")
            diagrams = re.findall(r"```mermaid\s*\n(.*?)```", markdown_text, re.S)
            for diagram in diagrams:
                with self.subTest(document=doc_path.name):
                    self.assertNotRegex(
                        diagram,
                        r"(?<!<)<--(?!>)",
                        "Mermaid flowcharts must express reverse direction by "
                        "swapping endpoints and using '-->'; '<-->' remains valid.",
                    )

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
        self.assertIn('<button class="toc-fab" type="button"', html)
        self.assertIn('aria-controls="doc-sidebar"', html)
        self.assertIn('<div class="toc-backdrop" hidden></div>', html)
        self.assertIn('<aside id="doc-sidebar" class="doc-sidebar" aria-label="文档目录">', html)
        self.assertIn('<a class="toc-home-link" href="/">首页</a>', html)
        self.assertNotIn('class="home-fab"', html)
        self.assertIn('<main class="doc-container">', html)
        self.assertIn("function setTocOpen(open)", html)
        self.assertIn("tocButton.setAttribute('aria-expanded', String(open));", html)
        self.assertIn("tocBackdrop.hidden = !open;", html)
        self.assertNotIn('<h2 id="目录">目录</h2>', html)
        self.assertRegex(html, r'<a class="toc-chapter" href="#第一章">第一章</a>')
        self.assertRegex(html, r'<a href="#子节">子节</a>')
        self.assertRegex(html, r'<h2 id="第一章">第一章</h2>')
        self.assertRegex(html, r'<h3 id="子节">子节</h3>')
        self.assertNotIn("<hr />\n\n<hr />", html)


if __name__ == "__main__":
    unittest.main()
