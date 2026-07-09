#!/usr/bin/env python3
"""Convert the deep-dive Markdown docs to styled HTML and serve on port 80."""

import markdown
from html import escape, unescape
from http.server import HTTPServer, SimpleHTTPRequestHandler
import re

INDEX = "/data/index.html"
DOCS = [
    {
        "src": "/data/Mooncake-Deep-Dive.md",
        "dst": "/data/Mooncake-Deep-Dive.html",
        "href": "/Mooncake-Deep-Dive.html",
        "title": "Mooncake 深度技术文档",
        "hero": "🌙 Mooncake 深度技术文档",
        "subtitle": "以 KVCache 为中心的分离式 LLM 推理架构全面解析",
        "meta": "FAST 2025 最佳论文 · Moonshot AI · Kimi 服务平台",
        "summary": "覆盖 Transfer Engine、Mooncake Store、Conductor、HiCache、SSD/DFS 持久化与缓存治理。",
        "footer": (
            '基于 <a href="https://kvcache-ai.github.io/Mooncake">Mooncake 官方文档</a> 整理 · '
            '<a href="https://github.com/kvcache-ai/Mooncake">GitHub</a>'
        ),
    },
    {
        "src": "/data/Dynamo-Deep-Dive.md",
        "dst": "/data/Dynamo-Deep-Dive.html",
        "href": "/Dynamo-Deep-Dive.html",
        "title": "Dynamo 深度技术文档",
        "hero": "Dynamo 深度技术文档",
        "subtitle": "数据中心级 LLM 推理编排、KV 路由、KVBM 与 Planner 架构解析",
        "meta": "基于 ai-dynamo/dynamo main@cc5cf40 · 2026-07-09",
        "summary": "覆盖 Request/Control/Storage 三平面、KV-Aware Router、KVBM、Planner、Operator 与部署模式。",
        "footer": (
            '基于 <a href="https://github.com/ai-dynamo/dynamo">ai-dynamo/dynamo</a> 与 '
            '<a href="https://docs.nvidia.com/dynamo/">NVIDIA Dynamo 官方文档</a> 整理'
        ),
    },
    {
        "src": "/data/HAMi-Deep-Dive.md",
        "dst": "/data/HAMi-Deep-Dive.html",
        "href": "/HAMi-Deep-Dive.html",
        "title": "HAMi 深度技术文档",
        "hero": "HAMi 深度技术文档",
        "subtitle": "Kubernetes 异构 AI 设备虚拟化、共享、隔离与调度架构解析",
        "meta": "基于 Project-HAMi/HAMi master@500fcef · 2026-07-09",
        "summary": "覆盖 MutatingWebhook、Scheduler Extender、Device Plugin、HAMi-Core、Annotation 协议、多厂商设备与生产实践。",
        "footer": (
            '基于 <a href="https://github.com/Project-HAMi/HAMi">Project-HAMi/HAMi</a> 与 '
            '<a href="https://project-hami.io/docs">HAMi 官方文档</a> 整理'
        ),
    },
    {
        "src": "/data/KServe-Deep-Dive.md",
        "dst": "/data/KServe-Deep-Dive.html",
        "href": "/KServe-Deep-Dive.html",
        "title": "KServe 深度技术文档",
        "hero": "KServe 深度技术文档",
        "subtitle": "Kubernetes 生成式 AI 与预测式 AI 推理服务平台架构解析",
        "meta": "基于 kserve/kserve master@9f68073 · website@f4f7147 · 2026-07-09",
        "summary": "覆盖 InferenceService、LLMInferenceService、ServingRuntime、Gateway API、LocalModelCache、KV cache offloading 与生产实践。",
        "footer": (
            '基于 <a href="https://github.com/kserve/kserve">kserve/kserve</a> 与 '
            '<a href="https://kserve.github.io/website/">KServe 官方文档</a> 整理'
        ),
    },
    {
        "src": "/data/Kubeflow-Deep-Dive.md",
        "dst": "/data/Kubeflow-Deep-Dive.html",
        "href": "/Kubeflow-Deep-Dive.html",
        "title": "Kubeflow 深度技术文档",
        "hero": "Kubeflow 深度技术文档",
        "subtitle": "Kubeflow Community Distribution、端到端 MLOps 平台与 KServe 节点集成解析",
        "meta": "基于 kubeflow/community-distribution master@80bb48d · 2026-07-09",
        "summary": "覆盖 Community Distribution 架构、Dashboard、Profiles、Pipelines、Notebooks、Katib、Trainer、KServe 节点、Istio/OAuth2/Dex 与生产实践。",
        "footer": (
            '基于 <a href="https://github.com/kubeflow/community-distribution">kubeflow/community-distribution</a> 与 '
            '<a href="https://www.kubeflow.org/">Kubeflow 官方文档</a> 整理'
        ),
    },
]

