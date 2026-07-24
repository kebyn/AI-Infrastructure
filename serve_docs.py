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
        "meta": "Mooncake v0.3.12 · source@c7ae97f · 2026-07-24",
        "summary": "覆盖 Transfer Engine、Mooncake Store、Conductor、HiCache、SSD/DFS 持久化与缓存治理。",
        "footer": (
            '基于 <a href="https://kvcache-ai.github.io/Mooncake">Mooncake 官方文档</a> 与 '
            '<a href="https://github.com/kvcache-ai/Mooncake/tree/v0.3.12">v0.3.12 源码</a> 整理'
        ),
    },
    {
        "src": "/data/Dynamo-Deep-Dive.md",
        "dst": "/data/Dynamo-Deep-Dive.html",
        "href": "/Dynamo-Deep-Dive.html",
        "title": "Dynamo 深度技术文档",
        "hero": "Dynamo 深度技术文档",
        "subtitle": "数据中心级 LLM 推理编排、KV 路由、KVBM 与 Planner 架构解析",
        "meta": "Dynamo v1.3.0 · source@8ce9e22 · 2026-07-24",
        "summary": "覆盖 Request/Control/Storage 三平面、KV-Aware Router、KVBM、Planner、Operator 与部署模式。",
        "footer": (
            '基于 <a href="https://github.com/ai-dynamo/dynamo/tree/v1.3.0">ai-dynamo/dynamo v1.3.0</a> 与 '
            '<a href="https://docs.nvidia.com/dynamo/">NVIDIA Dynamo 官方文档</a> 整理'
        ),
    },
    {
        "src": "/data/E2B-Deep-Dive.md",
        "dst": "/data/E2B-Deep-Dive.html",
        "href": "/E2B-Deep-Dive.html",
        "title": "E2B 深度技术文档",
        "hero": "E2B 深度技术文档",
        "subtitle": "AI Sandbox、Firecracker microVM、Orchestrator、envd 与自托管架构解析",
        "meta": "E2B Infra 2026.28 · source@fda7bef · 2026-07-20",
        "summary": "覆盖控制面/数据面、sandbox 生命周期、模板构建、网络隔离、状态存储、团队配额、可靠计量、预算、内部成本分摊、Terraform/Nomad 自托管与私有化部署取舍。",
        "footer": (
            '基于 <a href="https://github.com/e2b-dev/infra/tree/fda7bef1095afb909197e272c0a8a123797f0bfb">'
            'e2b-dev/infra 2026.28</a> 官方仓库与官方自托管资料整理'
        ),
    },
    {
        "src": "/data/LLM-Benchmark-Deep-Dive.md",
        "dst": "/data/LLM-Benchmark-Deep-Dive.html",
        "href": "/LLM-Benchmark-Deep-Dive.html",
        "title": "LLM 压测工具深度对比",
        "hero": "LLM 压测工具深度对比",
        "subtitle": "AIPerf、GuideLLM、inference-perf、genai-bench、SGLang Bench、LLMPerf、vLLM Bench、EvalScope 与 Ollama Benchmark 选型解析",
        "meta": "genai-bench v0.0.5 等 9 个工具的稳定 release · 2026-07-20",
        "summary": "覆盖指标口径、负载模型、工具选型、vLLM 可比压测模板、SLO/goodput、trace replay 与生产落地建议。",
        "footer": (
            '基于 <a href="https://github.com/ai-dynamo/aiperf/tree/v0.11.0">AIPerf v0.11.0</a>、'
            '<a href="https://github.com/vllm-project/guidellm/tree/v0.7.1">GuideLLM v0.7.1</a>、'
            '<a href="https://github.com/kubernetes-sigs/inference-perf/tree/v0.6.0">inference-perf v0.6.0</a>、'
            '<a href="https://github.com/sgl-project/genai-bench/tree/v0.0.5">genai-bench v0.0.5</a>、'
            '<a href="https://github.com/sgl-project/sglang/blob/v0.5.15.post1/docs/developer_guide/bench_serving.md">SGLang Bench v0.5.15.post1</a>、'
            '<a href="https://github.com/vllm-project/vllm/tree/v0.25.1/benchmarks">vLLM Bench v0.25.1</a> 与 '
            '<a href="https://github.com/modelscope/evalscope/tree/v1.9.0">EvalScope v1.9.0</a> 等官方资料整理'
        ),
    },
    {
        "src": "/data/Lustre-3FS-Deep-Dive.md",
        "dst": "/data/Lustre-3FS-Deep-Dive.html",
        "href": "/Lustre-3FS-Deep-Dive.html",
        "title": "Lustre 与 3FS 深度技术文档",
        "hero": "Lustre 与 3FS 深度技术文档",
        "subtitle": "HPC 并行文件系统、AI 原生分布式文件系统、RDMA/NVMe 与 KVCache 存储层选型解析",
        "meta": "Lustre 官方资料 · deepseek-ai/3fs main@22fca04 · 2026-07-20",
        "summary": "覆盖 Lustre MDS/OSS/OST/LNet、3FS Meta/Storage/CRAQ/USRBIO、AI dataloader、checkpoint、KV cache 与生产选型。",
        "footer": (
            '基于 <a href="https://wiki.lustre.org/Introduction_to_Lustre">Lustre Wiki</a>、'
            '<a href="https://github.com/deepseek-ai/3fs/tree/22fca04564c7cc230fd8b9523b8b92864e1dad47">deepseek-ai/3fs main@22fca04</a> 与 '
            '<a href="https://arxiv.org/html/2408.14158v1">Fire-Flyer AI-HPC 论文</a> 整理'
        ),
    },
    {
        "src": "/data/NVIDIA-GPU-Operator-Deep-Dive.md",
        "dst": "/data/NVIDIA-GPU-Operator-Deep-Dive.html",
        "href": "/NVIDIA-GPU-Operator-Deep-Dive.html",
        "title": "NVIDIA GPU Operator 深度技术文档",
        "hero": "NVIDIA GPU Operator 深度技术文档",
        "subtitle": "Kubernetes GPU 节点软件栈、ClusterPolicy 调谐、设备暴露、共享隔离与生产运维解析",
        "meta": "GPU Operator v26.3.3 · source@b0a49c0 · 2026-07-20",
        "summary": "覆盖 Controller 调谐、Driver/Toolkit/Device Plugin、CDI/NRI、MIG、Time-Slicing/MPS、DCGM、升级、安全与故障排查。",
        "footer": (
            '基于 <a href="https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.3/overview.html">'
            'NVIDIA GPU Operator 26.3 官方文档</a> 与 '
            '<a href="https://github.com/NVIDIA/gpu-operator/tree/b0a49c0e7b2e061dcd83f2bb2fe4fe960c5d0338">'
            'NVIDIA/gpu-operator v26.3.3 源码</a> 整理'
        ),
    },
    {
        "src": "/data/HAMi-Deep-Dive.md",
        "dst": "/data/HAMi-Deep-Dive.html",
        "href": "/HAMi-Deep-Dive.html",
        "title": "HAMi 深度技术文档",
        "hero": "HAMi 深度技术文档",
        "subtitle": "Kubernetes 异构 AI 设备虚拟化、共享、隔离与调度架构解析",
        "meta": "HAMi v2.9.0 · source@3a006c6 · 2026-07-20",
        "summary": "覆盖 MutatingWebhook、Scheduler Extender、Device Plugin、HAMi-Core、Annotation 协议、多厂商设备与生产实践。",
        "footer": (
            '基于 <a href="https://github.com/Project-HAMi/HAMi/tree/v2.9.0">Project-HAMi/HAMi v2.9.0</a> 与 '
            '<a href="https://project-hami.io/docs">HAMi 官方文档</a> 整理'
        ),
    },
    {
        "src": "/data/Kubernetes-Native-Scheduler-Deep-Dive.md",
        "dst": "/data/Kubernetes-Native-Scheduler-Deep-Dive.html",
        "href": "/Kubernetes-Native-Scheduler-Deep-Dive.html",
        "title": "Kubernetes 原生调度器深度技术文档",
        "hero": "Kubernetes 原生调度器深度技术文档",
        "subtitle": "kube-scheduler 架构、Scheduling Framework、工作负载级调度与 AI 调度器对比",
        "meta": "Kubernetes v1.36.3 · source@0f29094 · 2026-07-24",
        "summary": "覆盖调度队列、Filter/Score/Bind、DRA 对象与生命周期、DynamicResources 调用链、PodGroup/Gang/TAS、工作负载级抢占及 AI 调度器选型。",
        "footer": (
            '基于 <a href="https://kubernetes.io/docs/concepts/scheduling-eviction/">'
            'Kubernetes Scheduling, Preemption and Eviction 官方文档</a> 与 '
            '<a href="https://github.com/kubernetes/kubernetes/tree/v1.36.3">'
            'kubernetes/kubernetes v1.36.3 源码</a> 整理'
        ),
    },
    {
        "src": "/data/Kubernetes-AI-Schedulers-Deep-Dive.md",
        "dst": "/data/Kubernetes-AI-Schedulers-Deep-Dive.html",
        "href": "/Kubernetes-AI-Schedulers-Deep-Dive.html",
        "title": "Kubernetes AI 调度器深度对比",
        "hero": "Kubernetes AI 调度器深度对比",
        "subtitle": "Koordinator、Kueue、Grove、KAI-Scheduler 与 Volcano 架构、能力边界和生产选型解析",
        "meta": "Kueue v0.19.0 · KAI-Scheduler v0.16.6 · 2026-07-24",
        "summary": "覆盖队列准入、Gang Scheduling、GPU/拓扑、配额公平、Grove 调度后端、组合架构、升级治理与场景化选型。",
        "footer": (
            '基于 <a href="https://github.com/koordinator-sh/koordinator">Koordinator</a>、'
            '<a href="https://github.com/kubernetes-sigs/kueue/tree/v0.19.0">Kueue v0.19.0</a>、'
            '<a href="https://github.com/ai-dynamo/grove">Grove</a>、'
            '<a href="https://github.com/kai-scheduler/KAI-Scheduler/tree/v0.16.6">KAI-Scheduler v0.16.6</a> 与 '
            '<a href="https://github.com/volcano-sh/volcano">Volcano</a> 官方资料整理'
        ),
    },
    {
        "src": "/data/Volcano-Upgrade-Compatibility-Deep-Dive.md",
        "dst": "/data/Volcano-Upgrade-Compatibility-Deep-Dive.html",
        "href": "/Volcano-Upgrade-Compatibility-Deep-Dive.html",
        "title": "Volcano 升级与 Feature 兼容性",
        "hero": "Volcano 升级与 Feature 兼容性",
        "subtitle": "v1.8.2 到 v1.15.0 的 Helm、Webhook、Queue 语义与 Cloud Native Colocation 兼容边界",
        "meta": "Volcano v1.8.2 → v1.15.0 · 2026-07-20",
        "summary": "覆盖六层升级判定、逐版本矩阵、proportion/capacity 迁移、已确认故障、Agent 节点边界、DRA quota 与 gang-aware eviction。",
        "footer": (
            '基于 <a href="https://github.com/volcano-sh/volcano">Volcano</a>、'
            '<a href="https://volcano.sh/docs/keyfeatures/cloudnativecolocation/">Cloud Native Colocation</a>、'
            '<a href="https://volcano.sh/docs/keyfeatures/queueresourcemanagement/">Queue Resource Management</a> 与 '
            '<a href="https://github.com/volcano-sh/helm-charts">Helm Charts</a> 官方资料整理'
        ),
    },
    {
        "src": "/data/KServe-Deep-Dive.md",
        "dst": "/data/KServe-Deep-Dive.html",
        "href": "/KServe-Deep-Dive.html",
        "title": "KServe 深度技术文档",
        "hero": "KServe 深度技术文档",
        "subtitle": "Kubernetes 生成式 AI 与预测式 AI 推理服务平台架构解析",
        "meta": "KServe v0.19.0 · source@b0eda63 · master@d748bd1 · 2026-07-20",
        "summary": "覆盖 InferenceService、LLMInferenceService、ServingRuntime、Gateway API、LocalModelCache、LMCache 与未发布主线 KV cache offloading 边界。",
        "footer": (
            '基于 <a href="https://github.com/kserve/kserve/tree/v0.19.0">kserve/kserve v0.19.0</a> 与 '
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
        "meta": "Kubeflow Community Distribution 26.03.1 · source@f09f3ee · 2026-07-20",
        "summary": "覆盖 Community Distribution 架构、Dashboard、Profiles、Pipelines、Notebooks、Katib、Trainer、KServe 节点、Istio/OAuth2/Dex 与生产实践。",
        "footer": (
            '基于 <a href="https://github.com/kubeflow/community-distribution/tree/26.03.1">'
            'kubeflow/community-distribution 26.03.1</a> 与 '
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

def collect_toc_sections(body):
    """Collect h2/h3 headings into a nested table of contents."""
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

    return sections

def build_nested_toc(body):
    """Build the generated h2/h3 table of contents."""
    sections = collect_toc_sections(body)
    if not sections:
        return ""

    lines = [
        '<nav class="toc toc-nested" aria-label="文档章节">',
        '<div class="toc-title">目录</div>',
        "<ul>",
    ]
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
    lines.extend(["</ul>", "</nav>"])
    return "\n".join(lines)

def remove_inline_toc_placeholder(body):
    """Remove the Markdown TOC placeholder from the rendered document body."""
    body, _ = re.subn(
        r'<h2 id="目录">目录</h2>\s*<ul>.*?</ul>\s*(?:<hr\s*/?>\s*)?',
        "",
        body,
        count=1,
        flags=re.S,
    )
    return body

def split_body_and_toc(body):
    """Return the body without the inline TOC and a sidebar TOC fragment."""
    return remove_inline_toc_placeholder(body), build_nested_toc(body)

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
.doc-page {
  max-width: 1360px;
  margin: 0 auto;
}
.doc-shell {
  display: grid;
  grid-template-columns: minmax(220px, 280px) minmax(0, 960px);
  gap: 40px;
  align-items: start;
  justify-content: center;
  padding: 0 32px 120px;
}
.doc-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 40px 32px 120px;
}
.doc-hero-container {
  padding-bottom: 0;
}
.doc-shell .doc-container {
  width: 100%;
  min-width: 0;
  margin: 0;
  padding: 0;
}
.doc-sidebar {
  position: sticky;
  top: 24px;
  max-height: calc(100vh - 48px);
  overflow: auto;
  padding-bottom: 24px;
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
a:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
}

.toc-fab {
  display: none;
}
.toc-backdrop {
  display: none;
}

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
.doc-sidebar .toc-home-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 42px;
  margin: 0 0 12px;
  padding: 0 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: rgba(88, 166, 255, 0.08);
  color: var(--text);
  font-weight: 600;
}
.doc-sidebar .toc-home-link:hover {
  border-color: var(--accent-dim);
  color: var(--accent);
}
.doc-sidebar .toc {
  margin: 0;
  padding: 20px 18px;
  max-height: none;
}
.doc-sidebar .toc-title {
  position: sticky;
  top: 0;
  z-index: 1;
  margin: -20px -18px 12px;
  padding: 16px 18px 10px;
  background: var(--bg-card);
  border-bottom: 1px solid rgba(48, 54, 61, 0.7);
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
  .doc-container { padding: 20px 16px 104px; }
  .doc-hero-container { padding-bottom: 0; }
  .doc-shell {
    display: block;
    padding: 0 16px 104px;
  }
  .doc-shell .doc-container {
    padding: 0;
  }
  body.toc-open {
    overflow: hidden;
  }
  .doc-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 42;
    width: min(86vw, 340px);
    height: 100dvh;
    max-height: none;
    overflow: auto;
    padding: 16px;
    background: var(--bg);
    border-right: 1px solid var(--border);
    box-shadow: 20px 0 44px rgba(0, 0, 0, 0.45);
    transform: translateX(-100%);
    transition: transform 0.22s ease;
    overscroll-behavior: contain;
  }
  body.toc-open .doc-sidebar {
    transform: translateX(0);
  }
  .doc-sidebar .toc {
    min-height: calc(100dvh - 32px);
    max-height: none;
  }
  .toc-backdrop {
    position: fixed;
    inset: 0;
    z-index: 41;
    background: rgba(1, 4, 9, 0.68);
    backdrop-filter: blur(2px);
  }
  body.toc-open .toc-backdrop {
    display: block;
  }
  .toc-fab {
    position: fixed;
    left: 14px;
    bottom: 14px;
    z-index: 43;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 64px;
    height: 40px;
    padding: 0 14px;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: rgba(22, 27, 34, 0.92);
    color: var(--text);
    font: inherit;
    font-size: 0.9em;
    font-weight: 600;
    line-height: 1;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
    backdrop-filter: blur(10px);
  }
  .toc-fab:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 4px;
  }
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
    body, toc_html = split_body_and_toc(body)
    sidebar_html = (
        '<aside id="doc-sidebar" class="doc-sidebar" aria-label="文档目录">\n'
        '<a class="toc-home-link" href="/">首页</a>\n'
        f'{toc_html}\n</aside>'
        if toc_html
        else ""
    )
    mobile_toc_controls = (
        '<button class="toc-fab" type="button" aria-controls="doc-sidebar" '
        'aria-expanded="false">目录</button>\n'
        '<div class="toc-backdrop" hidden></div>'
        if toc_html
        else ""
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{doc["title"]}</title>
<style>{CSS}</style>
</head>
<body>
{mobile_toc_controls}
<div class="doc-page">
<div class="doc-container doc-hero-container">
  <div class="doc-hero">
    <h1>{doc["hero"]}</h1>
    <p class="subtitle">{doc["subtitle"]}</p>
    <p class="meta">{doc["meta"]}</p>
  </div>
</div>
<div class="doc-shell">
  {sidebar_html}
  <main class="doc-container">
  {body}
  <div class="doc-footer">
    <p>{doc["footer"]}</p>
  </div>
  </main>
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
<script>
  const tocButton = document.querySelector('.toc-fab');
  const tocBackdrop = document.querySelector('.toc-backdrop');
  const tocSidebar = document.querySelector('#doc-sidebar');

  if (tocButton && tocBackdrop && tocSidebar) {{
    function setTocOpen(open) {{
      document.body.classList.toggle('toc-open', open);
      tocButton.setAttribute('aria-expanded', String(open));
      tocBackdrop.hidden = !open;
    }}

    tocButton.addEventListener('click', () => {{
      setTocOpen(!document.body.classList.contains('toc-open'));
    }});
    tocBackdrop.addEventListener('click', () => setTocOpen(false));
    tocSidebar.addEventListener('click', (event) => {{
      if (event.target.closest('a')) {{
        setTocOpen(false);
      }}
    }});
    document.addEventListener('keydown', (event) => {{
      if (event.key === 'Escape') {{
        setTocOpen(false);
      }}
    }});
  }}
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
    <p class="subtitle">LLM 推理、压测、存储、Sandbox、异构设备、AI 调度、模型服务与 MLOps 技术分析入口</p>
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
