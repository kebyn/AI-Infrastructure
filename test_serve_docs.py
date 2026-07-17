import re
import tempfile
import unittest
from pathlib import Path

import serve_docs


class RenderDocLayoutTest(unittest.TestCase):
    def test_nvidia_gpu_operator_doc_is_registered(self):
        docs_by_src = {Path(doc["src"]).name: doc for doc in serve_docs.DOCS}

        self.assertIn("NVIDIA-GPU-Operator-Deep-Dive.md", docs_by_src)

        doc = docs_by_src["NVIDIA-GPU-Operator-Deep-Dive.md"]
        self.assertEqual(
            Path(doc["dst"]).name,
            "NVIDIA-GPU-Operator-Deep-Dive.html",
        )
        self.assertEqual(doc["href"], "/NVIDIA-GPU-Operator-Deep-Dive.html")
        self.assertEqual(doc["title"], "NVIDIA GPU Operator 深度技术文档")
        self.assertIn("v26.3.3", doc["meta"])
        self.assertIn("b0a49c0", doc["meta"])
        self.assertIn(
            "https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.3/overview.html",
            doc["footer"],
        )
        self.assertIn(
            "https://github.com/NVIDIA/gpu-operator/tree/"
            "b0a49c0e7b2e061dcd83f2bb2fe4fe960c5d0338",
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

        self.assertIn("NVIDIA GPU Operator 深度技术文档", html)
        self.assertIn('/NVIDIA-GPU-Operator-Deep-Dive.html', html)
        self.assertIn("GPU Operator v26.3.3", html)

    def test_render_nvidia_gpu_operator_doc_includes_toc_and_mermaid(self):
        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "NVIDIA-GPU-Operator-Deep-Dive.md"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            rendered_doc = dict(doc)
            rendered_doc["dst"] = str(Path(tmpdir) / "gpu-operator.html")
            serve_docs.render_doc(rendered_doc)
            html = Path(rendered_doc["dst"]).read_text(encoding="utf-8")

        self.assertIn(
            '<a class="toc-chapter" href="#第一章定位与边界">',
            html,
        )
        self.assertIn(
            '<a href="#4-1-两个配置层不要混淆">4.1 两个配置层不要混淆</a>',
            html,
        )
        self.assertIn(
            '<a class="toc-chapter" href="#第十二章故障排查方法">',
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

        self.assertIn("Kubernetes-Native-Scheduler-Deep-Dive.md", docs_by_src)

        doc = docs_by_src["Kubernetes-Native-Scheduler-Deep-Dive.md"]
        self.assertEqual(
            Path(doc["dst"]).name,
            "Kubernetes-Native-Scheduler-Deep-Dive.html",
        )
        self.assertEqual(doc["href"], "/Kubernetes-Native-Scheduler-Deep-Dive.html")
        self.assertEqual(doc["title"], "Kubernetes 原生调度器深度技术文档")
        self.assertIn("v1.36.2", doc["meta"])
        self.assertIn("5ecab45", doc["meta"])
        self.assertIn(
            "https://kubernetes.io/docs/concepts/scheduling-eviction/",
            doc["footer"],
        )
        self.assertIn(
            "https://github.com/kubernetes/kubernetes/tree/v1.36.2",
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

        self.assertIn("Kubernetes 原生调度器深度技术文档", html)
        self.assertIn('/Kubernetes-Native-Scheduler-Deep-Dive.html', html)
        self.assertIn("Kubernetes v1.36.2", html)
        self.assertIn("DRA 对象与生命周期", html)
        self.assertIn("DynamicResources 调用链", html)

    def test_render_kubernetes_native_scheduler_doc(self):
        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "Kubernetes-Native-Scheduler-Deep-Dive.md"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            rendered_doc = dict(doc)
            rendered_doc["dst"] = str(Path(tmpdir) / "kube-scheduler.html")
            serve_docs.render_doc(rendered_doc)
            html = Path(rendered_doc["dst"]).read_text(encoding="utf-8")

        self.assertIn(
            '<a class="toc-chapter" href="#第一章先明确-kube-scheduler-的边界">',
            html,
        )
        self.assertIn(
            '<a href="#3-1-两个周期与扩展点">3.1 两个周期与扩展点</a>',
            html,
        )
        self.assertIn(
            '<a class="toc-chapter" href="#第十章与五类-ai-调度项目对比">',
            html,
        )
        self.assertIn(
            '<a href="#8-2-dra-对象模型与-source-of-truth">'
            "8.2 DRA 对象模型与 source of truth</a>",
            html,
        )
        self.assertIn(
            '<a href="#8-5-dynamicresources-插件调用链">'
            "8.5 DynamicResources 插件调用链</a>",
            html,
        )
        self.assertIn(
            '<a href="#8-8-v1-36-2-feature-maturity-矩阵">'
            "8.8 v1.36.2 feature maturity 矩阵</a>",
            html,
        )
        self.assertIn(
            '<a href="#9-2-workload-podgroup-与-pod-对象链">'
            "9.2 Workload PodGroup 与 Pod 对象链</a>",
            html,
        )
        self.assertIn(
            '<a href="#9-4-podgroup-scheduling-cycle-源码路径">'
            "9.4 PodGroup scheduling cycle 源码路径</a>",
            html,
        )
        self.assertIn(
            '<a href="#9-9-dra-与-gang-的联合链路">'
            "9.9 DRA 与 Gang 的联合链路</a>",
            html,
        )
        self.assertGreaterEqual(html.count('<div class="mermaid">'), 13)
        self.assertIn("flowchart TB", html)
        self.assertIn("flowchart LR", html)
        self.assertIn("stateDiagram-v2", html)
        self.assertIn("sequenceDiagram", html)
        self.assertIn("resource.k8s.io/v1", html)
        self.assertIn("scheduling.k8s.io/v1alpha2", html)
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
        ):
            self.assertIn(feature_gate, html)
        self.assertIn("dra_grpc_operations_duration_seconds", html)
        self.assertNotIn("kubelet_dra_grpc_operations_duration_seconds", html)
        self.assertIn("Kubernetes-AI-Schedulers-Deep-Dive.html", html)
        self.assertNotIn('class="language-mermaid"', html)

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