def slugify_heading(value, separator):
    """Generate stable heading ids that match the hand-written Markdown TOC."""
    value = value.strip().lower()
    dash_marker = "__mooncake_dash__"
    value = re.sub(r"\s*[—–]\s*", dash_marker, value)
    value = re.sub(r"[：:]", "", value)
    value = re.sub(r"[()（）]", "", value)
    value = re.sub(r"[^\w\u4e00-\u9fff-]+", separator, value)
    value = re.sub(rf"{re.escape(separator)}+", separator, value)
    value = value.replace(dash_marker, f"{separator}{separator}")
    return value.strip(separator)

def inject_nested_toc(body):
    """Replace the hand-written top-level TOC with an h2/h3 nested TOC."""
    sections = []
    current = None
    heading_re = re.compile(r'<h([23]) id="([^"]+)">(.*?)</h\1>', re.S)

    for match in heading_re.finditer(body):
        level = int(match.group(1))
        heading_id = match.group(2)
        heading_html = match.group(3).strip()

        if heading_id == "目录":
            continue

        item = {
            "id": heading_id,
            "html": heading_html,
            "children": [],
        }
        if level == 2:
            sections.append(item)
            current = item
        elif level == 3 and current is not None:
            current["children"].append(item)

    if not sections:
        return body

    lines = ['<div class="toc toc-nested">', "<ul>"]
    for section in sections:
        lines.append(
            f'<li><a class="toc-chapter" href="#{escape(section["id"], quote=True)}">'
            f'{section["html"]}</a>'
        )
        if section["children"]:
            lines.append("<ul>")
            for child in section["children"]:
                lines.append(
                    f'<li><a href="#{escape(child["id"], quote=True)}">'
                    f'{child["html"]}</a></li>'
                )
            lines.append("</ul>")
        lines.append("</li>")
    lines.extend(["</ul>", "</div>"])

    replacement = '<h2 id="目录">目录</h2>\n' + "\n".join(lines)
    body, _ = re.subn(
        r'<h2 id="目录">目录</h2>\s*<ul>.*?</ul>',
        replacement,
        body,
        count=1,
        flags=re.S,
    )
    return body

def render_mermaid_blocks(body):
    """Convert fenced mermaid code blocks into Mermaid render targets."""
    def repl(match):
        diagram = unescape(match.group(1)).strip()
        return f'<div class="mermaid">\n{diagram}\n</div>'

    return re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        repl,
        body,
        flags=re.S,
    )

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+SC:wght@400;500;700&display=swap');

:root {
  --bg: #0d1117;
  --bg-card: #161b22;
  --bg-code: #1a1e26;
  --text: #e6edf3;
  --text-secondary: #8b949e;
  --accent: #58a6ff;
  --accent-dim: #1f6feb;
  --border: #30363d;
  --green: #3fb950;
  --orange: #d29922;
  --red: #f85149;
  --purple: #bc8cff;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

html {
  scroll-behavior: smooth;
  scroll-padding-top: 80px;
}

body {
  font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.75;
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
}

/* ─── Layout ─── */
.doc-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 40px 32px 120px;
}

/* ─── Hero ─── */
.doc-hero {
  text-align: center;
  padding: 80px 0 48px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 48px;
}
.doc-hero h1 {
  font-size: 2.5em;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 12px;
}
.doc-hero .subtitle {
  font-size: 1.15em;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.doc-hero .meta {
  font-size: 0.9em;
  color: var(--orange);
}

/* ─── Headings ─── */
h2 {
  font-size: 1.75em;
  font-weight: 700;
  color: var(--text);
  margin: 64px 0 24px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--accent-dim);
  letter-spacing: -0.01em;
}
h3 {
  font-size: 1.3em;
  font-weight: 600;
  color: var(--accent);
  margin: 36px 0 16px;
}
h4 {
  font-size: 1.1em;
  font-weight: 600;
  color: var(--purple);
  margin: 24px 0 12px;
}

