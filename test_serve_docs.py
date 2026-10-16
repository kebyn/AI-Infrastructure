import csv
import hashlib
import json
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
from html.parser import HTMLParser
from pathlib import Path
from threading import Thread
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

import serve_docs


class DocumentGraphParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.id_tags = {}
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
            self.id_tags[attrs["id"]] = tag
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])


class DocumentMigrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parent
        cls.manifest = json.loads((cls.root / "docs_migration.json").read_text())
        cls.graph = {}
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(StringIO()):
            for doc in serve_docs.DOCS:
                target = Path(directory) / Path(doc["dst"]).name
                serve_docs.render_doc(dict(doc, dst=str(target)))
                parser = DocumentGraphParser()
                parser.feed(target.read_text())
                cls.graph[Path(doc["src"]).name] = parser

    def test_registered_document_links_and_fragments_resolve(self):
        by_page = {Path(doc["dst"]).name: Path(doc["src"]).name for doc in serve_docs.DOCS}
        for filename, parser in self.graph.items():
            self.assertEqual(len(parser.ids), len(set(parser.ids)), filename)
            for href in parser.links:
                url = urlsplit(href)
                if url.scheme or url.netloc or url.path == "/":
                    continue
                with self.subTest(document=filename, link=href):
                    self.assertFalse(url.path.endswith(".md"), href)
                    target = by_page.get(Path(url.path).name) if url.path else filename
                    self.assertIn(target, self.graph)
                    if url.fragment:
                        self.assertTrue(unquote(url.fragment) in self.graph[target].ids, href)

    def test_all_original_sections_have_a_valid_disposition(self):
        self.assertEqual(len(self.manifest["sources"]), 16)
        for old, source in self.manifest["sources"].items():
            if source["retired"]:
                self.assertFalse((self.root / old).exists())
                self.assertFalse((self.root / old.replace(".md", ".html")).exists())
            self.assertTrue(source["sections"])
            for row in source["sections"]:
                with self.subTest(source=old, heading=row["heading"]):
                    self.assertIn(row["action"], ("保留", "合并", "去重"))
                    self.assertTrue(row["reason"])
                    target = urlsplit(row["target"])
                    self.assertIn(target.path, self.graph)
                    self.assertTrue(unquote(target.fragment) in self.graph[target.path].ids, row["target"])
                    self.assertRegex(self.graph[target.path].id_tags[unquote(target.fragment)], r"^h[1-6]$")

    def test_seven_domain_documents_have_unique_pages_and_no_retired_references(self):
        self.assertEqual(len(serve_docs.DOCS), 7)
        for field in ("src", "dst", "href"):
            self.assertEqual(len({doc[field] for doc in serve_docs.DOCS}), 7)
        retired = {name for name, source in self.manifest["sources"].items() if source["retired"]}
        for path in [*self.root.glob("*.md"), self.root / "serve_docs.py", self.root / "test_serve_docs.py"]:
            text = path.read_text()
            for name in retired:
                self.assertNotIn(name, text, str(path))
                self.assertNotIn(name.replace(".md", ".html"), text, str(path))

    def test_timeline_content_is_unchanged(self):
        source = self.manifest["sources"]["model_release_timeline.md"]
        actual = hashlib.sha256((self.root / "model_release_timeline.md").read_bytes()).hexdigest()
        self.assertEqual(actual, source["content_sha256"])

    def test_readme_local_links_and_fragments_resolve(self):
        parser = DocumentGraphParser()
        body = serve_docs.markdown.markdown(
            (self.root / "README.md").read_text(), extensions=["tables", "fenced_code"]
        )
        parser.feed(body)
        for href in parser.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            name = Path(url.path).name
            self.assertTrue((self.root / name).is_file(), href)
            if url.fragment:
                self.assertTrue(unquote(url.fragment) in self.graph[name].ids, href)

    def test_migration_preserves_original_code_and_official_evidence(self):
        for old, source in self.manifest["sources"].items():
            text = (self.root / source["document"]).read_text()
            codes = re.findall(r"^(`{3,}|~{3,})[^\n]*\n(.*?)^\1\s*$", text, re.M | re.S)
            hashes = {hashlib.sha256(code.encode()).hexdigest() for _, code in codes}
            with self.subTest(source=old):
                self.assertTrue(set(source["code_blocks"]) <= hashes)
                for url in source["evidence_urls"]:
                    self.assertIn(url, text)

    def test_local_markdown_links_keep_queries_fragments_and_external_urls(self):
        source = serve_docs.DOCS[0]["src"]
        target = serve_docs.DOCS[-1]
        name = Path(target["src"]).name
        body = (f'<a href="{name}?format=table&amp;x=1#版本">relative</a>'
                f'<a href="/{name}#版本">root</a>'
                f'<a href="{target["src"]}#版本">absolute</a>'
                '<a href="https://example.com/file.md#ref">external</a>'
                '<a href="unregistered.md#ref">other</a>')
        result = serve_docs.rewrite_document_links(body, source)
        self.assertIn(f'href="{target["href"]}?format=table&amp;x=1#版本"', result)
        self.assertEqual(result.count(f'href="{target["href"]}#版本"'), 2)
        self.assertIn('href="https://example.com/file.md#ref"', result)
        self.assertIn('href="unregistered.md#ref"', result)


def render_visual_fixture(directory):
    """Small real pages for visual and interaction checks, without the full corpus."""
    root = Path(directory)
    source = root / "sample.md"
    source.write_text(
        '# 示例\n\n## 第一章\n\n正文与 [链接](https://example.com)。\n\n'
        '```mermaid\nflowchart LR\nA --> B\n```\n\n'
        '| 非常长且不可换行的表头一 | 非常长且不可换行的表头二 | 非常长且不可换行的表头三 |\n'
        '| --- | --- | --- |\n| 内容 | 长内容 | 第三列内容 |\n\n'
        '| 表头 | 值 |\n| --- | --- |\n| 名称 | 内容 |\n\n'
        '```text\n' + 'long-code-' * 80 + '\n```\n\n'
        '## 第二章\n\n更多内容\n', encoding="utf-8"
    )
    doc = {
        "src": str(source), "dst": str(root / "sample.html"), "href": "/sample.html",
        "title": "推理架构 Example", "hero": "推理架构 Example", "subtitle": "阅读示例",
        "summary": "缓存与 KVCache", "meta": "v1.0 · source@" + "a" * 160, "footer": "官方资料",
        "category": "推理与压测",
    }
    storage = dict(doc, title="存储设计", summary="持久化与共享文件系统", category="存储")
    custom = dict(doc, title="未分类 Example", summary="自定义页面", meta="v2.0")
    del custom["category"]
    with redirect_stdout(StringIO()), patch.object(serve_docs, "INDEX", str(root / "index.html")), patch.object(serve_docs, "DOCS", [doc, storage, custom]):
        serve_docs.render_doc(doc)
        serve_docs.render_index()
    return doc