/* ─── Paragraphs & Lists ─── */
p { margin: 0 0 16px; }

ul, ol {
  margin: 0 0 16px 24px;
}
li { margin: 4px 0; }
li::marker { color: var(--accent); }

/* ─── Links ─── */
a {
  color: var(--accent);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s;
}
a:hover { border-bottom-color: var(--accent); }

/* ─── Blockquotes ─── */
blockquote {
  border-left: 4px solid var(--accent-dim);
  background: rgba(31, 111, 235, 0.08);
  padding: 14px 20px;
  margin: 16px 0;
  border-radius: 0 8px 8px 0;
  color: var(--text-secondary);
  font-style: italic;
}
blockquote strong { color: var(--accent); font-style: normal; }

/* ─── Code ─── */
code {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.88em;
  background: var(--bg-code);
  padding: 2px 7px;
  border-radius: 4px;
  color: var(--green);
  border: 1px solid var(--border);
}
pre {
  background: var(--bg-code);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 18px 22px;
  margin: 16px 0;
  overflow-x: auto;
  line-height: 1.6;
}
pre code {
  background: none;
  padding: 0;
  border: none;
  color: var(--text);
  font-size: 0.85em;
}
.mermaid {
  background: var(--bg-code);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 18px 22px;
  margin: 18px 0 24px;
  overflow-x: auto;
  text-align: center;
}
.mermaid svg {
  max-width: 100%;
  height: auto;
}

/* ─── Tables ─── */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0 24px;
  font-size: 0.92em;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--border);
}
thead {
  background: var(--bg-card);
}
th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: var(--accent);
  border-bottom: 2px solid var(--border);
  white-space: nowrap;
}
td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
tr:last-child td { border-bottom: none; }
tr:hover { background: rgba(88, 166, 255, 0.04); }

/* ─── Horizontal Rule ─── */
hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 48px 0;
}

/* ─── TOC ─── */
.toc {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px 28px;
  margin: 24px 0 48px;
}
.toc-title {
  font-size: 1.1em;
  font-weight: 600;
  color: var(--accent);
  margin-bottom: 12px;
}
.toc ul {
  list-style: none;
  margin: 0;
  padding: 0;
}
.toc > ul > li {
  padding: 4px 0;
}
.toc > ul > li > a {
  color: var(--text);
  font-weight: 500;
  font-size: 0.95em;
}
.toc > ul > li > a:hover { color: var(--accent); }
.toc.toc-nested {
  max-height: min(72vh, 760px);
  overflow: auto;
}
.toc.toc-nested > ul > li {
  padding: 10px 0;
  border-bottom: 1px solid rgba(48, 54, 61, 0.7);
}
.toc.toc-nested > ul > li:last-child {
  border-bottom: none;
}
.toc.toc-nested .toc-chapter {
  color: var(--text);
  font-weight: 600;
}
.toc.toc-nested ul ul {
  margin: 8px 0 0 16px;
  display: grid;
  gap: 2px;
}
.toc.toc-nested ul ul a {
  color: var(--text-secondary);
  font-size: 0.88em;
  line-height: 1.45;
}
.toc.toc-nested ul ul a:hover {
  color: var(--accent);
}

/* ─── Details (appendix) ─── */
details {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  margin: 16px 0;
  overflow: hidden;
}
summary {
  padding: 14px 20px;
  cursor: pointer;
  font-weight: 600;
  color: var(--accent);
  list-style: none;
  display: flex;
  align-items: center;
  gap: 8px;
}
summary::before {
  content: '▶';
  font-size: 0.7em;
  transition: transform 0.2s;
}
details[open] summary::before {
  transform: rotate(90deg);
}
details > *:not(summary) {
  padding: 0 20px 16px;
}

/* ─── Footer ─── */
.doc-footer {
  text-align: center;
  padding: 40px 0;
  border-top: 1px solid var(--border);
  margin-top: 64px;
  color: var(--text-secondary);
  font-size: 0.85em;
}

/* ─── Index ─── */
.doc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
  margin: 28px 0 48px;
}
.doc-card {
  display: block;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 22px 24px;
  min-height: 180px;
  color: var(--text);
  transition: border-color 0.2s, transform 0.2s, background 0.2s;
}
.doc-card:hover {
  border-bottom-color: var(--accent);
  border-color: var(--accent-dim);
  background: rgba(88, 166, 255, 0.06);
  transform: translateY(-2px);
}
.doc-card h2 {
  margin: 0 0 10px;
  padding: 0;
  border: none;
  color: var(--accent);
  font-size: 1.25em;
}
.doc-card p {
  color: var(--text-secondary);
  margin: 0 0 16px;
}
.doc-card .doc-card-meta {
  color: var(--orange);
  font-size: 0.86em;
}

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }

/* ─── Responsive ─── */
@media (max-width: 768px) {
  .doc-container { padding: 20px 16px 80px; }
  .doc-hero h1 { font-size: 1.8em; }
  h2 { font-size: 1.4em; }
  .doc-grid { grid-template-columns: 1fr; }
  table { font-size: 0.82em; }
  th, td { padding: 8px 10px; }
}

/* ─── Strong emphasis with accent ─── */
strong { color: var(--text); }
p strong, li strong { color: var(--green); }
"""

def render_doc(doc):
    with open(doc["src"], "r", encoding="utf-8") as f:
        md_text = f.read()

    extensions = [
        "tables",
        "fenced_code",
        "toc",
        "smarty",
        "sane_lists",
        "pymdownx.details",
    ]
    extension_configs = {
        "toc": {
            "title": "目录",
            "toc_depth": 2,
            "slugify": slugify_heading,
        },
    }

    body = markdown.markdown(
        md_text,
        extensions=extensions,
        extension_configs=extension_configs,
    )
    body = render_mermaid_blocks(body)
    body = inject_nested_toc(body)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{doc["title"]}</title>
<style>{CSS}</style>
</head>
<body>
<div class="doc-container">
  <div class="doc-hero">
    <h1>{doc["hero"]}</h1>
    <p class="subtitle">{doc["subtitle"]}</p>
    <p class="meta">{doc["meta"]}</p>
  </div>
  {body}
  <div class="doc-footer">
    <p>{doc["footer"]}</p>
  </div>
</div>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{
    startOnLoad: true,
    securityLevel: 'loose',
    theme: 'dark',
    themeVariables: {{
      background: '#0d1117',
      primaryColor: '#161b22',
      primaryTextColor: '#e6edf3',
      primaryBorderColor: '#30363d',
      lineColor: '#58a6ff',
      secondaryColor: '#1a1e26',
      tertiaryColor: '#0d1117',
      fontFamily: 'Inter, Noto Sans SC, sans-serif'
    }}
  }});
</script>
</body>
</html>"""

    with open(doc["dst"], "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Rendered {doc['src']} → {doc['dst']} ({len(html)} bytes)")


def render_index():
    cards = []
    for doc in DOCS:
        cards.append(
            f"""<a class="doc-card" href="{escape(doc["href"], quote=True)}">
  <h2>{escape(doc["title"])}</h2>
  <p>{escape(doc["summary"])}</p>
  <span class="doc-card-meta">{escape(doc["meta"])}</span>
</a>"""
        )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 基础设施深度文档</title>
<style>{CSS}</style>
</head>
<body>
<div class="doc-container">
  <div class="doc-hero">
    <h1>AI 基础设施深度文档</h1>
    <p class="subtitle">Mooncake、Dynamo、HAMi、KServe 与 Kubeflow 技术分析入口</p>
    <p class="meta">统一运行在 80 端口</p>
  </div>
  <div class="doc-grid">
    {"".join(cards)}
  </div>
  <div class="doc-footer">
    <p>本页由 <code>/data/serve_docs.py</code> 生成，文档源文件位于 <code>/data</code>。</p>
  </div>
</div>
</body>
</html>"""

    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Rendered index → {INDEX} ({len(html)} bytes)")


def convert():
    for doc in DOCS:
        render_doc(doc)
    render_index()


import socket

class V6HTTPServer(HTTPServer):
    address_family = socket.AF_INET6
    allow_reuse_address = True

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory="/data", **kw)

    def do_GET(self):
        path = self.path.rstrip("/")
        if path == "" or path == "/index.html":
            self.path = "/index.html"
        return super().do_GET()

    def log_message(self, fmt, *args):
        print(f"[HTTP] {args[0]}")


if __name__ == "__main__":
    convert()
    port = 80
    server = V6HTTPServer(("::", port), Handler)
    print(f"🚀 Serving on http://0.0.0.0:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Stopped")
        server.server_close()