class SharedThemeRenderingTest(unittest.TestCase):
    def test_index_categories_controls_and_custom_document_fallback(self):
        self.assertEqual({doc["category"] for doc in serve_docs.DOCS}, set(serve_docs.CATEGORIES))
        with tempfile.TemporaryDirectory() as directory:
            render_visual_fixture(directory)
            html = (Path(directory) / "index.html").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r'<a class="doc-card"[^>]*data-category="([^"]+)"', html), ["推理与压测", "存储", "其他"])
        self.assertIn('<option value="其他">其他</option>', html)
        self.assertIn('<label for="doc-search">搜索文档</label>', html)
        self.assertIn('<label for="doc-category">主题分类</label>', html)
        self.assertIn('id="doc-result-count"', html)
        self.assertIn('id="doc-clear"', html)
        self.assertIn('id="doc-empty-state"', html)
        self.assertIn("显示 3 / 3 篇", html)

    def test_wide_table_wrapping_keeps_timeline_and_code_intact(self):
        ordinary = '<table><thead><tr><th>很宽的表头</th></tr></thead></table>'
        timeline = '<div class="timeline-table-wrap"><table class="timeline-table" id="timeline-table"><tr><td>日期</td></tr></table></div>'
        code = '<pre><code>&lt;table&gt;literal&lt;/table&gt;</code></pre>'
        wrapped = serve_docs.wrap_tables(ordinary + timeline + code)
        self.assertEqual(wrapped.count('class="table-wrap"'), 1)
        self.assertIn('role="region" aria-label="可横向滚动的表格" tabindex="0"', wrapped)
        self.assertIn(timeline, wrapped)
        self.assertIn(code, wrapped)
        with tempfile.TemporaryDirectory() as directory:
            doc = render_visual_fixture(directory)
            html = Path(doc["dst"]).read_text(encoding="utf-8")
        self.assertIn('class="table-wrap"', html)
        self.assertIn('class="toc-close"', html)

    def test_navigation_and_early_theme_exist_on_all_page_types(self):
        with tempfile.TemporaryDirectory() as directory:
            doc = render_visual_fixture(directory)
            timeline = next(item for item in serve_docs.DOCS if item.get("type") == "timeline")
            with redirect_stdout(StringIO()):
                serve_docs.render_doc(dict(timeline, dst=str(Path(directory) / "timeline.html")))
            for name in ("index.html", "sample.html", "timeline.html"):
                with self.subTest(page=name):
                    html = (Path(directory) / name).read_text(encoding="utf-8")
                    self.assertEqual(html.count('id="theme-select"'), 1)
                    self.assertIn('aria-label="站点导航"', html)
                    for value, label in (("light", "明亮"), ("dark", "暗色"), ("system", "跟随系统")):
                        self.assertRegex(html, rf'<option value="{value}"[^>]*>{label}</option>')
                    self.assertLess(html.index("localStorage.getItem"), html.index("<style>"))
                    self.assertIn('id="main-content"', html)
            self.assertIn("mermaid.render", Path(doc["dst"]).read_text(encoding="utf-8"))

    def test_mermaid_fallback_preserves_definition_as_text(self):
        definition = "flowchart LR\nA[<example>] --> B & C"
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "diagram.md"
            dst = Path(directory) / "diagram.html"
            src.write_text("# 图\n\n```mermaid\n" + definition + "\n```\n", encoding="utf-8")
            with redirect_stdout(StringIO()):
                serve_docs.render_doc({
                    "src": str(src), "dst": str(dst), "title": "图",
                    "hero": "图", "subtitle": "图", "meta": "图", "footer": "图",
                })
            html = dst.read_text(encoding="utf-8")
        self.assertIn('<div class="mermaid">', html)
        self.assertIn("&lt;example&gt;", html)
        self.assertIn("&amp;", html)
        self.assertNotIn("<example>", html)

    def test_text_colors_meet_wcag_aa_on_theme_surfaces(self):
        def luminance(color):
            channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
            return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

        for name, palette in (("light", serve_docs.LIGHT_PALETTE), ("dark", serve_docs.DARK_PALETTE)):
            colors = dict(re.findall(r"--([\w-]+): (#[\da-f]{6});", palette))
            for foreground in ("text", "text-secondary", "accent", "green", "orange", "purple", "red"):
                for background in ("bg", "bg-card", "bg-code", "surface-hover"):
                    with self.subTest(theme=name, text=foreground, surface=background):
                        low, high = sorted((luminance(colors[foreground]), luminance(colors[background])))
                        self.assertGreaterEqual((high + 0.05) / (low + 0.05), 4.5)

    def test_head_metadata_present_on_all_page_types(self):
        with tempfile.TemporaryDirectory() as directory:
            render_visual_fixture(directory)
            timeline = next(item for item in serve_docs.DOCS if item.get("type") == "timeline")
            with redirect_stdout(StringIO()):
                serve_docs.render_doc(dict(timeline, dst=str(Path(directory) / "timeline.html")))
            for name, og_type in (
                ("index.html", "website"),
                ("sample.html", "article"),
                ("timeline.html", "article"),
            ):
                with self.subTest(page=name):
                    html = (Path(directory) / name).read_text(encoding="utf-8")
                    self.assertIn('<meta name="description" content="', html)
                    self.assertIn('<link rel="canonical" href="/', html)
                    self.assertIn(f'<meta property="og:type" content="{og_type}">', html)
                    self.assertIn('<meta property="og:title" content="', html)
                    self.assertIn('<meta name="twitter:card" content="summary">', html)
                    self.assertIn('rel="icon" type="image/svg+xml"', html)
                    self.assertIn('rel="preconnect" href="https://cdn.jsdelivr.net"', html)
                    self.assertEqual(html.count('<meta name="theme-color"'), 2)
                    self.assertLess(html.index("localStorage.getItem"), html.index("<style>"))

    def test_pygments_highlighting_and_theme_scoping(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "code.md"
            dst = Path(directory) / "code.html"
            src.write_text("# 代码\n\n```python\nprint('hi')\n```\n", encoding="utf-8")
            with redirect_stdout(StringIO()):
                serve_docs.render_doc({
                    "src": str(src), "dst": str(dst), "title": "代码",
                    "hero": "代码", "subtitle": "代码", "meta": "代码", "footer": "代码",
                })
            html = dst.read_text(encoding="utf-8")
        self.assertIn('<div class="highlight">', html)
        self.assertIn("<span", html)
        self.assertIn(':root[data-theme="dark"] .highlight', serve_docs.CSS)
        self.assertIn("@media (prefers-color-scheme: dark)", serve_docs.CSS)

    def test_print_rules_hide_page_chrome(self):
        match = re.search(r"@media print \{(.*)\n\}", serve_docs.CSS, re.S)
        self.assertIsNotNone(match)
        block = match.group(1)
        for selector in (
            ".site-header", ".doc-sidebar", ".doc-pager",
            ".back-to-top", ".reading-progress", ".heading-anchor",
        ):
            with self.subTest(selector=selector):
                self.assertIn(selector, block)


@unittest.skipUnless(sync_playwright, "可选浏览器测试需要 uv run --with playwright，并安装 Chromium")
class PageBrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        render_visual_fixture(cls.directory.name)
        timeline = next(doc for doc in serve_docs.DOCS if doc.get("type") == "timeline")
        with redirect_stdout(StringIO()):
            serve_docs.render_doc(dict(timeline, dst=str(Path(cls.directory.name) / "timeline.html")))
            for doc in serve_docs.DOCS:
                if Path(doc["src"]).name in ("AI-Inference-Deep-Dive.md", "Kubernetes-AI-Platform-Deep-Dive.md"):
                    serve_docs.render_doc(dict(doc, dst=str(Path(cls.directory.name) / Path(doc["dst"]).name)))

        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=cls.directory.name))
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.addClassCleanup(cls.server.server_close)
        cls.addClassCleanup(cls.server.shutdown)
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.playwright = sync_playwright().start()
        cls.addClassCleanup(cls.playwright.stop)
        cls.browser = cls.playwright.chromium.launch()
        cls.addClassCleanup(cls.browser.close)

    def setUp(self):
        self.context = self.browser.new_context(color_scheme="light")
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.context.route("https://cdn.jsdelivr.net/**", lambda route: route.abort())

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def assert_theme(self, page, theme, preference):
        page.wait_for_function("([theme, preference]) => document.documentElement.dataset.theme === theme && document.querySelector('#theme-select').value === preference", arg=[theme, preference])
        self.assertEqual(page.evaluate("getComputedStyle(document.documentElement).colorScheme"), theme)

    def test_composite_document_toc_subsection_anchors_and_mobile_navigation(self):
        for filename, parts in (("AI-Inference-Deep-Dive.html", 5), ("Kubernetes-AI-Platform-Deep-Dive.html", 9)):
            with self.subTest(document=filename):
                self.page.set_viewport_size({"width": 1280, "height": 900})
                self.page.goto(self.url + "/" + filename)
                self.assertEqual(self.page.locator("main h2").count(), parts)
                self.assertEqual(self.page.locator(".toc .toc-chapter").count(), parts)
                self.assertEqual(self.page.locator(".toc li li a").count(), self.page.locator("main h3").count())
                subsection = self.page.locator("main h4").first.get_attribute("id")
                self.assertEqual(self.page.locator(f'.toc a[href="#{subsection}"]').count(), 0)
                self.page.evaluate("id => location.hash = id", subsection)
                self.page.wait_for_function("id => document.getElementById(id).getBoundingClientRect().top < 150", arg=subsection)
                self.page.set_viewport_size({"width": 390, "height": 844})
                self.page.locator(".toc-fab").click()
                self.assertEqual(self.page.locator("#doc-sidebar").get_attribute("role"), "dialog")
                chapter = self.page.locator(".toc li li a").last
                href = chapter.get_attribute("href")
                chapter.click()
                self.page.wait_for_function("!document.body.classList.contains('toc-open')")
                self.assertEqual(unquote(urlsplit(self.page.url).fragment), href[1:])
                self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth"))

    def test_composite_document_mermaid_theme_switching_and_cross_page_persistence(self):
        self.context.unroute("https://cdn.jsdelivr.net/**")
        module = """
        let theme;
        export default {
          initialize(config) { theme = config.themeVariables.darkMode ? 'dark' : 'light'; },
          async render(id, source) {
            return {svg: `<svg data-test-theme="${theme}"><text>Diagram</text></svg>`};
          }
        };
        """
        self.context.route("https://cdn.jsdelivr.net/**", lambda route: route.fulfill(body=module, content_type="text/javascript"))
        for filename in ("AI-Inference-Deep-Dive.html", "Kubernetes-AI-Platform-Deep-Dive.html"):
            self.page.goto(self.url + "/" + filename)
            self.page.wait_for_function("[...document.querySelectorAll('.mermaid')].every(node => node.querySelector('svg'))")
            count = self.page.locator(".mermaid").count()
            self.assertGreater(count, 10)
            self.page.select_option("#theme-select", "dark")
            self.assert_theme(self.page, "dark", "dark")
            self.page.wait_for_function("[...document.querySelectorAll('.mermaid svg')].every(node => node.dataset.testTheme === 'dark')")
            self.assertEqual(self.page.locator('.mermaid svg[data-test-theme="dark"]').count(), count)
            self.page.reload()
            self.assert_theme(self.page, "dark", "dark")

    def test_index_search_and_category_intersection(self):
        self.page.goto(self.url)
        search = self.page.locator("#doc-search")
        search.fill("kVcAcHe")
        self.assertEqual(self.page.locator(".doc-card:not([hidden])").count(), 1)
        self.page.select_option("#doc-category", "存储")
        self.assertEqual(self.page.locator(".doc-card:not([hidden])").count(), 0)
        self.assertTrue(self.page.locator("#doc-empty-state").is_visible())
        self.assertEqual(self.page.locator("#doc-result-count").inner_text(), "显示 0 / 3 篇")
        self.page.click("#doc-clear")
        self.assertEqual(search.input_value(), "")
        self.assertEqual(self.page.locator("#doc-category").input_value(), "")
        self.assertTrue(search.evaluate("node => node === document.activeElement"))
        self.assertEqual(self.page.locator(".doc-card:not([hidden])").count(), 3)
        self.assertFalse(self.page.locator("#doc-empty-state").is_visible())
        search.fill("共享")
        self.assertEqual(self.page.locator(".doc-card:not([hidden]) h2").inner_text(), "存储设计")
        search.fill("存储")
        self.assertEqual(self.page.locator(".doc-card:not([hidden])").count(), 1)
        search.fill("source@")
        self.assertEqual(self.page.locator(".doc-card:not([hidden])").count(), 0)
        self.page.click("#doc-clear")
        self.page.select_option("#doc-category", "其他")
        self.assertEqual(self.page.locator(".doc-card:not([hidden]) h2").inner_text(), "未分类 Example")

    def test_mobile_toc_keyboard_close_focus_and_resize(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.page.goto(self.url + "/sample.html")
        sidebar = self.page.locator("#doc-sidebar")
        opener = self.page.locator(".toc-fab")
        close = self.page.locator(".toc-close")
        self.assertTrue(sidebar.evaluate("node => node.inert"))
        self.assertFalse(sidebar.is_visible())
        for _ in range(8):
            self.page.keyboard.press("Tab")
            self.assertFalse(sidebar.evaluate("node => node.contains(document.activeElement)"))
        opener.click()
        self.assertTrue(close.evaluate("node => node === document.activeElement"))
        self.assertEqual(sidebar.get_attribute("aria-modal"), "true")
        self.assertTrue(self.page.locator("main").evaluate("node => node.inert"))
        self.page.keyboard.press("Shift+Tab")
        self.assertTrue(sidebar.locator("a").last.evaluate("node => node === document.activeElement"))
        self.page.keyboard.press("Tab")
        self.assertTrue(close.evaluate("node => node === document.activeElement"))
        self.page.keyboard.press("Escape")
        self.assertTrue(opener.evaluate("node => node === document.activeElement"))
        self.assertTrue(sidebar.evaluate("node => node.inert"))
        self.assertFalse(self.page.locator("main").evaluate("node => node.inert"))
        opener.click()
        close.click()
        self.assertTrue(opener.evaluate("node => node === document.activeElement"))
        opener.click()
        self.page.locator(".toc-backdrop").click(position={"x": 380, "y": 200})
        self.assertTrue(opener.evaluate("node => node === document.activeElement"))
        opener.click()
        sidebar.locator('a[href="#第一章"]').click()
        self.page.wait_for_function("location.hash === '#%E7%AC%AC%E4%B8%80%E7%AB%A0'")
        self.assertFalse(sidebar.is_visible())
        opener.click()
        self.page.set_viewport_size({"width": 1280, "height": 900})
        self.page.wait_for_function("!document.querySelector('#doc-sidebar').inert && !document.body.classList.contains('toc-open')")
        self.assertTrue(sidebar.is_visible())
        self.assertIsNone(sidebar.get_attribute("aria-modal"))
        self.assertTrue(sidebar.locator('a').first.evaluate("node => node === document.activeElement"))

    def test_responsive_grid_and_independent_scrolling_in_both_themes(self):
        for theme in ("light", "dark"):
            self.page.goto(self.url)
            self.page.select_option("#theme-select", theme)
            for width, columns in ((1280, 3), (900, 2), (390, 1), (320, 1)):
                with self.subTest(theme=theme, width=width):
                    self.page.set_viewport_size({"width": width, "height": 900})
                    self.assertEqual(self.page.locator(".doc-grid").evaluate("node => getComputedStyle(node).gridTemplateColumns.split(' ').length"), columns)
                    self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
            self.page.goto(self.url + "/sample.html")
            self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
            for selector in (".table-wrap", "pre"):
                with self.subTest(scroll_area=selector):
                    area = self.page.locator(selector).first
                    self.assertTrue(area.evaluate("node => node.scrollWidth > node.clientWidth"))
                    self.assertEqual(area.evaluate("node => getComputedStyle(node).overflowX"), "auto")
            self.assertGreaterEqual(self.page.locator('.table-wrap table').first.evaluate("node => node.clientWidth"), 640)
            self.assertTrue(self.page.locator('.table-wrap').last.evaluate("node => node.scrollWidth <= node.clientWidth"))
            self.page.emulate_media(reduced_motion="reduce")
            self.assertEqual(self.page.evaluate("getComputedStyle(document.documentElement).scrollBehavior"), "auto")

    def test_timeline_filters_urls_exports_and_empty_results(self):
        self.page.goto(self.url + "/timeline.html?supplier=OpenAI&year=2024")
        rows = self.page.locator("#timeline-table tbody tr:not([hidden])")
        count = rows.count()
        self.assertGreater(count, 0)
        self.assertTrue(rows.evaluate_all("nodes => nodes.every(node => node.dataset.supplier === 'OpenAI' && node.dataset.year === '2024')"))
        for kind in ("csv", "json", "markdown"):
            with self.subTest(export=kind), self.page.expect_download() as pending:
                self.page.click(f"#timeline-export-{kind}")
            download = pending.value
            content = Path(download.path()).read_text(encoding="utf-8-sig")
            if kind == "json":
                records = json.loads(content)
                self.assertEqual(len(records), count)
                self.assertEqual(set(records[0]), {key for key, _ in serve_docs.TIMELINE_COLUMNS} | {"year", "multimodal", "open_source"})
                self.assertTrue(all(record["supplier"] == "OpenAI" for record in records))
                self.assertIn("https://", records[0]["official_source"])
            elif kind == "csv":
                exported_rows = list(csv.reader(StringIO(content)))
                self.assertEqual(len(exported_rows), count + 1)
                self.assertEqual(exported_rows[0], [label for _, label in serve_docs.TIMELINE_COLUMNS])
            else:
                self.assertIn("| 发布时间 |", content)
                self.assertEqual(len([line for line in content.splitlines() if line.startswith("|")]), count + 2)
        self.page.select_option("#timeline-multimodal-filter", "yes")
        self.assertIn("multimodal=yes", self.page.url)
        self.assertTrue(rows.evaluate_all("nodes => nodes.every(node => node.dataset.multimodal === 'yes')"))
        self.page.click("#timeline-clear-filters")
        self.assertEqual(rows.count(), 126)
        self.assertNotIn("supplier=", self.page.url)
        self.page.locator('input[data-filter="supplier"][value="Xiaomi / MiMo"]').check()
        self.page.locator('input[data-filter="year"][value="2022"]').check()
        self.assertEqual(rows.count(), 0)
        self.assertTrue(self.page.locator("#timeline-empty-state").is_visible())
        self.assertTrue(self.page.locator("#timeline-export-csv").is_disabled())
        self.page.reload()
        self.assertEqual(rows.count(), 0)
        self.page.select_option("#theme-select", "dark")
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth"))

    def test_theme_persistence_system_changes_and_tabs(self):
        self.page.goto(self.url)
        self.assert_theme(self.page, "light", "system")
        self.page.emulate_media(color_scheme="dark")
        self.assert_theme(self.page, "dark", "system")
        self.page.select_option("#theme-select", "light")
        self.page.emulate_media(color_scheme="light")
        self.page.emulate_media(color_scheme="dark")
        self.assert_theme(self.page, "light", "light")
        self.page.reload()
        self.assert_theme(self.page, "light", "light")
        self.page.goto(self.url + "/sample.html")
        self.assert_theme(self.page, "light", "light")
        second = self.context.new_page()
        second.goto(self.url)
        second.select_option("#theme-select", "dark")
        self.assert_theme(self.page, "dark", "dark")
        second.evaluate("localStorage.clear()")
        self.assert_theme(self.page, "dark", "system")

    def test_invalid_and_unavailable_storage(self):
        self.page.goto(self.url)
        self.page.evaluate("localStorage.setItem('ai-docs-theme', 'invalid')")
        self.page.reload()
        self.assert_theme(self.page, "light", "system")
        self.context.add_init_script("Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('blocked'); } });")
        self.page.reload()
        self.assert_theme(self.page, "light", "system")
        self.page.select_option("#theme-select", "dark")
        self.assert_theme(self.page, "dark", "dark")

    def test_no_javascript_follows_system(self):
        context = self.browser.new_context(java_script_enabled=False, color_scheme="dark")
        try:
            page = context.new_page()
            page.goto(self.url)
            self.assertEqual(page.evaluate("getComputedStyle(document.documentElement).colorScheme"), "dark")
            self.assertTrue(page.locator("#theme-select").is_disabled())
            page.emulate_media(color_scheme="light")
            self.assertEqual(page.evaluate("getComputedStyle(document.documentElement).colorScheme"), "light")
        finally:
            context.close()

    def test_mermaid_loading_failure_keeps_source(self):
        self.page.goto(self.url + "/sample.html")
        self.page.wait_for_selector('.mermaid[data-mermaid-error="true"]')
        self.assertIn("A --> B", self.page.locator(".mermaid").inner_text())
        self.page.select_option("#theme-select", "dark")
        self.assertIn("A --> B", self.page.locator(".mermaid").inner_text())

    def test_mermaid_serializes_and_merges_rapid_theme_changes(self):
        self.context.unroute("https://cdn.jsdelivr.net/**")
        module = """
        let config;
        window.diagramRuns = [];
        window.activeRenders = 0;
        window.maxActiveRenders = 0;
        export default {
          initialize(value) { config = value; },
          async render(id, source) {
            window.activeRenders++;
            window.maxActiveRenders = Math.max(window.maxActiveRenders, window.activeRenders);
            const theme = config.themeVariables.darkMode ? 'dark' : 'light';
            window.diagramRuns.push({theme, source});
            await new Promise(resolve => setTimeout(resolve, 80));
            window.activeRenders--;
            if (source === 'invalid diagram') throw new Error('parse error');
            return {svg: `<svg data-test-theme="${theme}"><text>A → B</text></svg>`};
          }
        };
        """
        self.context.route("https://cdn.jsdelivr.net/**", lambda route: route.fulfill(body=module, content_type="text/javascript"))
        self.page.goto(self.url + "/sample.html")
        self.page.wait_for_function("window.activeRenders === 1")
        self.page.evaluate("['dark', 'light', 'dark'].forEach(window.docsTheme.setPreference)")
        self.page.wait_for_selector('.mermaid[data-rendered="dark"] svg[data-test-theme="dark"]')
        self.assertEqual(self.page.evaluate("window.maxActiveRenders"), 1)
        sources = self.page.evaluate("window.diagramRuns.map(run => run.source)")
        self.assertTrue(all(source == "flowchart LR\nA --> B" for source in sources))
        self.page.select_option("#theme-select", "light")
        self.page.wait_for_selector('.mermaid[data-rendered="light"]')
        invalid_html = (Path(self.directory.name) / "sample.html").read_text(encoding="utf-8").replace("flowchart LR\nA --&gt; B", "invalid diagram")
        self.context.route(self.url + "/invalid.html", lambda route: route.fulfill(body=invalid_html, content_type="text/html"))
        self.page.goto(self.url + "/invalid.html")
        self.page.wait_for_selector('.mermaid[data-mermaid-error="true"]')
        self.assertEqual(self.page.locator(".mermaid").inner_text(), "invalid diagram")


    def test_scrollspy_highlights_active_section_and_back_to_top(self):
        self.page.set_viewport_size({"width": 1280, "height": 900})
        self.page.goto(self.url + "/AI-Inference-Deep-Dive.html")
        heading_id = self.page.locator("main h2[id]").nth(1).get_attribute("id")
        self.page.evaluate("id => { location.hash = ''; location.hash = id; }", heading_id)
        self.page.wait_for_function(
            """id => [...document.querySelectorAll('.toc a[aria-current="true"]')]
               .some(a => a.getAttribute('href') === '#' + id)""",
            arg=heading_id,
        )
        self.assertEqual(self.page.locator('.toc a[aria-current="true"]').count(), 1)
        self.page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        self.page.wait_for_function("document.querySelector('.back-to-top').hidden === false")
        self.page.emulate_media(reduced_motion="reduce")
        self.page.locator(".back-to-top").click()
        self.page.wait_for_function("window.scrollY < 5")


class RenderDocLayoutTest(unittest.TestCase):
    def test_all_deep_dives_are_registered_and_use_current_audit_date(self):
        docs_dir = Path(__file__).resolve().parent
        markdown_docs = {path.name for path in docs_dir.glob("*-Deep-Dive.md")}
        deep_dive_docs = [doc for doc in serve_docs.DOCS if doc.get("type") != "timeline"]
        registered_docs = {Path(doc["src"]).name for doc in deep_dive_docs}

        self.assertEqual(len(markdown_docs), 6)
        self.assertEqual(registered_docs, markdown_docs)
        for doc in deep_dive_docs:
            with self.subTest(document=Path(doc["src"]).name):
                self.assertIn("2026-10-16", doc["meta"])
                self.assertNotIn("2026-09-17", doc["meta"])
                self.assertNotIn("2026-09-06", doc["meta"])
                self.assertNotIn("2026-09-01", doc["meta"])
                self.assertNotIn("2026-08-22", doc["meta"])
                markdown_text = Path(doc["src"]).read_text(encoding="utf-8")
                self.assertIn("审校日期：2026-10-16", markdown_text)
                self.assertNotIn("审校日期：2026-09-17", markdown_text)
                self.assertNotIn("审校日期：2026-09-06", markdown_text)
                self.assertNotIn("审校日期：2026-08-22", markdown_text)

    def test_model_release_timeline_is_registered_with_its_own_page_metadata(self):
        docs_by_src = {Path(doc["src"]).name: doc for doc in serve_docs.DOCS}

        self.assertIn("model_release_timeline.md", docs_by_src)
        doc = docs_by_src["model_release_timeline.md"]
        self.assertEqual(doc["type"], "timeline")
        self.assertEqual(Path(doc["dst"]).name, "model_release_timeline.html")
        self.assertEqual(doc["href"], "/model_release_timeline.html")
        self.assertEqual(doc["title"], "模型发布时间时间线")
        self.assertEqual(doc["hero"], "模型发布时间时间线")
        self.assertIn("2026-10-16", doc["meta"])
        self.assertIn("筛选", doc["summary"])
        self.assertIn("导出", doc["summary"])
        self.assertIn("model_release_timeline.md", doc["footer"])

    def test_render_index_includes_model_release_timeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_index = serve_docs.INDEX
            serve_docs.INDEX = str(Path(tmpdir) / "index.html")
            try:
                serve_docs.render_index()
                html = Path(serve_docs.INDEX).read_text(encoding="utf-8")
            finally:
                serve_docs.INDEX = original_index

        self.assertIn("模型发布时间时间线", html)
        self.assertIn('/model_release_timeline.html', html)
        self.assertIn("2026-10-16", html)

    def test_timeline_source_has_126_rows_and_rendered_rows_have_filter_metadata(self):
        source = Path(__file__).resolve().parent / "model_release_timeline.md"
        source_rows = re.findall(r"^\| 20", source.read_text(encoding="utf-8"), re.M)
        self.assertEqual(len(source_rows), 126)

        doc = next(doc for doc in serve_docs.DOCS if doc.get("type") == "timeline")
        with tempfile.TemporaryDirectory() as tmpdir:
            rendered_doc = dict(doc, dst=str(Path(tmpdir) / "timeline.html"))
            serve_docs.render_doc(rendered_doc)
            html = Path(rendered_doc["dst"]).read_text(encoding="utf-8")

        rendered_rows = re.findall(
            r'<tr data-year="([^"]+)" data-supplier="([^"]+)" '
            r'data-multimodal="(yes|no)" data-open-source="(yes|no)">',
            html,
        )
        self.assertEqual(len(rendered_rows), 126)
        self.assertEqual(
            {row[0] for row in rendered_rows},
            {"2022", "2023", "2024", "2025", "2026"},
        )
        self.assertEqual(
            {row[1] for row in rendered_rows},
            {
                "DeepSeek",
                "Moonshot / Kimi",
                "Alibaba / Qwen",
                "智谱 / GLM",
                "Xiaomi / MiMo",
                "腾讯混元",
                "OpenAI",
                "Anthropic",
                "Google",
            },
        )
        self.assertIn(
            ('2024', 'OpenAI', 'yes', 'no'),
            rendered_rows,
        )
        self.assertIn(
            ('2023', 'Alibaba / Qwen', 'yes', 'yes'),
            rendered_rows,
        )
        timeline_text = source.read_text(encoding="utf-8")
        for entry in (
            "GPT-6 Astra",
            "GPT-6 Sol / GPT-6 Luna",
            "GPT-6.1 Sol",
            "GPT-6 in ChatGPT / Intelligent UI",
            "Gemini 4 Argon",
            "这是产品部署更新，不是新的底层模型",
            "同一公告中的两个模型档位合并为一行",
        ):
            with self.subTest(timeline_entry=entry):
                self.assertIn(entry, timeline_text)
        self.assertIn(('2026', 'Google', 'yes', 'no'), rendered_rows)

    def test_timeline_controls_restore_and_combine_filters(self):
        doc = next(doc for doc in serve_docs.DOCS if doc.get("type") == "timeline")
        with tempfile.TemporaryDirectory() as tmpdir:
            rendered_doc = dict(doc, dst=str(Path(tmpdir) / "timeline.html"))
            serve_docs.render_doc(rendered_doc)
            html = Path(rendered_doc["dst"]).read_text(encoding="utf-8")

        for control in (
            'id="timeline-controls"',
            'name="supplier"',
            'name="year"',
            'id="timeline-multimodal-filter"',
            'id="timeline-open-source-filter"',
            'id="timeline-clear-filters"',
            'id="timeline-result-count"',
            '当前筛选没有匹配记录',
        ):
            with self.subTest(control=control):
                self.assertIn(control, html)

        for script_contract in (
            "new URLSearchParams(window.location.search)",
            "url.searchParams.set(filterName, state[filterName].join(','))",
            "window.history.replaceState",
            "state.supplier.length && !state.supplier.includes(record.supplier)",
            "state.year.length && !state.year.includes(record.year)",
            "state.multimodal && (record.multimodal ? 'yes' : 'no')",
            "state.open_source && (record.open_source ? 'yes' : 'no')",
            "const visible = visibleRecords()",
            "record._row.hidden = !visibleRows.has(record)",
        ):
            with self.subTest(script_contract=script_contract):
                self.assertIn(script_contract, html)

    def test_timeline_exports_preserve_schema_links_and_empty_state_contract(self):
        doc = next(doc for doc in serve_docs.DOCS if doc.get("type") == "timeline")
        with tempfile.TemporaryDirectory() as tmpdir:
            rendered_doc = dict(doc, dst=str(Path(tmpdir) / "timeline.html"))
            serve_docs.render_doc(rendered_doc)
            html = Path(rendered_doc["dst"]).read_text(encoding="utf-8")

        for button in (
            'id="timeline-export-csv"',
            'id="timeline-export-json"',
            'id="timeline-export-markdown"',
        ):
            self.assertIn(button, html)
        for field in (
            "release_date",
            "supplier",
            "model",
            "type",
            "release_form",
            "features",
            "lineage",
            "official_source",
            "notes",
            "year",
            "multimodal",
            "open_source",
        ):
            with self.subTest(field=field):
                self.assertIn(field, html)
        for export_contract in (
            "\\ufeff",
            '''replaceAll('"', '""')''',
            "model-release-timeline-filtered.csv",
            "model-release-timeline-filtered.json",
            "model-release-timeline-filtered.md",
            "JSON.stringify(records.map(toExportRecord), null, 2)",
            "当前筛选没有匹配记录。",
            "key === 'official_source' ? record[key] : markdownCell(record[key])",
        ):
            with self.subTest(export_contract=export_contract):
                self.assertIn(export_contract, html)

    def test_timeline_metadata_detection_handles_month_only_and_open_semantics(self):
        cells = [
            "2023-09（官方回顾）",
            "Example / Model",
            "Vision Model",
            "多模态、视觉",
            "研究发布、开放权重",
            "支持 Apache-2.0 和图像理解",
            "A → B",
            '<a href="https://example.com">官方公告</a>',
            "官方只提供月份。",
        ]

        self.assertEqual(
            serve_docs._timeline_row_metadata(cells),
            {
                "year": "2023",
                "supplier": "Example / Model",
                "multimodal": "yes",
                "open_source": "yes",
            },
        )

    def test_readme_tracks_domain_index_and_evidence_boundaries(self):
        root = Path(__file__).resolve().parent
        readme = (root / "README.md").read_text()
        entries = re.findall(r"^\| \[.*?\]\(([^)#]+\.md)\)", readme, re.M)
        self.assertEqual(set(entries), {Path(doc["src"]).name for doc in serve_docs.DOCS})
        self.assertEqual(len(entries), 7)
        for term in ("2026-10-16", "exact source commit", "tag-only", "未发布主线快照", "26.03.1", "v0.21.0", "docs_migration.json", "不提供旧地址重定向"):
            self.assertIn(term, readme)
        # All former README revision pins remain verifiable in their domain documents.
        corpus = "\n".join(Path(doc["src"]).read_text() for doc in serve_docs.DOCS)
        revisions = ['v1.5.0@b83b1d9304ebfc624709ac46db32b1b6f1ff1615', 'v18.10.0@ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d', 'v0.6.0@e91f650aa6a1847959e7f7da1b39c19e16b312e3', '2026.30@f32ee8a2a50052f32e3632ceb451111a98dd5104', 'v1.0.4@810726d89c71da77cdc82668bca1b00f5cd21ed8', 'v0.29.1@54f93c807be2c161a94c0df764242849125161a8', 'v0.5.3@ff8b285497809e084915016c40c2bc5e5991ffbc', 'v0.19.6@f0e95cea51b5591e0177fbe0fa06a299f36db548', 'v0.18.0@2df9a1ffca535d602d57023074b824606e312797', 'v0.7.4@291a6e609c3eb52d6eadcedecc7a056e396cd5eb', 'v0.7.0@5804ea6b7ebd2bfceff29cf113311ed3af95146e', 'v0.5.4@9e441efe48756928e453ff26694d6e5af1a9c71d', 'v0.5.20@94602c9c2b7cbdb8efd5c52802dac6a1c180089e', 'v26.7.2@5a9c8a8b3f5bac7fb06ad3c2a05771fceb8b4832', 'v2.10.0@4707fb02c91c545bc7343ce26dba4c32919f9a3e', 'v1.37.1@f78e722310e50bcaca9276be22276d9e91d91308', 'v0.30.0@ced6857afa0ea7b2e3f0846a62e1394e90f15607', 'v1.12.0@f09e55de5d5f0a0953cd90aa7b0382b45859c4f5', 'v0.3.13.post1@719735896c86b56fabec6cf3e825fb2ea640597a', 'v0.1.0-alpha.13@af2df1ffff0ae7a1135554564a6240a3f22f2c35', 'v1.15.2@1462fb7b4835970708717456e3aed85e697ec2eb', 'v0.33.3@76042ed40db3bab9506b689f436716b6df624f23', 'main@ccaf9fc0ffe6ac39c7ec786af7608ab1de19467b', 'main@12f8f3f31111564e5e1b9aac3f7f916e8bba4039', 'master@bb22cc477a6bd317bb2c7e357a85efcab8c7462a', 'main@71c8b22a05d6be72560b2cc326865930063cd0e8', 'main@618b581b32668e317b0d18523d46cf9f55b549d8', 'master@f5258704d7ef5bda28f31ba51950cdea9adbe921', 'volcano-1.15.2@c2050e3debe58dbcdf9bb75b667799eec9409513', 'main@22fca04564c7cc230fd8b9523b8b92864e1dad47', 'v0.20.1@5922dc7d1a4661d3fc43d60943f92a775c892bdc']
        for revision in revisions:
            version, commit = revision.split("@")
            with self.subTest(revision=revision):
                self.assertIn(version, corpus)
                self.assertIn(commit, corpus)

    def test_teleport_doc_is_registered_rendered_and_source_backed(self):
        docs_by_src = {Path(doc["src"]).name: doc for doc in serve_docs.DOCS}

        self.assertIn("Teleport-Deep-Dive.md", docs_by_src)
        doc = docs_by_src["Teleport-Deep-Dive.md"]
        self.assertEqual(Path(doc["dst"]).name, "Teleport-Deep-Dive.html")
        self.assertEqual(doc["href"], "/Teleport-Deep-Dive.html")
        self.assertEqual(doc["title"], "基础设施访问治理：Self-hosted 平台对比")
        self.assertEqual(doc["hero"], "基础设施访问治理：Self-hosted 平台对比")
        self.assertEqual(
            doc["meta"],
            "Teleport v18.10.0 · Bastion v3.24.01 · Warpgate v0.29.2 · Boundary v0.21.3 · Pomerium v0.33.4 · Guacamole 1.6.0 tag-only · 2026-10-16",
        )
        for summary_term in (
            "六个平台",
            "统一能力矩阵",
            "短期凭据",
            "RBAC/JIT",
            "SSH/Kubernetes/数据库/HTTP/RDP/VNC",
            "录制/SIEM",
            "许可证商业边界",
        ):
            with self.subTest(summary_term=summary_term):
                self.assertIn(summary_term, doc["summary"])

        for source_link in (
            "https://github.com/gravitational/teleport/tree/"
            "ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d",
            "https://github.com/ovh/the-bastion/releases/tag/v3.24.01",
            "https://github.com/warp-tech/warpgate/releases/tag/v0.29.2",
            "https://developer.hashicorp.com/boundary/docs/concepts",
            "https://www.pomerium.com/docs",
            "https://guacamole.apache.org/doc/gug/",
        ):
            with self.subTest(source_link=source_link):
                self.assertIn(source_link, doc["footer"])

        markdown_text = Path(doc["src"]).read_text(encoding="utf-8")
        for required_text in (
            "审校日期：2026-10-16",
            "v18.10.0",
            "v0.29.2@5c5ee3f2e300ff01d305c3fe9301fe68ec1ad934",
            "ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d",
            "lightweight tag",
            "GNU AGPL-3.0",
            "Teleport Community Edition License",
            "少于 100 名员工且年收入低于 1,000 万美元",
            "Auth Service",
            "Proxy Service",
            "Node Service",
            "Reverse Tunnel",
            "Trusted Cluster",
            "`tsh`",
            "`tctl`",
            "`tbot`",
            "kubernetes_resources",
            "db_labels",
            "app_labels",
            "mcp.tools",
            "Per-session MFA",
            "Community 唯一官方 SSO connector",
            "OIDC / SAML",
            "Session/Identity Lock",
            "SSH Server Access",
            "Kubernetes Access",
            "Database Access",
            "Application、TCP 与 Cloud API Access",
            "Windows Desktop Access",
            "MCP Access",
            "mcp.session.start/end/request/notification",
            "Teleport-Jwt-Assertion",
            "node-sync",
            "proxy-sync",
            "Auth→Proxy→Agent",
            "v19.*-dev.*",
            "v0.33.4@5cd94927fee53f35a2bbd77797cc9524094bff78",
            "v0.33.2` 虽有 tag，但 release build 失败",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, markdown_text)

        with tempfile.TemporaryDirectory() as tmpdir:
            rendered_doc = dict(doc)
            rendered_doc["dst"] = str(Path(tmpdir) / "teleport.html")
            serve_docs.render_doc(rendered_doc)
            html = Path(rendered_doc["dst"]).read_text(encoding="utf-8")

            original_index = serve_docs.INDEX
            serve_docs.INDEX = str(Path(tmpdir) / "index.html")
            try:
                serve_docs.render_index()
                index_html = Path(serve_docs.INDEX).read_text(encoding="utf-8")
            finally:
                serve_docs.INDEX = original_index

        self.assertIn(
            '<a class="toc-chapter" '
            'href="#第一章比较对象-版本与证据规则">',
            html,
        )
        self.assertGreaterEqual(html.count('<div class="mermaid">'), 3)
        self.assertIn("flowchart LR", html)
        self.assertIn("sequenceDiagram", html)
        self.assertNotIn('class="language-mermaid"', html)
        self.assertIn(
            "ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d", html
        )
        self.assertIn("基础设施访问治理：Self-hosted 平台对比", index_html)
        self.assertIn('/Teleport-Deep-Dive.html', index_html)
        self.assertIn("Teleport v18.10.0", index_html)

    def test_kubernetes_blog_doc_is_registered_rendered_and_source_backed(self):
        docs_by_src = {Path(doc["src"]).name: doc for doc in serve_docs.DOCS}

        self.assertIn("Kubernetes-AI-Platform-Deep-Dive.md", docs_by_src)
        doc = docs_by_src["Kubernetes-AI-Platform-Deep-Dive.md"]
        self.assertEqual(
            doc["title"], "Kubernetes AI 平台深度文档"
        )
        self.assertEqual(
            doc["category"],
            "Kubernetes 平台",
        )
        for summary_term in (
            "Workload/Gang",
            "Node lifecycle",
            "resize preemption",
            "DRA",
            "Memory QoS",
            "Pod-level managers",
            "Native Histograms",
            "CBT",
            "存储加固",
            "rootless",
            "Stable/Beta/Alpha",
        ):
            with self.subTest(summary_term=summary_term):
                self.assertIn(summary_term, Path(doc["src"]).read_text())

        for source_link in (
            "https://kubernetes.io/blog/",
            "https://kubernetes.io/feed.xml",
            "https://kubernetes.io/blog/2026/08/26/kubernetes-v1-37-release/",
            "https://kubernetes.io/docs/",
            "https://kep.k8s.io/5966",
            "f78e722310e50bcaca9276be22276d9e91d91308",
        ):
            with self.subTest(source_link=source_link):
                self.assertIn(source_link, doc["footer"])

        markdown_text = Path(doc["src"]).read_text(encoding="utf-8")
        for required_text in (
            "审校日期：2026-10-16",
            "v1.37.1@f78e722310e50bcaca9276be22276d9e91d91308",
            "2026-09-02",
            "2026-09-03",
            "2026-09-04",
            "2026-09-08",
            "2026-09-09",
            "2026-09-10",
            "2026-09-11",
            "2026-09-14",
            "2026-09-15",
            "2026-09-16",
            "2026-09-21",
            "2026-09-22",
            "PersistentVolumeClaimUnusedSinceTime",
            "NoPodsUsingPVC",
            "sig-apps-spotlight",
            "KEP-4443",
            "HPA",
            "Scale-to-Zero",
            "DRA",
            "Gang Scheduling",
            "Storage Version Migration",
            "RangeStream",
            "Pod Certificates",
            "ClusterTrustBundles",
            "KubeletInUserNamespace",
            "KYAML",
            "Gateway API",
            "Agent Sandbox",
            "staticManifestsDir",
            "StatefulSetRecreateStrategy",
            "PodAndContainerStatsFromCRI",
            "NodeLifecycleConditions",
            "DrainInProgress",
            "InPlacePodVerticalScalingSchedulerPreemption",
            "always_scrape_classic_histograms",
            "cbt.storage.k8s.io/v1beta1",
            "VolumeBindMountOptions",
            "EmptyDirVolumeMode",
            "PodResources",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, markdown_text)

        with tempfile.TemporaryDirectory() as tmpdir:
            rendered_doc = dict(doc)
            rendered_doc["dst"] = str(Path(tmpdir) / "kubernetes-blog.html")
            serve_docs.render_doc(rendered_doc)
            html = Path(rendered_doc["dst"]).read_text(encoding="utf-8")

        self.assertIn(
            '<a href="#k8s-history-rss-范围与证据边界">', html
        )
        self.assertIn('<div class="mermaid">', html)
        self.assertNotIn('class="language-mermaid"', html)
        self.assertIn("Kubernetes AI 平台深度文档", html)
        self.assertIn("f78e722310e50bcaca9276be22276d9e91d91308", html)

    def test_benchmark_snapshot_uses_current_stable_releases(self):
        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "AI-Inference-Deep-Dive.md"
        )
        markdown_text = Path(doc["src"]).read_text(encoding="utf-8")

        for release in (
            "AIPerf v0.13.0",
            "GuideLLM v0.7.4",
            "inference-perf v0.7.0",
            "SGLang v0.5.21",
            "vLLM v0.31.0",
            "EvalScope v1.13.0",
        ):
            self.assertIn(release, doc["meta"])
        self.assertIn("genai-bench/tree/v0.0.5", doc["footer"])
        self.assertIn("e00930c5489053f26d86b179cee0d087f846acbb", doc["footer"])
        self.assertIn("db9527a46873454610df6dbedf79a36d6bf1a7f6", doc["footer"])
        for exact_commit in (
            "794f8bb75f8582f22e412d7e650fc71ca2a3d21a",
            "291a6e609c3eb52d6eadcedecc7a056e396cd5eb",
            "5804ea6b7ebd2bfceff29cf113311ed3af95146e",
            "498027686e6e3cf4eb32405a3fd21c65ff9237f1",
            "4f873e03719c947a101647c6646954d5ebc3d35b",
            "e00930c5489053f26d86b179cee0d087f846acbb",
            "db9527a46873454610df6dbedf79a36d6bf1a7f6",
            "9e441efe48756928e453ff26694d6e5af1a9c71d",
        ):
            self.assertIn(exact_commit, markdown_text)
        self.assertIn("text-to-speech", markdown_text)
        self.assertIn("Audio Throughput", markdown_text)
        self.assertIn('A(500)', markdown_text)
        self.assertIn("spec_cap_lens_histogram", markdown_text)
        self.assertIn("vllm-bench", markdown_text)
        self.assertNotIn("fdebc938f7f4d16fe6b9f55dcd9a767cf0899ea1", markdown_text)
        self.assertNotIn("be53bf2953d30e46c500e6a80fc1f8b6f84bc718", markdown_text)
        self.assertNotIn("0bcd822377da7b5718e674eaf9c870d349424dd1", markdown_text)
        self.assertNotIn("98dff2a81d747d1dba01a47f939f48c3526d4206", markdown_text)
        self.assertNotIn("a6a2e419abb83fdc2f8a4d766c26567a008dbc96", markdown_text)
        self.assertNotIn("568afb3a13806beb53bb2e6bd518269357b237c0", markdown_text)
        self.assertNotIn(
            "0e723bb8c984564cddf7274d19aab4eb7714f919", markdown_text
        )
        self.assertNotIn(
            "github.com/sgl-project/sglang/blob/"
            "71de97b264b04dcd514cf904003028aefe9775c8/docs_new/",
            markdown_text,
        )
        for required_text in (
            "AgentX v1.0",
            "--endpoint-type messages",
            "adaptive_scale_events.jsonl",
            "click~=8.4.0",
            "GUIDELLM_DEFAULT_RESULTS_DIR",
            "prefix_file",
            "prefix_role",
            "Avg Latency (s)",
            "混合流式/非流式 run",
            "纯非流式 run 仍保留兼容 fallback",
            "vllm-embedding",
            "autobench` 已在 v0.5.17 移除",
            "SGLANG_CACHE_DIR",
            "torch 2.13.0",
            "triton 3.7.1",
            "22 个未维护 benchmark 被移除",
            "VLLM_SERVER_DEV_MODE=1",
            "按 token ID 排序后的 tokenizer vocabulary",
            "processor 初始化后重新设置 Python 和 NumPy seed",
            "docs/docs/developer_guide/bench_serving.mdx",
            "拿不到 worker internal states",
            "--probe-request-rate",
            "probe 不占 `--max-concurrency` semaphore",
            "VLLM_USE_RUST_BENCH=1",
            "VLLM_RUST_FRONTEND_PATH",
            "跳过稀疏 vocab 中未分配的 ID",
            "`sonnet`、`hf`、`timed_trace`",
            "不为同一 chunk 内的 token 人工补零",
            "quantized DSpark Markov head",
            "没有专用的 prefill/decode 分角色模式",
            "timed_trace",
            "预 tokenized `list[int]`",
            "Rust `vllm-bench` 以 byte buffer",
            "Triton Proton profiler",
            "closed-loop warmup",
            "nearest-rank",
            "HTTP 200 中实际承载的 gateway error payload",
            "metadata-only chunk",
            "U+2028/U+2029",
            "warmup/cooldown",
            "synthetic_agentic",
            "Time to First User Token（TFUT）",
            "server_usage",
            "Model Runner V2",
            "sharded_rdt",
            "Mamba prefix caching",
            "VLLM_ALLREDUCE_USE_FLASHINFER=0",
            "PD Handoff Latency",
            "reasoning output 可作为首个有效输出",
            "requests` 提升到 `2.33.0",
            "v0.30.1rc0",
            "audio_transcription",
            "--per-chunk-usage",
            "telemetry_source_url",
            "WARMUP_ISOLATION_",
            "Kubernetes native execution（beta）",
            "CUDA 12 lane",
            "--sampling-mask-max-tokens",
            "msgspec.Struct",
            "--enable-response-store",
            "gptq_marlin",
            "WatchEngineState",
            "tag object `d158602ff1d2cb953196c95158c488d503d2470c`",
            "--load-format ipc_cache",
            "--enable-scale-out",
            "HiSparseConnector",
            "`g_idx`",
            "torchaudio",
            "stop_model(ollamabin, model_name)",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, markdown_text)

    def test_render_benchmark_doc_uses_refreshed_toc_mermaid_and_links(self):
        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "AI-Inference-Deep-Dive.md"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            rendered_doc = dict(doc)
            rendered_doc["dst"] = str(Path(tmpdir) / "benchmark.html")
            serve_docs.render_doc(rendered_doc)
            html = Path(rendered_doc["dst"]).read_text(encoding="utf-8")

        self.assertIn(
            '<a href="#benchmark-sglang-bench">', html
        )
        self.assertIn(
            '<a href="#benchmark-vllm-bench">', html
        )
        self.assertIn('<div class="mermaid">', html)
        self.assertNotIn('class="language-mermaid"', html)
        self.assertIn("e00930c5489053f26d86b179cee0d087f846acbb", html)
        self.assertIn("db9527a46873454610df6dbedf79a36d6bf1a7f6", html)

    def test_refreshed_stable_release_commits_are_pinned(self):
        docs_dir = Path(__file__).resolve().parent
        expected_commits = {
            ("E2B-Deep-Dive.md", "component"): (
                "f32ee8a2a50052f32e3632ceb451111a98dd5104",
                "62a17dfc3f11439d1d06bfb9bb515eadc5adfcd3",
                "807cc37107bd7c012115afac9fa9c3b77b8365c2",
            ),
            ("Teleport-Deep-Dive.md", "component"): (
                "ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d",
                "5c5ee3f2e300ff01d305c3fe9301fe68ec1ad934",
                "5cd94927fee53f35a2bbd77797cc9524094bff78",
            ),
            ("Multica-Deep-Dive.md", "component"): (
                "7ab92d7622ecd81d179a8d83ae2dea74835a5069",
            ),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'gpu-operator'): (
                "5a9c8a8b3f5bac7fb06ad3c2a05771fceb8b4832",
            ),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'hami'): (
                "4707fb02c91c545bc7343ce26dba4c32919f9a3e",
            ),
            ('AI-Inference-Deep-Dive.md', 'dynamo'): (
                "2093662a4d4e5fd318732935213dde08dc7be818",
                "ac6d03a87a550c8188c3ed59f187b90d4f0554f5",
            ),
            ('AI-Inference-Deep-Dive.md', 'mooncake'): (
                "719735896c86b56fabec6cf3e825fb2ea640597a",
            ),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'k8s-scheduler'): (
                "f78e722310e50bcaca9276be22276d9e91d91308",
            ),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'k8s-history'): (
                "f78e722310e50bcaca9276be22276d9e91d91308",
            ),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'ai-schedulers'): (
                "296ec3db567abbe36b65a63695710e3d3f3d0bdb",
                "e33b8353e66dd6ed86fd4913660f88f8dbd17955",
                "279f61c6d55b20bd47a43f2560c1b4f646a55547",
                "41f27d567fb5bdaf2cab01e1caaf48f7e266eefb",
            ),
            ('AI-Inference-Deep-Dive.md', 'benchmark'): (
                "794f8bb75f8582f22e412d7e650fc71ca2a3d21a",
                "291a6e609c3eb52d6eadcedecc7a056e396cd5eb",
                "5804ea6b7ebd2bfceff29cf113311ed3af95146e",
                "498027686e6e3cf4eb32405a3fd21c65ff9237f1",
                "e00930c5489053f26d86b179cee0d087f846acbb",
                "db9527a46873454610df6dbedf79a36d6bf1a7f6",
                "9e441efe48756928e453ff26694d6e5af1a9c71d",
            ),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'kserve'): (
                "d1482554fc4f66dd41aee70e01f5174e24f265bd",
                "bb22cc477a6bd317bb2c7e357a85efcab8c7462a",
            ),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'volcano-upgrade'): (
                "41f27d567fb5bdaf2cab01e1caaf48f7e266eefb",
            ),
        }
        for (filename, component), commits in expected_commits.items():
            markdown_text = (docs_dir / filename).read_text(encoding="utf-8")
            for commit in commits:
                with self.subTest(document=filename, commit=commit):
                    self.assertIn(commit, markdown_text)

    def test_annotated_tags_distinguish_tag_objects_from_source_commits(self):
        docs_dir = Path(__file__).resolve().parent
        cases = {
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'k8s-scheduler'): (
                "d2b770f4c94636a992534a8d3156b6b2d8e82ac3",
                "f78e722310e50bcaca9276be22276d9e91d91308",
            ),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'volcano-upgrade'): (
                "b4ad252f3fd42c766d11d204e97622cddbbe4bd5",
                "41f27d567fb5bdaf2cab01e1caaf48f7e266eefb",
            ),
            ("E2B-Deep-Dive.md", "component"): (
                "b3832ed88cb8acc57cc5e81072f551d52f14b32f",
                "807cc37107bd7c012115afac9fa9c3b77b8365c2",
            ),
            ("Multica-Deep-Dive.md", "component"): (
                "0854695681139a5b0dce03aaf3583752a65409ed",
                "7ab92d7622ecd81d179a8d83ae2dea74835a5069",
            ),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'ai-schedulers'): (
                "b0fbbfe44ff20ee7f74cc0485c1a6812fe999a93",
                "296ec3db567abbe36b65a63695710e3d3f3d0bdb",
            ),
        }
        docs_by_src = {Path(doc["src"]).name: doc for doc in serve_docs.DOCS}

        for (filename, component), (tag_object, source_commit) in cases.items():
            markdown_text = (docs_dir / filename).read_text(encoding="utf-8")
            with self.subTest(document=filename):
                self.assertIn(tag_object, markdown_text)
                self.assertIn(source_commit, markdown_text)
                if tag_object in docs_by_src[filename]["footer"]:
                    self.assertIn(tag_object, docs_by_src[filename]["footer"])
                else:
                    self.assertNotIn(tag_object[:7], docs_by_src[filename]["footer"])
                self.assertIn(source_commit, docs_by_src[filename]["footer"])

    def test_lightweight_release_tags_point_directly_to_current_sources(self):
        docs_dir = Path(__file__).resolve().parent
        markdown_text = (docs_dir / "Kubernetes-AI-Platform-Deep-Dive.md").read_text(
            encoding="utf-8"
        )
        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "Kubernetes-AI-Platform-Deep-Dive.md"
        )
        for version, source_commit in (
            (
                "v0.1.0-alpha.16",
                "e33b8353e66dd6ed86fd4913660f88f8dbd17955",
            ),
            (
                "v0.18.6",
                "279f61c6d55b20bd47a43f2560c1b4f646a55547",
            ),
        ):
            with self.subTest(version=version):
                self.assertIn(source_commit, markdown_text)
                self.assertIn(source_commit, doc["footer"])
                self.assertIn("lightweight tag", markdown_text)

    def test_current_cards_exclude_superseded_primary_baselines(self):
        docs_by_src = {Path(doc["src"]).name: doc for doc in serve_docs.DOCS}
        expected = {
            ('AI-Inference-Deep-Dive.md', 'mooncake'): ("v0.3.13.post1", "v0.3.12.post1"),
            ('AI-Inference-Deep-Dive.md', 'dynamo'): ("Dynamo v1.5.1", "Dynamo v1.4.2"),
            ("Teleport-Deep-Dive.md", "component"): ("Teleport v18.10.0", "Teleport v19"),
            ("E2B-Deep-Dive.md", "component"): ("E2B Infra 2026.30", "E2B Infra 2026.29"),
            ("Multica-Deep-Dive.md", "component"): ("Multica v0.6.2", "Multica v0.4.44"),
            ('AI-Inference-Deep-Dive.md', 'benchmark'): ("vLLM v0.31.0", "vLLM v0.29.0"),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'ai-schedulers'): (
                "Kueue v0.20.2",
                "Kueue v0.19.4",
            ),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'ai-schedulers-grove'): (
                "Grove alpha.16",
                "Grove alpha.15",
            ),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'ai-schedulers-kai'): (
                "KAI-Scheduler v0.18.6",
                "KAI-Scheduler v0.18.5",
            ),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'kserve'): ("KServe v0.21.0", "KServe v0.20.0"),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'k8s-scheduler'): (
                "Kubernetes v1.37.1",
                "Kubernetes v1.37.0",
            ),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'volcano-upgrade'): (
                "v1.8.2 → v1.16.0",
                "v1.8.2 → v1.15.1",
            ),
            ('Kubernetes-AI-Platform-Deep-Dive.md', 'gpu-operator'): (
                "GPU Operator v26.7.2",
                "GPU Operator v26.7.1",
            ),
        }
        for (filename, component), (current, superseded) in expected.items():
            with self.subTest(document=filename):
                self.assertIn(current, docs_by_src[filename]["meta"])
                self.assertNotIn(superseded, docs_by_src[filename]["meta"])

    def test_refreshed_release_behavior_is_documented(self):
        docs_dir = Path(__file__).resolve().parent
        mooncake_text = (docs_dir / "AI-Inference-Deep-Dive.md").read_text(
            encoding="utf-8"
        )
        kai_text = (docs_dir / "Kubernetes-AI-Platform-Deep-Dive.md").read_text(
            encoding="utf-8"
        )

        for required_text in (
            "v0.3.13.post1@719735896c86b56fabec6cf3e825fb2ea640597a",
            "TCP connection pool 默认开启",
            "NVMe KV",
            "batch-record OpLog",
            "N-D logical weight transfer planner",
            "MOONCAKE_OFFSET_PERSIST_MODE",
            "PollRemoveAll",
            "cache_salt",
            "MooncakeBundleTransfer",
            "10000ms",
        ):
            with self.subTest(document="Mooncake", required_text=required_text):
                self.assertIn(required_text, mooncake_text)

        for required_text in (
            "segmented elastic PyTorchJob",
            "mandatorySegments",
            "MinAvailable=0",
            "minReplicas",
            "kai.scheduler/preemption-delay",
            "kai.scheduler/last-eviction-timestamp",
            "不能通过 preempt、reclaim 或 consolidation 驱逐别人",
            "DRA-backed extended resources",
            "v0.20.1@5922dc7d1a4661d3fc43d60943f92a775c892bdc",
            "tag，但它没有对应的正式 GitHub Release",
            "不能仅按 tag 排序",
            "不替代上表的正式 v0.18.6",
            "hierarchical gang floors",
            "同名 PodGroup 按 Kubernetes namespace 隔离",
            "releasing Pods 不再阻塞 required inter-pod anti-affinity",
            "不请求 GPU 的 Pod 不再获得 GPU-sharing node score",
        ):
            with self.subTest(document="KAI-Scheduler", required_text=required_text):
                self.assertIn(required_text, kai_text)

        dynamo_text = (docs_dir / "AI-Inference-Deep-Dive.md").read_text(
            encoding="utf-8"
        )
        for required_text in (
            "v1.5.1@2093662a4d4e5fd318732935213dde08dc7be818",
            "nixl==1.3.2",
            "EFA Installer `1.49.0`",
            "EFA Installer `1.50`",
            "libfabric `2.4.0amzn5.0`",
            "Lost connection with prefill instance",
            "空 HTTP 200/零 token",
            "ModelExpress 独立稳定版 `v0.7.0",
            "/v1/classify",
            "/v1/pooling",
            "logprob_token_ids",
            "libnixl_capi.so",
            "protobuf 6 runtime",
            "checkpoint_format=\"MX\"",
            "reshard-refit",
            "不做全量 gather",
            "per-shard digest",
            "Prometheus per-RPC",
            "S3 成为与 HuggingFace、NGC、GCS 并列的一等 provider",
            "cluster-wide metadata RBAC",
            "异构 CUDA/XPU source",
            "reservation replay",
            "sequenced KV relay",
            "endpoint-scoped event transport",
            "tenant cache salt",
            "/inference/v1/generate",
            "tokenizer prefix cache 在 v1.4.0 默认开启",
            "NIXL RDMA 多节点分离",
            "modality-aware routing",
            "自定义 vision encoder",
            "Omni realtime worker",
            "Spica",
            "request trace",
            "SATF",
            "G1 Mocker",
            "SGLang radix scheduling",
            "rollout strategy",
            "v1alpha1 → v1beta1",
            "shadow-engine failover",
            "XPU 场景有 DRA 示例",
            "standalone EPP",
            "dynamo.request.trace.v1",
            "OTLP sink",
            "allowlisted headers",
            "DYN_SELF_HOST_METADATA",
            "NATS subchart",
            "KVBM | v1.4.0 **deprecated**",
            "agg_kvbm.yaml",
        ):
            with self.subTest(document="Dynamo", required_text=required_text):
                self.assertIn(required_text, dynamo_text)

        dynamo_doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "AI-Inference-Deep-Dive.md"
        )
        self.assertIn("Dynamo v1.5.1", dynamo_doc["meta"])
        self.assertIn("source@2093662", dynamo_doc["meta"])
        self.assertIn(
            "2093662a4d4e5fd318732935213dde08dc7be818", dynamo_doc["footer"]
        )
        self.assertNotIn(
            "a49702e4432e7fa43cbc88175bddb31604340f19", dynamo_text
        )

    def test_latest_upstream_release_behavior_and_migration_boundaries_are_documented(self):
        docs_dir = Path(__file__).resolve().parent
        kubernetes_text = (docs_dir / "Kubernetes-AI-Platform-Deep-Dive.md").read_text(
            encoding="utf-8"
        )
        e2b_text = (docs_dir / "E2B-Deep-Dive.md").read_text(encoding="utf-8")

        for required_text in (
            "v26.7.2",
            "DRA Driver for NVIDIA GPUs 升为 `v0.5.1`",
            "app.kubernetes.io/component",
            "OpenShift DRA/MPS",
            "NVIDIA_GPU_MEMORY_LIMIT",
            "v0.20.2@296ec3db567abbe36b65a63695710e3d3f3d0bdb",
            "KueueViz",
            "StatefulSet 与 LeaderWorkerSet",
            "negative Pod overhead",
            "Fair Sharing",
            "role-hash",
            "PodIntegrationVerifyRoleRequests",
            "TAS 与 WebSocket/RBAC",
            "v0.1.0-alpha.16@e33b8353e66dd6ed86fd4913660f88f8dbd17955",
            "Kueue prebuilt workload backend",
            "reject queue label",
            "scheduler profile",
            "v0.18.6@279f61c6d55b20bd47a43f2560c1b4f646a55547",
            "per-worker score map",
            "replacement subgroup",
            "terminal BindRequest",
            "reservation",
            "v1.16.0@41f27d567fb5bdaf2cab01e1caaf48f7e266eefb",
            "NamespaceQueue",
            "fairshare",
            "Unschedulable Job Cache",
            "HyperNode",
            "Kubernetes 1.36",
            "DRA scoring",
        ):
            with self.subTest(document="Kubernetes", required_text=required_text):
                self.assertIn(required_text, kubernetes_text)

        for required_text in (
            "v1.0.7@807cc37107bd7c012115afac9fa9c3b77b8365c2",
            "--auth-token-sha256",
            "Authorization: Bearer",
            "`128+n`",
            "`137`",
            "logging.basicConfig",
            "WarmPool scheduling gate",
            "ProcessHandle",
            "terminated Pod",
        ):
            with self.subTest(document="E2B", required_text=required_text):
                self.assertIn(required_text, e2b_text)

    def test_scheduler_release_snapshots_and_patch_boundaries_are_documented(self):
        docs_dir = Path(__file__).resolve().parent
        ai_text = (docs_dir / "Kubernetes-AI-Platform-Deep-Dive.md").read_text(
            encoding="utf-8"
        )
        native_text = (
            docs_dir / "Kubernetes-AI-Platform-Deep-Dive.md"
        ).read_text(encoding="utf-8")
        volcano_text = (
            docs_dir / "Kubernetes-AI-Platform-Deep-Dive.md"
        ).read_text(encoding="utf-8")

        ai_doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "Kubernetes-AI-Platform-Deep-Dive.md"
        )
        volcano_doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name
            == "Kubernetes-AI-Platform-Deep-Dive.md"
        )

        self.assertIn("KAI-Scheduler v0.18.6", ai_doc["meta"])
        self.assertIn("prerelease", ai_text)
        self.assertIn("Kueue v0.20.2", ai_doc["meta"])
        self.assertIn("Grove alpha.16", ai_doc["meta"])
        self.assertIn("Volcano v1.16.0", ai_doc["meta"])
        self.assertIn("v1.8.2 → v1.16.0", volcano_doc["meta"])
        for revision in (
            "1462fb7b4835970708717456e3aed85e697ec2eb",
            "f5258704d7ef5bda28f31ba51950cdea9adbe921",
            "c2050e3debe58dbcdf9bb75b667799eec9409513",
        ):
            self.assertIn(revision, volcano_text)
        self.assertIn(
            "master@f5258704d7ef5bda28f31ba51950cdea9adbe921", ai_text
        )
        self.assertIn(
            "https://github.com/volcano-sh/website/tree/"
            "f5258704d7ef5bda28f31ba51950cdea9adbe921",
            ai_text,
        )
        self.assertNotIn(
            "master@aee652b985d25e33f59f6112e857627784b741ca", ai_text
        )
        self.assertNotIn(
            "https://github.com/volcano-sh/website/tree/"
            "aee652b985d25e33f59f6112e857627784b741ca",
            ai_text,
        )

        for required_text in (
            "OnDemand PVC informer race",
            "NeedContinueAllocating",
            "DRA count saturating arithmetic",
            "golang.org/x/crypto",
            "scalar resource milli-unit",
            "GHSA-j38h-7pfq-cxmw",
            "常数时间 quantity multiplication",
            "reclaim / preempt",
            "terminating PodGroup",
        ):
            self.assertIn(required_text, volcano_text)

        self.assertIn("KAI-Scheduler v0.18.6", native_text)
        self.assertIn("Kueue v0.20.2", native_text)
        self.assertIn("Volcano v1.16.0", native_text)
        self.assertIn("preemption delay", native_text)
        self.assertIn("DRADeviceCompatibilityGroups", native_text)
        self.assertIn("5922dc7d1a4661d3fc43d60943f92a775c892bdc", ai_text)
        self.assertIn("没有对应的正式 GitHub Release", ai_text)
        self.assertIn("v0.1.0-alpha.12", ai_text)
        self.assertIn("PodGangMap", ai_text)
        self.assertIn("LastScheduled", ai_text)
        self.assertIn("保留其他 controller 已写入的 scheduling gate", ai_text)

        for required_text in (
            "f0e95cea51b5591e0177fbe0fa06a299f36db548",
            "e28d01afc0aae90ec5ad8f0bc00ee6ab9294b11b",
            "TASCacheTopologyTree",
            "SchedulerLibraryIntegration",
            "PrioritizePreemptorWorkloads",
            "ValidateRayAndSparkJobUpdates",
            "is-group-workload",
            "v0.19.1 补丁升级前必读",
            "`LWSImmutableGroupSize` 默认开启",
            "关闭会同时恢复已知配额绕过",
            "`TASValidateWorkloadSliceSize`",
            "`TASRecomputeAssignmentWithinSchedulingCycle=false`",
            "`WorkloadValidateResourcesAreNonNegative`",
            "scheduler 实际会分配的 DeviceClass",
            "小于一个 milli-unit",
            "`int64`/`int32` wrap",
            "`PreserveFlavorScanProgress`",
            "`RecomputeAssignmentUponPreemptionTargetsOverlap`",
            "留在 `SchedulingGated`",
            "resourceNames",
            "unlimited quota 报为 `+Inf`",
            "不会替代上一节的 minor API",
            "TASGroupedPodSetSlicing",
            "MultiKueueReuseClientConnectionConfigForWorkers",
            "共享一个 rate limiter",
            "RuntimeClass overhead",
            "StatefulSet scale-to-zero",
            "ReclaimablePods",
            "v0.20.0-rc.1",
            "TASPartialSlices",
            "Spark 接受的 Java 格式",
            "384Mi",
            "Load` 方法签名改为返回",
            "TASLeaderPodSetFeasibility",
            "NvFractions GPU sharing",
            "gpu-compute.mode",
            "global.fipsMode",
            "gpujoborder",
        ):
            with self.subTest(document="Kueue", required_text=required_text):
                self.assertIn(required_text, ai_text)

    def test_e2b_get_host_private_ingress_auth_is_documented(self):
        docs_dir = Path(__file__).resolve().parent
        markdown_text = (docs_dir / "E2B-Deep-Dive.md").read_text(encoding="utf-8")

        for required_text in (
            "https://<port>-<sandbox-id>.<sandbox-domain>",
            "allowPublicTraffic=false",
            "e2b-traffic-access-token",
            "缺失或错误均返回 `403`",
            "trafficAccessToken",
            "envdAccessToken",
            "SANDBOX_ACCESS_TOKEN_HASH_SEED",
            "HMAC-SHA256",
            "只有校验通过才允许自动恢复",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, markdown_text)

        self.assertIn(
            "https://github.com/e2b-dev/infra/blob/"
            "f32ee8a2a50052f32e3632ceb451111a98dd5104/"
            "packages/orchestrator/pkg/proxy/proxy.go",
            markdown_text,
        )
        self.assertIn(
            "https://github.com/e2b-dev/infra/blob/"
            "f32ee8a2a50052f32e3632ceb451111a98dd5104/"
            "tests/integration/internal/tests/proxies/traffic_access_token_test.go",
            markdown_text,
        )
        self.assertIn(
            "https://github.com/e2b-dev/e2b/blob/"
            "62a17dfc3f11439d1d06bfb9bb515eadc5adfcd3/"
            "packages/js-sdk/src/sandbox/index.ts",
            markdown_text,
        )

    def test_e2b_header_routing_contract_is_documented(self):
        docs_dir = Path(__file__).resolve().parent
        markdown_text = (docs_dir / "E2B-Deep-Dive.md").read_text(encoding="utf-8")
        header_section = markdown_text.split(
            "#### 4.2.1 Host 与 Header 两种寻址方式", maxsplit=1
        )[1].split("#### 4.2.2 Public 与 Private ingress", maxsplit=1)[0]

        for required_text in (
            "E2b-Sandbox-Id",
            "E2b-Sandbox-Port",
            "`sandbox.<domain>`",
            "字面量 `localhost`、任意 IP",
            "必须成对提供",
            "回退到 Host 解析",
            "会忽略它们，以 Host 中的端口和 Sandbox ID 为准",
            "路由 Header 不是凭证，不提供认证或授权",
            "e2b-traffic-access-token",
            "Client Proxy 和 Orchestrator Proxy 调用同一个目标解析函数",
            "SDK 自己发往 envd 的请求自动附加官方路由 Header",
            "Infra 2026.30 没有名为 Router 的独立服务",
            "http://<orchestrator-ip>:5007",
            "orch-accepts-combined-host",
            "httputil.ReverseProxy",
            "没有独立的 E2B WebSocket handler",
            "不调用 `SetXForwarded()`",
            "`610s`",
            "`620s`",
            "sandbox-max-incoming-connections",
            "按 Sandbox lifecycle 计数",
            "超限返回 `429`",
            "E2B 固定版本不支持 `X-Sandbox-Namespace`",
            "Agent Sandbox v1.0.7",
            "b3832ed88cb8acc57cc5e81072f551d52f14b32f",
            "preview=true",
            "Docker image 或 guest 应用不需要解析路由 Header",
            "它不会启动 guest 服务",
            "镜像仍必须自行在所选端口实际运行一个可访问的服务",
            "Header 不会替应用启动服务",
            "这不是 E2B 可用调用示例",
            "不绝对要求所有服务监听 `0.0.0.0`",
            "envd 每 `1s` 扫描 loopback 上的 TCP listener",
            "首次连接可能有短暂就绪延迟",
            "不得用于身份认证或授权",
            "默认 allow-all",
            "scoped-token",
            "raw escaped path 保真",
            "`scope.raw_path`",
            "`%2E` / `%2E%2E`",
            "只属于 Agent Sandbox 的旧 Python Router",
            "两者都不要求进入 Pod 的容器镜像解析 `X-Sandbox-Port`",
            "`X-Sandbox-Port` 不是 E2B 的兼容 Header",
            "在请求进入 Client Proxy 前成对转换",
            "`v1alpha1` 和 conversion webhook 基础设施均被移除",
            "先 `kubectl apply -f helm/crds/`",
            "sandboxd",
            "Files.WriteReader",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, header_section)

        self.assertIn(
            "这一固定版本不支持 `X-Sandbox-ID` 和 `X-Sandbox-Port`，"
            "它们不是兼容别名",
            header_section,
        )
        self.assertNotIn('-H "X-Sandbox-ID:', header_section)
        self.assertNotIn('-H "X-Sandbox-Port:', header_section)

        infra_commit_base = (
            "https://github.com/e2b-dev/infra/blob/"
            "f32ee8a2a50052f32e3632ceb451111a98dd5104/"
        )
        for source_path in (
            "packages/shared/pkg/proxy/host.go",
            "packages/shared/pkg/proxy/host_test.go",
            "packages/shared/pkg/proxy/handler.go",
            "packages/shared/pkg/proxy/pool/client.go",
            "packages/shared/pkg/proxy/proxy.go",
            "packages/shared/pkg/proxy/pool/pool.go",
            "packages/shared/pkg/proxy/proxy_test.go",
            "packages/shared/pkg/connlimit/limiter.go",
            "packages/shared/pkg/featureflags/flags.go",
            "packages/envd/internal/port/forward.go",
            "packages/envd/main.go",
            "tests/integration/internal/tests/envd/localhost_bind_test.go",
        ):
            with self.subTest(source_path=source_path):
                self.assertIn(infra_commit_base + source_path, markdown_text)

        sdk_commit_base = (
            "https://github.com/e2b-dev/e2b/blob/"
            "62a17dfc3f11439d1d06bfb9bb515eadc5adfcd3/"
        )
        for source_path in (
            "packages/js-sdk/src/connectionConfig.ts",
            "packages/js-sdk/src/sandbox/index.ts",
            "packages/python-sdk/e2b/connection_config.py",
            "packages/python-sdk/e2b/api/client_sync/__init__.py",
            "packages/python-sdk/e2b/envd/client_shared.py",
            "packages/python-sdk/e2b/sandbox_sync/main.py",
        ):
            with self.subTest(source_path=source_path):
                self.assertIn(sdk_commit_base + source_path, markdown_text)

        agent_sandbox_commit_base = (
            "https://github.com/kubernetes-sigs/agent-sandbox/blob/"
            "807cc37107bd7c012115afac9fa9c3b77b8365c2/"
        )
        for source_path in (
            "clients/python/agentic-sandbox-client/sandbox-router/sandbox_router.py",
            "docs/api-migration-guide.md",
            "packages/sandboxd/USER_GUIDE.md",
            "sandbox-router/README.md",
            "sandbox-router/proxy/browsersession.go",
            "sandbox-router/proxy/headers.go",
            "sandbox-router/proxy/proxy.go",
            "sandbox-router/authz/authorizer.go",
            "sandbox-router/authz/scopedtoken_v2.go",
            "sandbox-router/deploy/deployment.yaml",
            "examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py",
        ):
            with self.subTest(source_path=source_path):
                self.assertIn(agent_sandbox_commit_base + source_path, markdown_text)

        for required_text in (
            "pyqwest transport",
            "同步 Sandbox 也只创建一个普通 envd HTTP client",
            "60 秒 idle-read bound",
            "best-effort `kill()`",
            "`SandboxError` / `SandboxException`",
            "不代表 Infra 2026.30 新增了控制面事务或原子创建语义",
            "IAM workload identity",
            "Secret.iamToken",
            "iam_token",
            "callback placeholder",
            "token name",
            "http2",
            "具体客户端接口仍固定在未发布 SDK 主线",
            "WarmPool status",
            "ServiceMonitor",
            "PodScheduled image",
            "Pi 示例",
            "Podman kind",
            "不能回填成 E2B",
            "删除 deprecated E2B access-token authentication",
            "删除 database read-replica support",
            "`memory: false`",
            "LOGS_READ_CONFIG",
            "cluster registration",
            "live upgrade",
            "authz.AuthorizationTarget",
            "agent-sandbox-system",
            "Ed25519",
            "ConnectivityInClusterService",
            "FleetConfig.adopt_existing=True",
            "Infra `2026.30` 是 lightweight tag",
            "Agent Sandbox v1.0.7",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, markdown_text)

        self.assertIn(
            "v1.0.3（2026-09-17 发布）与 v1.0.4（2026-09-24 发布）",
            markdown_text,
        )
        self.assertNotIn("v1.0.3（2026-09-26 发布）", markdown_text)

        self.assertNotIn(
            "88f41f392722a2f56971ea6c1084f0fc574ef1f4", markdown_text
        )
        self.assertNotIn(
            "108be73b56d9bff55a0cc626c9e89100d797a9bc", markdown_text
        )

    def test_e2b_self_hosted_quota_and_billing_boundaries_are_documented(self):
        docs_dir = Path(__file__).resolve().parent
        markdown_text = (docs_dir / "E2B-Deep-Dive.md").read_text(encoding="utf-8")

        for required_text in (
            "第十章：自托管配额与计费架构",
            "team_limits",
            "quota_policy",
            "tenant_policy_binding",
            "quota_override",
            "quota_reservation",
            "usage_events",
            "usage_intervals",
            "price_book",
            "ledger_entries",
            "budgets",
            "reconciliation_runs",
            "execution_id",
            "transactional outbox",
            "Usage Ledger",
            "Price Book",
            "fail-open",
            "fail-closed",
            "reconciliation",
            "不能把官方云公开价格写成自托管默认单价",
            "不能直接充当唯一财务账本",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, markdown_text)

        self.assertNotRegex(
            markdown_text,
            r"github[.]com/e2b-dev/infra/(?:blob|tree)/(?:main|master)/",
        )

        infra_revisions = set(
            re.findall(
                r"github[.]com/e2b-dev/infra/(?:blob|tree)/([^/)]+)",
                markdown_text,
            )
        )
        self.assertEqual(
            infra_revisions,
            {"f32ee8a2a50052f32e3632ceb451111a98dd5104"},
        )

        commit_base = (
            "https://github.com/e2b-dev/infra/blob/"
            "f32ee8a2a50052f32e3632ceb451111a98dd5104/"
        )
        source_paths = (
            "packages/db/migrations/20251011200438_create_addons_table.sql",
            "packages/db/migrations/20260702120000_add_events_ttl_days.sql",
            "packages/dashboard-api/internal/handlers/teams_list.go",
            "packages/api/internal/sandbox/reservations/redis/scripts.go",
            "packages/api/internal/middleware/ratelimit/ratelimit.go",
            "packages/api/internal/handlers/sandbox.go",
            "packages/shared/pkg/events/sandbox.go",
            "packages/orchestrator/pkg/server/sandboxes.go",
            "packages/clickhouse/migrations/20250725223340_add_sandbox_events_local.sql",
            "packages/clickhouse/migrations/20260702120000_add_sandbox_events_ttl_days.sql",
            "packages/clickhouse/pkg/events/delivery.go",
            "packages/api/internal/orchestrator/analytics.go",
        )
        for source_path in source_paths:
            with self.subTest(source_path=source_path):
                self.assertIn(commit_base + source_path, markdown_text)

        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "E2B-Deep-Dive.md"
        )
        for summary_term in (
            "filesystem-only resume",
            "workload identity",
            "Secrets",
            "团队配额",
            "bearer-token",
            "流式命令",
            "WarmPool",
        ):
            with self.subTest(summary_term=summary_term):
                self.assertIn(summary_term, doc["summary"])
        self.assertIn(
            "https://github.com/e2b-dev/infra/tree/"
            "f32ee8a2a50052f32e3632ceb451111a98dd5104",
            doc["footer"],
        )

    def test_e2b_2026_29_fork_contract_is_documented(self):
        docs_dir = Path(__file__).resolve().parent
        markdown_text = (docs_dir / "E2B-Deep-Dive.md").read_text(encoding="utf-8")

        for required_text in (
            "POST /sandboxes/{sandboxID}/fork",
            "每次请求只捕获一次完整内存状态",
            "原实例继续占一个槽",
            "每个 fork 通过正常 `startSandbox` 路径独立申请槽",
            "继承 snapshot 中的 egress/ingress",
            "按新 Sandbox ID 重新生成 envd access token",
            "部分 fork 可以成功",
            "sandbox_fork.go",
            "sandbox_fork_test.go",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, markdown_text)

    def test_render_e2b_quota_chapter_includes_toc_and_mermaid(self):
        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "E2B-Deep-Dive.md"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            rendered_doc = dict(doc)
            rendered_doc["dst"] = str(Path(tmpdir) / "e2b.html")
            serve_docs.render_doc(rendered_doc)
            html = Path(rendered_doc["dst"]).read_text(encoding="utf-8")

        self.assertIn(
            '<a class="toc-chapter" href="#第十章自托管配额与计费架构">',
            html,
        )
        self.assertIn("10.7 Usage Event、可靠账本与分析层", html)
        self.assertIn('<div class="mermaid">', html)
        self.assertIn("participant QS as Quota Service", html)
        self.assertNotIn('class="language-mermaid"', html)

    def test_kserve_v0_21_separates_release_and_unreleased_main(self):
        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "Kubernetes-AI-Platform-Deep-Dive.md"
        )
        markdown_text = Path(doc["src"]).read_text(encoding="utf-8")

        self.assertIn("KServe v0.21.0", doc["meta"])
        self.assertIn("master@bb22cc4", doc["meta"])
        self.assertIn("website@71c8b22", doc["meta"])
        for revision in (
            "d1482554fc4f66dd41aee70e01f5174e24f265bd",
            "bb22cc477a6bd317bb2c7e357a85efcab8c7462a",
            "71c8b22a05d6be72560b2cc326865930063cd0e8",
        ):
            self.assertIn(revision, markdown_text)

        self.assertIn("v0.21.0 v1alpha2 稳定 API", markdown_text)
        self.assertIn("示例使用顶层 `spec.kvCacheOffloading`", markdown_text)
        self.assertIn("`spec.router.route.group` / `weight`", markdown_text)
        self.assertIn("把上一轮全部“未发布 master”观察项正式纳入 release", markdown_text)
        self.assertIn("已被 `v0.21.0` 正式 Release 取代", markdown_text)
        for stable_feature in (
            "KV cache offloading",
            "LLMISVC traffic splitting 与 rollout",
            "路由与运行能力",
            "存储与模型源",
            "弹性与 TLS",
            "运行时与依赖",
            "AgentGateway 集成指南",
            "主线快照",
        ):
            self.assertIn(stable_feature, markdown_text)
        for required_text in (
            "`spec.rolloutStrategy.maxUnavailable` / `maxSurge`",
            "多节点 workload 若 `maxUnavailable=0`",
            "`PresetsCombined=False/InvalidRenderedConfig`",
            "只有 Ready canary 才进入 HTTPRoute/Ingress 权重计算",
            "`idleReplicaCount: 0`",
            "idle count 严格小于",
            "`oci+fetch://`",
            "`ms://` ModelScope storage provider",
            "依赖树的安全修复与 Gateway API Inference Extension 的 weighted `InferencePool` 后端选择测试随 release 固化",
            "versioned docs",
            "当前实现明确不支持 LLMInferenceService fetch",
            "P/D engine 的 NixlConnector",
            "LoRA adapter 的 LocalModelCache",
            "controller TLS 证书热重载",
            "KEDA v2.20.2",
            "Envoy AI Gateway v1.1.0、llm-d 0.10",
            "DRA `resourceClaims` 进入 ServingRuntime",
            "UDS tokenizer sidecar 被 vLLM render deployment 取代",
            "已在本版迁移到 `v1alpha2`",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, markdown_text)
        self.assertIn("不把它扩展为 v0.21.0 的兼容承诺", markdown_text)
        self.assertNotIn(
            "b15ac29c6443340e2f4389a8e376f65fbcf8c6ec", markdown_text
        )
        self.assertNotIn(
            "b561e05b36abcae07508a83eaf0244f153531c97", markdown_text
        )
        self.assertNotIn("b0eda63d2c105479140af8ec9149d992b7e44be5", markdown_text)
        self.assertNotIn("f8a0ac1c85c3d06e7f4a9b6872f2778a556c7886", markdown_text)

    def test_multica_doc_is_registered_and_rendered_on_index(self):
        docs_by_src = {Path(doc["src"]).name: doc for doc in serve_docs.DOCS}

        self.assertIn("Multica-Deep-Dive.md", docs_by_src)
        doc = docs_by_src["Multica-Deep-Dive.md"]
        self.assertEqual(Path(doc["dst"]).name, "Multica-Deep-Dive.html")
        self.assertEqual(doc["href"], "/Multica-Deep-Dive.html")
        self.assertEqual(doc["title"], "Agent 协作与编排：Multica")
        self.assertEqual(
            doc["meta"],
            "Multica v0.6.2 · source@7ab92d7 · main@7ab92d7 · 2026-10-16",
        )
        for summary_term in (
            "Issue 四类 lifecycle",
            "Triage",
            "Task/runs",
            "Agent/Runtime",
            "25 种 protocol family",
            "Codex usage/thread",
            "Channel",
            "Desktop",
            "Squad",
            "Autopilot",
            "无 Sandbox",
        ):
            with self.subTest(summary_term=summary_term):
                self.assertIn(summary_term, doc["summary"])
        self.assertIn(
            "https://github.com/multica-ai/multica/tree/"
            "7ab92d7622ecd81d179a8d83ae2dea74835a5069",
            doc["footer"],
        )
        self.assertIn("https://multica.ai/docs", doc["footer"])

        with tempfile.TemporaryDirectory() as tmpdir:
            original_index = serve_docs.INDEX
            serve_docs.INDEX = str(Path(tmpdir) / "index.html")
            try:
                serve_docs.render_index()
                html = Path(serve_docs.INDEX).read_text(encoding="utf-8")
            finally:
                serve_docs.INDEX = original_index

        self.assertIn("Agent 协作与编排：Multica", html)
        self.assertIn('/Multica-Deep-Dive.html', html)
        self.assertIn("Multica v0.6.2", html)
        self.assertIn("无 Sandbox", html)

    def test_multica_execution_and_security_contract_is_documented(self):
        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "Multica-Deep-Dive.md"
        )
        markdown_text = Path(doc["src"]).read_text(encoding="utf-8")

        for required_text in (
            "v0.6.2",
            "7ab92d7622ecd81d179a8d83ae2dea74835a5069",
            "0854695681139a5b0dce03aaf3583752a65409ed",
            "审校日期：2026-10-16",
            "MULTICA_IMAGE_TAG=v0.6.2",
            "没有强制的 Issue 状态转换图",
            "Task 完成不等于 Issue 完成",
            "Task 与目标 Runtime 固定绑定且不会自动迁移",
            "普通任务最多两次执行",
            "工具网络中断最多三次执行",
            "“仅运行”模式不自动重试",
            "`custom_env` 值会以明文 JSONB 存入 Multica 服务端 PostgreSQL 数据库",
            'sandbox_mode = "danger-full-access"',
            "--permission-mode bypassPermissions",
            "专用 Unix 用户",
            "容器内运行 daemon",
            "专用 VM",
            "/readyz",
            "企业微信多副本回复路由",
            "socket-owner relay",
            "自定义 Multica License，纳入 Apache 2.0 条款并附加托管服务、商业嵌入、品牌和署名条件",
            "Saved Issue Views",
            "Oh-My-Pi Runtime",
            "`multica chat history`",
            "dotenv 风格文本",
            "60 秒有效",
            "有界 keyset page",
            "10 秒 lock wait 上限",
            "不是文件系统隔离",
            "DeepSeek Harness",
            "`dsh`",
            "DEEPSEEK_API_KEY",
            "dsh --profile multica --probe",
            "25 种 protocol family",
            "`in_place`（默认）",
            "`worktree`",
            "agent/<agent>/<task>",
            "2000 个文件或 200 MiB",
            "capability 双重校验",
            "安全回退风险",
            "MULTICA_WORKSPACES_ROOT",
            "MULTICA_AGENT_TEMP_BASE",
            "AF_UNIX",
            "MULTICA_CODEX_FIRST_TURN_TIMEOUT",
            "严格小于",
            "owner-only API/CLI",
            "Private Skill Plugin V1",
            "multica.plugin/v1",
            "agent.skill.contribute",
            "multica plugin validate",
            "Kernel Policy",
            "不可运行的 CLI",
            "Hermes",
            "Windows",
            "manual rerun",
            "in-flight agent run",
            "recently created Issue",
            "runtime-local Skill",
            "binary supporting files",
            "immutable version",
            "custom provider",
            "Execution-root fencing",
            "exclusively claimed env root",
            "Workspace seats",
            "Plugin Public API v1",
            "durable scheduled hooks",
            "ZeroClaw",
            "华为云 CodeArts",
            "MULTICA_TASK_QUEUED_TTL",
            "Runtime 只是满并发而仍在线时，积压会继续保留",
            "`unstarted`",
            "`started`",
            "`closed`",
            "issue.triage_state",
            "Triage 没有 executor",
            "reserved `triage` status key",
            "cancelled 不再伪装成成功",
            "reasoning_output_tokens",
            "thread ID 读写同步",
            "DingTalk",
            "Lark bind session 跨 replica 共享",
            "desktop.json",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, markdown_text)

        for issue_status in (
            "backlog",
            "todo",
            "in_progress",
            "in_review",
            "done",
            "blocked",
            "cancelled",
        ):
            with self.subTest(issue_status=issue_status):
                self.assertIn(f"| `{issue_status}` |", markdown_text)
        for task_status in (
            "deferred",
            "queued",
            "dispatched",
            "waiting_local_directory",
            "running",
            "completed",
            "failed",
            "cancelled",
        ):
            with self.subTest(task_status=task_status):
                self.assertIn(f"| `{task_status}` |", markdown_text)

        self.assertIn("只有目标 Runtime 的心跳缺席超过", markdown_text)
        self.assertIn("修改负责人不会停止活动 Task", markdown_text)
        self.assertIn("修改 Issue 状态不会停止活动 Task", markdown_text)

    def test_multica_stable_evidence_links_are_pinned(self):
        markdown_text = Path("/data/Multica-Deep-Dive.md").read_text(
            encoding="utf-8"
        )
        stable_commit = "7ab92d7622ecd81d179a8d83ae2dea74835a5069"
        product_image = (
            "https://raw.githubusercontent.com/multica-ai/multica/"
            f"{stable_commit}/apps/docs/public/images/docs/workspace-overview.webp"
        )

        self.assertIn(product_image, markdown_text)
        self.assertIn(
            f"https://github.com/multica-ai/multica/blob/{stable_commit}/"
            "server/pkg/agent/agent.go",
            markdown_text,
        )
        self.assertNotRegex(
            markdown_text,
            r"https://github\.com/multica-ai/multica/(?:blob|tree)/(?:main|master)(?:/|\))",
        )
        self.assertNotRegex(
            markdown_text,
            r"https://raw\.githubusercontent\.com/multica-ai/multica/(?:main|master)/",
        )
        self.assertIn("`v0.6.2` 是本轮审校采用的最新正式 release", markdown_text)
        self.assertIn("未发布主线和 tag-only 证据不反推为稳定能力", markdown_text)
        self.assertNotIn("0dfaac266eed3b7ac710de33d8207e4f71cfb20b", markdown_text)
        self.assertNotIn("c7f259c70a60bff30011c403fada79ab382f608a", markdown_text)

    def test_render_multica_doc_includes_toc_mermaid_and_product_image(self):
        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "Multica-Deep-Dive.md"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            rendered_doc = dict(doc)
            rendered_doc["dst"] = str(Path(tmpdir) / "multica.html")
            serve_docs.render_doc(rendered_doc)
            html = Path(rendered_doc["dst"]).read_text(encoding="utf-8")

        self.assertIn(
            '<a class="toc-chapter" href="#第十二章落地架构建议">',
            html,
        )
        self.assertIn(
            '<a class="toc-chapter" href="#附录-e官方文档与源码证据">',
            html,
        )
        self.assertGreaterEqual(html.count('<div class="mermaid">'), 5)
        self.assertIn("sequenceDiagram", html)
        self.assertIn("stateDiagram-v2", html)
        self.assertIn(
            "https://raw.githubusercontent.com/multica-ai/multica/"
            "7ab92d7622ecd81d179a8d83ae2dea74835a5069/"
            "apps/docs/public/images/docs/workspace-overview.webp",
            html,
        )
        self.assertNotIn('class="language-mermaid"', html)

    def test_new_release_behavior_boundaries_are_documented(self):
        docs_dir = Path(__file__).resolve().parent
        gpu_text = (docs_dir / "Kubernetes-AI-Platform-Deep-Dive.md").read_text(
            encoding="utf-8"
        )
        hami_text = (docs_dir / "Kubernetes-AI-Platform-Deep-Dive.md").read_text(encoding="utf-8")
        native_text = (
            docs_dir / "Kubernetes-AI-Platform-Deep-Dive.md"
        ).read_text(encoding="utf-8")
        kueue_text = (
            docs_dir / "Kubernetes-AI-Platform-Deep-Dive.md"
        ).read_text(encoding="utf-8")

        for required_text in (
            "GPUCluster",
            "ResourceClaim",
            "nvidia.com/gpu.deploy.client",
            "upgradePolicy",
            "hostPaths.kubeletRootDir",
            "NRI_MANAGEMENT_CDI_DEVICE_NAMESPACES",
            "595.91.07",
            "615.71.09",
            "NVIDIA_GPU_MEMORY_LIMIT",
            "v0.12.1",
            "v1.20.1",
            "v0.20.1",
            "v0.15.1",
            "4.6.1-1",
            "v0.19.3",
        ):
            with self.subTest(document="GPU Operator", required_text=required_text):
                self.assertIn(required_text, gpu_text)

        for required_text in (
            "Remove DRA components from HAMi main chart",
            "ascend-dra-driver",
            "init-container",
            "NodeLock",
            "gangScheduling",
            "dynamic allocation/deallocation",
            "mutex",
            "comma-separated",
            "NUMA",
            "Biren",
            "Mi300x",
            "vir05_1c_16g",
            "DRA components",
        ):
            with self.subTest(document="HAMi", required_text=required_text):
                self.assertIn(required_text, hami_text)

        for required_text in (
            "DRADeviceTaintRules",
            "scheduling.k8s.io/v1beta1",
            "v1alpha2` 在 v1.37 不再 serve",
            "DRAWorkloadResourceClaims` | Beta | **关**",
            "DRA device metadata API 在 v1.37 升为 `v1beta1`",
            "DRAResourceHealth",
            "DRADeviceCompatibilityGroups",
            "DRADerivedAttributes",
            "DRAOptionalNodeOperations",
            "DRAResourcePoolStatus",
            "DRANodeAllocatableResources",
            "SchedulerPreQueueingHints",
        ):
            with self.subTest(document="Kubernetes", required_text=required_text):
                self.assertIn(required_text, native_text)

        for required_text in (
            "TASCacheTopologyTree",
            "SchedulerLibraryIntegration",
            "PrioritizePreemptorWorkloads",
            "ValidateRayAndSparkJobUpdates",
            "is-group-workload",
            "AFS",
            "+Inf",
            "stale `status.nominatedClusterNames`",
        ):
            with self.subTest(document="Kueue", required_text=required_text):
                self.assertIn(required_text, kueue_text)

    def test_nvidia_gpu_operator_doc_is_registered(self):
        docs_by_src = {Path(doc["src"]).name: doc for doc in serve_docs.DOCS}

        self.assertIn("Kubernetes-AI-Platform-Deep-Dive.md", docs_by_src)

        doc = docs_by_src["Kubernetes-AI-Platform-Deep-Dive.md"]
        self.assertEqual(
            Path(doc["dst"]).name,
            "Kubernetes-AI-Platform-Deep-Dive.html",
        )
        self.assertEqual(doc["href"], "/Kubernetes-AI-Platform-Deep-Dive.html")
        self.assertEqual(doc["title"], "Kubernetes AI 平台深度文档")
        self.assertIn("v26.7.2", doc["meta"])
        self.assertIn("5a9c8a8", doc["meta"])
        self.assertIn(
            "https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.7/overview.html",
            doc["footer"],
        )
        self.assertIn(
            "https://github.com/NVIDIA/gpu-operator/tree/"
            "5a9c8a8b3f5bac7fb06ad3c2a05771fceb8b4832",
            doc["footer"],
        )
        self.assertIn(
            "https://github.com/NVIDIA/gpu-operator/releases/tag/v26.7.2",
            doc["footer"],
        )

    def test_render_index_includes_nvidia_gpu_operator_doc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_index = serve_docs.INDEX
            serve_docs.INDEX = str(Path(tmpdir) / "index.html")
            try:
                serve_docs.render_index()
                html = Path(serve_docs.INDEX).read_text(encoding="utf-8")
            finally:
                serve_docs.INDEX = original_index

        self.assertIn("Kubernetes AI 平台深度文档", html)
        self.assertIn('/Kubernetes-AI-Platform-Deep-Dive.html', html)
        self.assertIn("GPU Operator v26.7.2", html)

    def test_render_nvidia_gpu_operator_doc_includes_toc_and_mermaid(self):
        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "Kubernetes-AI-Platform-Deep-Dive.md"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            rendered_doc = dict(doc)
            rendered_doc["dst"] = str(Path(tmpdir) / "gpu-operator.html")
            serve_docs.render_doc(rendered_doc)
            html = Path(rendered_doc["dst"]).read_text(encoding="utf-8")

        self.assertIn(
            '<a href="#gpu-operator-定位与边界">',
            html,
        )
        self.assertIn(
            '<h4 id="gpu-operator-4-1-两个配置层不要混淆">3.4.1 两个配置层不要混淆</h4>',
            html,
        )
        self.assertIn(
            '<a href="#gpu-operator-故障排查方法">',
            html,
        )
        self.assertGreaterEqual(html.count('<div class="mermaid">'), 5)
        self.assertIn("flowchart TB", html)
        self.assertIn("flowchart LR", html)
        self.assertIn("sequenceDiagram", html)
        self.assertNotIn('class="language-mermaid"', html)

    def test_lustre_3fs_doc_is_registered(self):
        docs_by_src = {Path(doc["src"]).name: doc for doc in serve_docs.DOCS}

        self.assertIn("Lustre-3FS-Deep-Dive.md", docs_by_src)

        doc = docs_by_src["Lustre-3FS-Deep-Dive.md"]
        self.assertEqual(Path(doc["dst"]).name, "Lustre-3FS-Deep-Dive.html")
        self.assertEqual(doc["href"], "/Lustre-3FS-Deep-Dive.html")
        self.assertIn("Lustre", doc["title"])
        self.assertIn("3FS", doc["title"])

    def test_kubernetes_native_scheduler_doc_is_registered(self):
        docs_by_src = {Path(doc["src"]).name: doc for doc in serve_docs.DOCS}

        self.assertIn("Kubernetes-AI-Platform-Deep-Dive.md", docs_by_src)

        doc = docs_by_src["Kubernetes-AI-Platform-Deep-Dive.md"]
        self.assertEqual(
            Path(doc["dst"]).name,
            "Kubernetes-AI-Platform-Deep-Dive.html",
        )
        self.assertEqual(doc["href"], "/Kubernetes-AI-Platform-Deep-Dive.html")
        self.assertEqual(doc["title"], "Kubernetes AI 平台深度文档")
        self.assertIn("v1.37.1", doc["meta"])
        self.assertIn("f78e722", doc["meta"])
        self.assertIn(
            "https://kubernetes.io/docs/concepts/scheduling-eviction/",
            doc["footer"],
        )
        self.assertIn(
            "https://github.com/kubernetes/kubernetes/tree/f78e722310e50bcaca9276be22276d9e91d91308",
            doc["footer"],
        )

    def test_render_index_includes_kubernetes_native_scheduler_doc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_index = serve_docs.INDEX
            serve_docs.INDEX = str(Path(tmpdir) / "index.html")
            try:
                serve_docs.render_index()
                html = Path(serve_docs.INDEX).read_text(encoding="utf-8")
            finally:
                serve_docs.INDEX = original_index

        self.assertIn("Kubernetes AI 平台深度文档", html)
        self.assertIn('/Kubernetes-AI-Platform-Deep-Dive.html', html)
        self.assertIn("Kubernetes v1.37.1", html)
        self.assertIn("v1.37 DRA 扩展", html)
        self.assertIn("Workload/PodGroup v1beta1", html)

    def test_render_kubernetes_native_scheduler_doc(self):
        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "Kubernetes-AI-Platform-Deep-Dive.md"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            rendered_doc = dict(doc)
            rendered_doc["dst"] = str(Path(tmpdir) / "kube-scheduler.html")
            serve_docs.render_doc(rendered_doc)
            html = Path(rendered_doc["dst"]).read_text(encoding="utf-8")

        self.assertIn(
            '<a href="#k8s-scheduler-先明确-kube-scheduler-的边界">',
            html,
        )
        self.assertIn(
            '<h4 id="k8s-scheduler-3-1-两个周期与扩展点">2.3.1 两个周期与扩展点</h4>',
            html,
        )
        self.assertIn(
            '<a href="#k8s-scheduler-与五类-ai-调度项目对比">',
            html,
        )
        self.assertIn(
            '<h4 id="k8s-scheduler-8-2-dra-对象模型与-source-of-truth">2.8.2 DRA 对象模型与 source of truth</h4>',
            html,
        )
        self.assertIn(
            '<h4 id="k8s-scheduler-8-5-dynamicresources-插件调用链">2.8.5 DynamicResources 插件调用链</h4>',
            html,
        )
        self.assertIn(
            '<h4 id="k8s-scheduler-8-8-v1-37-1-feature-maturity-矩阵">2.8.8 v1.37.1 feature maturity 矩阵</h4>',
            html,
        )
        self.assertIn(
            '<h4 id="k8s-scheduler-9-2-workload-podgroup-与-pod-对象链">2.9.2 Workload PodGroup 与 Pod 对象链</h4>',
            html,
        )
        self.assertIn(
            '<h4 id="k8s-scheduler-9-4-podgroup-scheduling-cycle-源码路径">2.9.4 PodGroup scheduling cycle 源码路径</h4>',
            html,
        )
        self.assertIn(
            '<h4 id="k8s-scheduler-9-9-dra-与-gang-的联合链路">2.9.9 DRA 与 Gang 的联合链路</h4>',
            html,
        )
        self.assertGreaterEqual(html.count('<div class="mermaid">'), 13)
        self.assertIn("flowchart TB", html)
        self.assertIn("flowchart LR", html)
        self.assertIn("stateDiagram-v2", html)
        self.assertIn("sequenceDiagram", html)
        self.assertIn("resource.k8s.io/v1", html)
        self.assertIn("scheduling.k8s.io/v1beta1", html)
        self.assertNotIn("apiVersion: scheduling.k8s.io/v1alpha2", html)
        for extension_point in (
            "PreEnqueue",
            "PreFilter",
            "Filter",
            "Score",
            "Reserve",
            "PreBind",
            "Unreserve",
            "PostFilter",
        ):
            self.assertIn(extension_point, html)
        for feature_gate in (
            "DRAWorkloadResourceClaims",
            "DRANodeAllocatableResources",
            "DRAListTypeAttributes",
            "DRADeviceCompatibilityGroups",
            "DRADerivedAttributes",
            "DRAOptionalNodeOperations",
            "DRAResourcePoolStatus",
            "SchedulerPreQueueingHints",
        ):
            self.assertIn(feature_gate, html)
        self.assertIn("dra_grpc_operations_duration_seconds", html)
        self.assertNotIn("kubelet_dra_grpc_operations_duration_seconds", html)
        self.assertIn("Kubernetes-AI-Platform-Deep-Dive.html", html)
        self.assertNotIn('class="language-mermaid"', html)

    def test_kubernetes_ai_schedulers_doc_is_registered(self):
        docs_by_src = {Path(doc["src"]).name: doc for doc in serve_docs.DOCS}

        self.assertIn("Kubernetes-AI-Platform-Deep-Dive.md", docs_by_src)

        doc = docs_by_src["Kubernetes-AI-Platform-Deep-Dive.md"]
        self.assertEqual(
            Path(doc["dst"]).name,
            "Kubernetes-AI-Platform-Deep-Dive.html",
        )
        self.assertEqual(doc["href"], "/Kubernetes-AI-Platform-Deep-Dive.html")
        self.assertIn("AI 调度器", doc["summary"])
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

        self.assertIn("Kubernetes AI 平台深度文档", html)
        self.assertIn('/Kubernetes-AI-Platform-Deep-Dive.html', html)

    def test_volcano_upgrade_compatibility_doc_is_registered(self):
        docs_by_src = {Path(doc["src"]).name: doc for doc in serve_docs.DOCS}

        self.assertIn("Kubernetes-AI-Platform-Deep-Dive.md", docs_by_src)

        doc = docs_by_src["Kubernetes-AI-Platform-Deep-Dive.md"]
        self.assertEqual(
            Path(doc["dst"]).name,
            "Kubernetes-AI-Platform-Deep-Dive.html",
        )
        self.assertEqual(doc["href"], "/Kubernetes-AI-Platform-Deep-Dive.html")
        self.assertIn("Volcano", doc["summary"])
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

        self.assertIn("Kubernetes AI 平台深度文档", html)
        self.assertIn('/Kubernetes-AI-Platform-Deep-Dive.html', html)

    def test_render_volcano_upgrade_doc_includes_toc_and_mermaid(self):
        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "Kubernetes-AI-Platform-Deep-Dive.md"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            rendered_doc = dict(doc)
            rendered_doc["dst"] = str(Path(tmpdir) / "volcano-upgrade.html")
            serve_docs.render_doc(rendered_doc)
            html = Path(rendered_doc["dst"]).read_text(encoding="utf-8")

        self.assertIn('<a href="#volcano-upgrade-结论与适用范围">', html)
        self.assertIn('<h4 id="volcano-upgrade-3-1-主版本变化矩阵">6.3.1 主版本变化矩阵</h4>', html)
        self.assertGreaterEqual(html.count('<div class="mermaid">'), 2)
        self.assertIn("flowchart TB", html)
        self.assertIn("flowchart LR", html)
        self.assertNotIn('class="language-mermaid"', html)

    def test_fenced_mermaid_block_renders_as_mermaid_target(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "diagram.md"
            dst = Path(directory) / "diagram.html"
            src.write_text(
                "# 图\n\n```mermaid\nflowchart LR\nA --> B\n```\n", encoding="utf-8"
            )
            with redirect_stdout(StringIO()):
                serve_docs.render_doc({
                    "src": str(src), "dst": str(dst), "title": "图",
                    "hero": "图", "subtitle": "图", "meta": "图", "footer": "图",
                })
            html = dst.read_text(encoding="utf-8")
        self.assertIn('<div class="mermaid">flowchart LR\nA --&gt; B</div>', html)
        self.assertNotIn('class="language-mermaid"', html)

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
        self.assertIn('<main id="main-content" class="doc-container" tabindex="-1">', html)
        self.assertIn("function setTocOpen(open)", html)
        self.assertIn("tocButton.setAttribute('aria-expanded', String(open));", html)
        self.assertIn("tocBackdrop.hidden = !open;", html)
        self.assertNotIn('<h2 id="目录">目录</h2>', html)
        self.assertRegex(html, r'<a class="toc-chapter" href="#第一章">第一章</a>')
        self.assertRegex(html, r'<a href="#子节">子节</a>')
        self.assertRegex(html, r'<h2 id="第一章">第一章<a class="heading-anchor" href="#第一章"[^>]*>#</a></h2>')
        self.assertRegex(html, r'<h3 id="子节">子节<a class="heading-anchor" href="#子节"[^>]*>#</a></h3>')
        self.assertNotIn("<hr />\n\n<hr />", html)


    def test_prev_next_derives_from_docs_order(self):
        def render(doc, directory):
            target = dict(doc, dst=str(Path(directory) / (Path(doc["dst"]).stem + ".html")))
            with redirect_stdout(StringIO()):
                serve_docs.render_doc(target)
            return Path(target["dst"]).read_text(encoding="utf-8")

        with tempfile.TemporaryDirectory() as directory:
            first = render(serve_docs.DOCS[0], directory)
            last = render(serve_docs.DOCS[-1], directory)
        self.assertIn('class="pager-link pager-next"', first)
        self.assertNotIn('class="pager-link pager-prev"', first)
        self.assertIn('class="pager-link pager-prev"', last)
        self.assertNotIn('class="pager-link pager-next"', last)

    def test_document_absent_from_registry_has_no_pager(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "orphan.md"
            dst = Path(directory) / "orphan.html"
            src.write_text("# 孤立文档\n\n正文\n", encoding="utf-8")
            with redirect_stdout(StringIO()):
                serve_docs.render_doc({
                    "src": str(src), "dst": str(dst), "title": "孤立文档",
                    "hero": "孤立文档", "subtitle": "孤立文档", "meta": "孤立文档", "footer": "孤立文档",
                })
            html = dst.read_text(encoding="utf-8")
        self.assertNotIn('class="doc-pager"', html)
        self.assertNotIn('aria-label="文档导航"', html)

    def test_heading_permalinks_and_sidebar_toc_stay_clean(self):
        doc = next(d for d in serve_docs.DOCS if Path(d["src"]).name == "Lustre-3FS-Deep-Dive.md")
        with tempfile.TemporaryDirectory() as directory:
            target = dict(doc, dst=str(Path(directory) / "lustre.html"))
            with redirect_stdout(StringIO()):
                serve_docs.render_doc(target)
            html = Path(target["dst"]).read_text(encoding="utf-8")
        self.assertIn('class="heading-anchor" href="#', html)
        for text in re.findall(r'<a class="toc-chapter" href="#[^"]*">(.*?)</a>', html):
            with self.subTest(chapter=text):
                self.assertNotIn("#", text)


if __name__ == "__main__":
    unittest.main()
