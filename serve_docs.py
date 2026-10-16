#!/usr/bin/env python3
"""Convert the deep-dive Markdown docs to styled HTML and serve on port 80."""

import markdown
from html import escape, unescape
from http.server import HTTPServer, SimpleHTTPRequestHandler
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit

from pymdownx.superfences import fence_div_format
from pygments.formatters import HtmlFormatter

INDEX = "/data/index.html"
CATEGORIES = (
    "推理与压测", "模型时间线", "存储", "访问治理", "Kubernetes 平台", "Agent 协作", "Sandbox",
)
DOCS = [{'src': '/data/AI-Inference-Deep-Dive.md',
  'dst': '/data/AI-Inference-Deep-Dive.html',
  'href': '/AI-Inference-Deep-Dive.html',
  'title': '推理系统与压测深度文档',
  'category': '推理与压测',
  'hero': '推理系统与压测深度文档',
  'subtitle': '公共概念、Mooncake、Dynamo、压测工具与组合选型',
  'meta': 'Mooncake v0.3.13.post1 · Dynamo v1.5.1 source@2093662 · ModelExpress v0.7.0 · AIPerf '
          'v0.13.0 · GuideLLM v0.7.4 · inference-perf v0.7.0 · SGLang v0.5.21 · vLLM v0.31.0 · '
          'EvalScope v1.13.0 · 2026-10-16',
  'summary': '覆盖 KVCache、P/D 分离、Mooncake Transfer Engine/Store/HiCache、Dynamo '
             'Router/Planner/ModelExpress，以及 AIPerf、SGLang Bench、vLLM Bench、EvalScope 的指标、trace 与 '
             'SLO/goodput。',
  'footer': '基于 <a href="https://kvcache-ai.github.io/Mooncake">Mooncake 官方文档</a> 与 <a '
            'href="https://github.com/kvcache-ai/Mooncake/tree/719735896c86b56fabec6cf3e825fb2ea640597a">v0.3.13.post1 '
            '源码</a> 整理 · 基于 <a '
            'href="https://github.com/ai-dynamo/dynamo/tree/2093662a4d4e5fd318732935213dde08dc7be818">ai-dynamo/dynamo '
            'v1.5.1 源码</a> 与 <a '
            'href="https://github.com/ai-dynamo/modelexpress/tree/ac6d03a87a550c8188c3ed59f187b90d4f0554f5">ModelExpress '
            'v0.7.0 源码</a> 与 <a href="https://docs.nvidia.com/dynamo/">NVIDIA Dynamo 官方文档</a> 整理 · '
            '<a '
            'href="https://github.com/ai-dynamo/aiperf/tree/794f8bb75f8582f22e412d7e650fc71ca2a3d21a">AIPerf '
            'v0.13.0 源码</a>、<a '
            'href="https://github.com/vllm-project/guidellm/tree/291a6e609c3eb52d6eadcedecc7a056e396cd5eb">GuideLLM '
            'v0.7.4 源码</a>、<a '
            'href="https://github.com/kubernetes-sigs/inference-perf/tree/5804ea6b7ebd2bfceff29cf113311ed3af95146e">inference-perf '
            'v0.7.0 源码</a>、<a '
            'href="https://github.com/sgl-project/genai-bench/tree/v0.0.5">genai-bench '
            'v0.0.5</a>、<a '
            'href="https://github.com/sgl-project/sglang/tree/e00930c5489053f26d86b179cee0d087f846acbb">SGLang '
            'Bench v0.5.21 源码</a>、<a '
            'href="https://github.com/vllm-project/vllm/tree/db9527a46873454610df6dbedf79a36d6bf1a7f6/benchmarks">vLLM '
            'Bench v0.31.0 源码</a> 与 <a '
            'href="https://github.com/modelscope/evalscope/tree/498027686e6e3cf4eb32405a3fd21c65ff9237f1">EvalScope '
            'v1.13.0 源码</a> 等官方资料整理'},
 {'src': '/data/Kubernetes-AI-Platform-Deep-Dive.md',
  'dst': '/data/Kubernetes-AI-Platform-Deep-Dive.html',
  'href': '/Kubernetes-AI-Platform-Deep-Dive.html',
  'title': 'Kubernetes AI 平台深度文档',
  'category': 'Kubernetes 平台',
  'hero': 'Kubernetes AI 平台深度文档',
  'subtitle': '版本演进、调度、GPU 设备、服务平台与统一组合选型',
  'meta': 'Kubernetes v1.37.1 source@f78e722 · GPU Operator v26.7.2@5a9c8a8 · HAMi v2.10.0 · '
          'Koordinator v1.8.0 · Kueue v0.20.2@296ec3db · Grove alpha.16@e33b8353 · KAI-Scheduler '
          'v0.18.6@279f61c6 · Volcano v1.16.0@41f27d56（升级 v1.8.2 → v1.16.0） · KServe v0.21.0 '
          'master@bb22cc4 website@71c8b22 · Kubeflow 26.03.1 · Kubernetes v1.38.0-alpha.2 仅作预览 · '
          '2026-10-16',
  'summary': '覆盖 Kubernetes Blog/RSS、v1.37 DRA 扩展、Workload/PodGroup v1beta1、Gang/TAS、GPU '
             'Operator、HAMi、五类 AI 调度器、Volcano 升级、独立 KServe 与 Kubeflow 发行版，以及成熟度和组合合同。',
  'footer': '基于 <a '
            'href="https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.7/overview.html">NVIDIA '
            'GPU Operator 26.7 官方文档</a> 与 <a '
            'href="https://github.com/NVIDIA/gpu-operator/releases/tag/v26.7.2">NVIDIA GPU Operator '
            'v26.7.2 Release</a>、<a '
            'href="https://github.com/NVIDIA/gpu-operator/tree/9ae64a28deb145182fc0def6f4ceb23fdd3aba79">tag object</a> 与 <a '
            'href="https://github.com/NVIDIA/gpu-operator/tree/5a9c8a8b3f5bac7fb06ad3c2a05771fceb8b4832">v26.7.2 exact source</a> 整理 · 基于 <a '
            'href="https://github.com/Project-HAMi/HAMi/tree/4707fb02c91c545bc7343ce26dba4c32919f9a3e">Project-HAMi/HAMi '
            'v2.10.0</a> 与 <a href="https://project-hami.io/docs">HAMi 官方文档</a> 整理 · 基于 <a '
            'href="https://kubernetes.io/blog/">Kubernetes 官方 Blog</a>、<a '
            'href="https://kubernetes.io/feed.xml">Kubernetes Blog RSS</a>、<a '
            'href="https://kubernetes.io/blog/2026/08/26/kubernetes-v1-37-release/">v1.37 Release '
            '页面</a>、<a href="https://kubernetes.io/docs/">Kubernetes 官方文档</a>、<a '
            'href="https://kep.k8s.io/5966">相关 KEP</a> 与 <a '
            'href="https://github.com/kubernetes/kubernetes/tree/f78e722310e50bcaca9276be22276d9e91d91308">v1.37.1 '
            'exact source</a> 整理 · 基于 <a '
            'href="https://kubernetes.io/docs/concepts/scheduling-eviction/">Kubernetes '
            'Scheduling, Preemption and Eviction 官方文档</a> 与 <a '
            'href="https://github.com/kubernetes/kubernetes/tree/f78e722310e50bcaca9276be22276d9e91d91308">kubernetes/kubernetes '
            'v1.37.1 源码</a> 整理 · 基于 <a '
            'href="https://github.com/koordinator-sh/koordinator">Koordinator</a>、<a '
            'href="https://github.com/kubernetes-sigs/kueue/releases/tag/v0.20.2">Kueue v0.20.2 Release</a>、<a '
            'href="https://github.com/kubernetes-sigs/kueue/tree/b0fbbfe44ff20ee7f74cc0485c1a6812fe999a93">Kueue tag object</a>、<a '
            'href="https://github.com/kubernetes-sigs/kueue/tree/296ec3db567abbe36b65a63695710e3d3f3d0bdb">Kueue exact source</a>、<a '
            'href="https://github.com/ai-dynamo/grove/releases/tag/v0.1.0-alpha.16">Grove alpha.16 Release</a>、<a '
            'href="https://github.com/ai-dynamo/grove/tree/e33b8353e66dd6ed86fd4913660f88f8dbd17955">Grove alpha.16 source</a>、<a '
            'href="https://github.com/kai-scheduler/KAI-Scheduler/releases/tag/v0.18.6">KAI-Scheduler v0.18.6 Release</a>、<a '
            'href="https://github.com/kai-scheduler/KAI-Scheduler/tree/279f61c6d55b20bd47a43f2560c1b4f646a55547">KAI-Scheduler exact source</a> 与 <a '
            'href="https://github.com/kai-scheduler/KAI-Scheduler/tree/5922dc7d1a4661d3fc43d60943f92a775c892bdc">v0.20.1 '
            'tag-only 边界</a>、<a '
            'href="https://github.com/volcano-sh/volcano/releases/tag/v1.16.0">Volcano v1.16.0 Release</a>、<a '
            'href="https://github.com/volcano-sh/volcano/tree/b4ad252f3fd42c766d11d204e97622cddbbe4bd5">Volcano tag object</a>、<a '
            'href="https://github.com/volcano-sh/volcano/tree/41f27d567fb5bdaf2cab01e1caaf48f7e266eefb">Volcano exact source</a> 官方资料整理 · 基于 <a '
            'href="https://github.com/volcano-sh/website/blob/f5258704d7ef5bda28f31ba51950cdea9adbe921/versioned_docs/version-v1.15.0/KeyFeatures/cloudNativeColocation.md">Cloud '
            'Native Colocation</a>、<a '
            'href="https://github.com/volcano-sh/website/blob/f5258704d7ef5bda28f31ba51950cdea9adbe921/versioned_docs/version-v1.15.0/KeyFeatures/QueueResourceManagement.md">Queue '
            'Resource Management</a> 与 <a '
            'href="https://github.com/volcano-sh/helm-charts/tree/c2050e3debe58dbcdf9bb75b667799eec9409513">Helm '
            'Charts</a> 官方资料整理 · 基于 <a '
            'href="https://github.com/kserve/kserve/tree/d1482554fc4f66dd41aee70e01f5174e24f265bd">kserve/kserve '
            'v0.21.0 源码</a>、<a '
            'href="https://github.com/kserve/kserve/tree/bb22cc477a6bd317bb2c7e357a85efcab8c7462a">未发布 '
            'master 快照</a> 与 <a '
            'href="https://github.com/kserve/website/tree/71c8b22a05d6be72560b2cc326865930063cd0e8">KServe '
            '官网快照</a> 整理 · 基于 <a '
            'href="https://github.com/kubeflow/community-distribution/tree/26.03.1">kubeflow/community-distribution '
            '26.03.1</a> 与 <a href="https://www.kubeflow.org/">Kubeflow 官方文档</a> 整理'},
 {'src': '/data/Lustre-3FS-Deep-Dive.md',
  'dst': '/data/Lustre-3FS-Deep-Dive.html',
  'href': '/Lustre-3FS-Deep-Dive.html',
  'title': 'AI 存储与文件系统：Lustre 与 3FS',
  'category': '存储',
  'hero': 'AI 存储与文件系统：Lustre 与 3FS',
  'subtitle': 'HPC 并行文件系统、AI 原生分布式文件系统、RDMA/NVMe 与 KVCache 存储层选型解析',
  'meta': 'Lustre 官方资料 · deepseek-ai/3fs main@22fca04 · 2026-10-16',
  'summary': '覆盖 Lustre MDS/OSS/OST/LNet、3FS Meta/Storage/CRAQ/USRBIO、AI dataloader、checkpoint、KV '
             'cache 与生产选型。',
  'footer': '基于 <a href="https://wiki.lustre.org/Introduction_to_Lustre">Lustre Wiki</a>、<a '
            'href="https://github.com/deepseek-ai/3fs/tree/22fca04564c7cc230fd8b9523b8b92864e1dad47">deepseek-ai/3fs '
            'main@22fca04</a> 与 <a href="https://arxiv.org/html/2408.14158v1">Fire-Flyer AI-HPC '
            '论文</a> 整理'},
 {'src': '/data/Teleport-Deep-Dive.md',
  'dst': '/data/Teleport-Deep-Dive.html',
  'href': '/Teleport-Deep-Dive.html',
  'title': '基础设施访问治理：Self-hosted 平台对比',
  'category': '访问治理',
  'hero': '基础设施访问治理：Self-hosted 平台对比',
  'subtitle': 'Teleport、The Bastion、Warpgate 与 Boundary/Pomerium/Guacamole 的身份、协议、审计和运维比较',
  'meta': 'Teleport v18.10.0 · Bastion v3.24.01 · Warpgate v0.29.2 · Boundary v0.21.3 · Pomerium '
          'v0.33.4 · Guacamole 1.6.0 tag-only · 2026-10-16',
  'summary': '覆盖六个平台的统一能力矩阵、信任边界、短期凭据、RBAC/JIT、SSH/Kubernetes/数据库/HTTP/RDP/VNC '
             '协议审计、录制/SIEM、HA、迁移验收和许可证商业边界。',
  'footer': '基于 <a '
            'href="https://github.com/gravitational/teleport/tree/ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d">Teleport '
            'v18.10.0 源码</a>、<a '
            'href="https://github.com/ovh/the-bastion/releases/tag/v3.24.01">The Bastion '
            'v3.24.01</a>、<a '
            'href="https://github.com/warp-tech/warpgate/releases/tag/v0.29.2">Warpgate '
            'v0.29.2</a>、<a href="https://developer.hashicorp.com/boundary/docs/concepts">Boundary '
            '官方文档</a>、<a href="https://github.com/pomerium/pomerium/releases/tag/v0.33.4">Pomerium '
            'v0.33.4</a>、<a href="https://www.pomerium.com/docs">Pomerium 官方文档</a> 与 <a '
            'href="https://guacamole.apache.org/doc/gug/">Guacamole 官方手册</a> 整理'},
 {'src': '/data/Multica-Deep-Dive.md',
  'dst': '/data/Multica-Deep-Dive.html',
  'href': '/Multica-Deep-Dive.html',
  'title': 'Agent 协作与编排：Multica',
  'category': 'Agent 协作',
  'hero': 'Agent 协作与编排：Multica',
  'subtitle': 'AI-native 团队任务管理、coding agent 协作编排、本地执行与自托管架构解析',
  'meta': 'Multica v0.6.2 · source@7ab92d7 · main@7ab92d7 · 2026-10-16',
  'summary': '覆盖 Issue 四类 lifecycle 与 Triage、Task/runs、Agent/Runtime、25 种 protocol family、Codex '
             'usage/thread、Channel、Desktop、Squad、Autopilot、MCP 与无 Sandbox 边界。',
  'footer': '基于 <a '
            'href="https://github.com/multica-ai/multica/tree/7ab92d7622ecd81d179a8d83ae2dea74835a5069">multica-ai/multica '
            'v0.6.2 源码</a> 与 <a href="https://multica.ai/docs">Multica 官方文档</a> 整理'},
 {'src': '/data/E2B-Deep-Dive.md',
  'dst': '/data/E2B-Deep-Dive.html',
  'href': '/E2B-Deep-Dive.html',
  'title': 'Sandbox 与执行环境：E2B',
  'category': 'Sandbox',
  'hero': 'Sandbox 与执行环境：E2B',
  'subtitle': 'AI Sandbox、Firecracker microVM、Orchestrator、envd 与自托管架构解析',
  'meta': 'E2B Infra 2026.30 · source@f32ee8a · SDK main@62a17dfc · Agent Sandbox v1.0.7@807cc371 · '
          '2026-10-16',
  'summary': '覆盖 Firecracker、Sandbox fork、filesystem-only resume、workload '
             'identity、Secrets、日志与集群管理、团队配额和计量，以及 Agent Sandbox v1.0.7 的 bearer-token、流式命令、WarmPool 与迁移边界。',
  'footer': '基于 <a '
            'href="https://github.com/e2b-dev/infra/tree/f32ee8a2a50052f32e3632ceb451111a98dd5104">e2b-dev/infra '
            '2026.30</a>、<a '
            'href="https://github.com/e2b-dev/e2b/tree/62a17dfc3f11439d1d06bfb9bb515eadc5adfcd3">E2B '
            'SDK 主线快照</a> 与 <a '
            'href="https://github.com/kubernetes-sigs/agent-sandbox/releases/tag/v1.0.7">Agent Sandbox v1.0.7 Release</a>、<a '
            'href="https://github.com/kubernetes-sigs/agent-sandbox/tree/b3832ed88cb8acc57cc5e81072f551d52f14b32f">tag object</a> 与 <a '
            'href="https://github.com/kubernetes-sigs/agent-sandbox/tree/807cc37107bd7c012115afac9fa9c3b77b8365c2">exact source</a> 官方资料整理'},
 {'src': '/data/model_release_timeline.md',
  'dst': '/data/model_release_timeline.html',
  'href': '/model_release_timeline.html',
  'title': '模型发布时间时间线',
  'category': '模型时间线',
  'hero': '模型发布时间时间线',
  'subtitle': '2022—2026 九大阵营主线公开模型的首次发布与开放形态',
  'meta': '2022-01—2026-10-16 · 126 条记录 · 审校日期 2026-10-16',
  'summary': '按首次公开日期整理九个模型阵营的主线版本，并支持按供应商、年份、多模态和开放权重筛选及 CSV/JSON/Markdown 导出。',
  'footer': '事实来源为 <a '
            'href="/model_release_timeline.md">model_release_timeline.md</a>；每条记录保留对应的官方公告、模型页、技术报告或官方仓库链接。',
  'type': 'timeline'}]

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


def rewrite_document_links(body, source):
    """Resolve registered local Markdown links to pages, preserving query/fragment."""
    pages = {Path(doc["src"]).resolve(): doc["href"] for doc in DOCS}
    source_dir = Path(source).resolve().parent

    def replace(match):
        url = urlsplit(unescape(match.group(1)))
        if url.scheme or url.netloc or not url.path.endswith(".md"):
            return match.group(0)
        path = Path(unquote(url.path))
        if path.is_absolute() and path.resolve() in pages:
            pass
        elif url.path.startswith("/"):
            # Root-relative website links name files in the source directory.
            path = source_dir / url.path.lstrip("/")
        elif not path.is_absolute():
            path = source_dir / path
        page = pages.get(path.resolve())
        if page is None:
            return match.group(0)
        target = urlunsplit(("", "", page, url.query, url.fragment))
        return f'href="{escape(target, quote=True)}"'

    return re.sub(r'href="([^"]*)"', replace, body)

def wrap_tables(body):
    """Give ordinary Markdown tables their own keyboard-accessible scroll area."""
    def repl(match):
        table = match.group(0)
        if re.match(r'<table\b[^>]*class="[^"]*\btimeline-table\b', table):
            return table
        return (
            '<div class="table-wrap" role="region" aria-label="可横向滚动的表格" tabindex="0">'
            f'{table}</div>'
        )

    return re.sub(r"<table\b[^>]*>.*?</table>", repl, body, flags=re.S)


TIMELINE_COLUMNS = (
    ("release_date", "发布时间"),
    ("supplier", "公司 / 阵营"),
    ("model", "模型"),
    ("type", "类型"),
    ("release_form", "发布形态"),
    ("features", "关键特点"),
    ("lineage", "前后继关系"),
    ("official_source", "官方来源"),
    ("notes", "备注"),
)
TIMELINE_MULTIMODAL_RE = re.compile(r"多模态|全模态|原生视觉|视觉|语音")
TIMELINE_OPEN_SOURCE_RE = re.compile(
    r"开放权重|开源|Apache(?:[- ]?2(?:\.0)?)?|MIT(?:\s+许可)?|open[- ]weights?",
    re.IGNORECASE,
)


def _html_fragment_text(fragment):
    """Return readable text from a small HTML table-cell fragment."""
    text = re.sub(r"<[^>]+>", "", fragment)
    return unescape(text).strip()


def _timeline_year(value):
    match = re.search(r"\b(20\d{2})\b", value)
    return match.group(1) if match else ""


def _timeline_row_metadata(cells):
    """Derive stable filter metadata from one rendered timeline row."""
    values = [_html_fragment_text(cell) for cell in cells]
    release_date, supplier, _, model_type, release_form, features, _, _, notes = values
    multimodal = bool(TIMELINE_MULTIMODAL_RE.search(model_type))
    open_source_text = " ".join(
        (model_type, release_form, features, notes)
    )
    open_source = bool(TIMELINE_OPEN_SOURCE_RE.search(open_source_text))
    return {
        "year": _timeline_year(release_date),
        "supplier": supplier,
        "multimodal": "yes" if multimodal else "no",
        "open_source": "yes" if open_source else "no",
    }


def _timeline_checkbox_group(name, values):
    labels = []
    for index, value in enumerate(values):
        control_id = f"timeline-{name}-{index}"
        labels.append(
            f'<label class="timeline-checkbox" for="{escape(control_id, quote=True)}">'
            f'<input type="checkbox" id="{escape(control_id, quote=True)}" '
            f'name="{escape(name, quote=True)}" value="{escape(value, quote=True)}" '
            f'data-filter="{escape(name, quote=True)}">'
            f'<span>{escape(value)}</span></label>'
        )
    return "\n".join(labels)


def enhance_timeline_body(body):
    """Add filter metadata and controls to the timeline's main Markdown table."""
    table_match = re.search(r"<table\b[^>]*>.*?</table>", body, flags=re.S)
    if table_match is None:
        raise ValueError("Timeline document must contain a Markdown table")

    table_html = table_match.group(0)
    tbody_match = re.search(r"(<tbody\b[^>]*>)(.*?)(</tbody>)", table_html, flags=re.S)
    if tbody_match is None:
        raise ValueError("Timeline table must contain a tbody")

    row_matches = re.findall(
        r"<tr\b[^>]*>.*?</tr>", tbody_match.group(2), flags=re.S
    )
    if not row_matches:
        raise ValueError("Timeline table must contain at least one data row")

    enhanced_rows = []
    metadata_rows = []
    for row in row_matches:
        cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row, flags=re.S)
        if len(cells) != len(TIMELINE_COLUMNS):
            raise ValueError(
                "Timeline table rows must contain exactly "
                f"{len(TIMELINE_COLUMNS)} columns"
            )
        metadata = _timeline_row_metadata(cells)
        metadata_rows.append(metadata)
        attributes = " ".join(
            f'data-{key.replace("_", "-")}="{escape(value, quote=True)}"'
            for key, value in metadata.items()
        )
        enhanced_rows.append(
            re.sub(
                r"<tr\b[^>]*>",
                f'<tr {attributes}>',
                row,
                count=1,
            )
        )

    new_tbody = (
        tbody_match.group(1)
        + "\n"
        + "\n".join(enhanced_rows)
        + "\n"
        + tbody_match.group(3)
    )
    table_html = table_html[: tbody_match.start()] + new_tbody + table_html[tbody_match.end() :]
    table_html = table_html.replace(
        "<table>",
        '<table class="timeline-table" id="timeline-table" '
        'aria-describedby="timeline-result-count">',
        1,
    )
    table_html = (
        '<div class="timeline-table-wrap" role="region" aria-label="模型时间线表格" tabindex="0">'
        f'{table_html}</div>'
    )

    suppliers = list(dict.fromkeys(row["supplier"] for row in metadata_rows))
    years = sorted(
        {row["year"] for row in metadata_rows if row["year"]},
        key=lambda value: int(value),
    )
    controls = f"""
<section class="timeline-controls" id="timeline-controls" aria-label="时间线筛选与导出">
  <div class="timeline-filter-panel">
    <div class="timeline-panel-title">筛选时间线</div>
    <div class="timeline-filter-grid">
      <fieldset class="timeline-fieldset">
        <legend>供应商（可多选）</legend>
        <div class="timeline-checkbox-list" aria-label="按供应商筛选">
          {_timeline_checkbox_group("supplier", suppliers)}
        </div>
      </fieldset>
      <fieldset class="timeline-fieldset">
        <legend>年份（可多选）</legend>
        <div class="timeline-checkbox-list" aria-label="按年份筛选">
          {_timeline_checkbox_group("year", years)}
        </div>
      </fieldset>
      <div class="timeline-select-group">
        <label for="timeline-multimodal-filter">多模态</label>
        <select id="timeline-multimodal-filter" class="timeline-select" aria-label="按多模态筛选">
          <option value="">全部</option>
          <option value="yes">是</option>
          <option value="no">否</option>
        </select>
      </div>
      <div class="timeline-select-group">
        <label for="timeline-open-source-filter">开源 / 开放权重</label>
        <select id="timeline-open-source-filter" class="timeline-select" aria-label="按开源或开放权重筛选">
          <option value="">全部</option>
          <option value="yes">是</option>
          <option value="no">否</option>
        </select>
      </div>
    </div>
    <div class="timeline-filter-actions">
      <button id="timeline-clear-filters" class="timeline-button timeline-button-secondary" type="button">清除筛选</button>
      <span id="timeline-result-count" class="timeline-result-count" aria-live="polite">显示 {len(metadata_rows)} / {len(metadata_rows)} 条</span>
    </div>
  </div>
  <div class="timeline-export-panel" aria-label="导出当前筛选结果">
    <span class="timeline-panel-title">导出当前结果</span>
    <div class="timeline-export-actions">
      <button id="timeline-export-csv" class="timeline-button" type="button">导出 CSV</button>
      <button id="timeline-export-json" class="timeline-button" type="button">导出 JSON</button>
      <button id="timeline-export-markdown" class="timeline-button" type="button">导出 Markdown</button>
    </div>
  </div>
  <p id="timeline-empty-state" class="timeline-empty-state" hidden>当前筛选没有匹配记录。</p>
</section>
"""
    enhanced_body = (
        body[: table_match.start()]
        + controls
        + table_html
        + body[table_match.end() :]
    )
    return enhanced_body


TIMELINE_SCRIPT = r"""
<script>
  (() => {
    const timelineColumnKeys = [
      'release_date', 'supplier', 'model', 'type', 'release_form',
      'features', 'lineage', 'official_source', 'notes'
    ];
    const timelineColumnLabels = [
      '发布时间', '公司 / 阵营', '模型', '类型', '发布形态',
      '关键特点', '前后继关系', '官方来源', '备注'
    ];
    const table = document.querySelector('#timeline-table');
    const rows = table ? Array.from(table.querySelectorAll('tbody tr')) : [];
    const count = document.querySelector('#timeline-result-count');
    const emptyState = document.querySelector('#timeline-empty-state');
    const exportButtons = [
      document.querySelector('#timeline-export-csv'),
      document.querySelector('#timeline-export-json'),
      document.querySelector('#timeline-export-markdown')
    ].filter(Boolean);

    function cellText(cell) {
      return cell ? cell.textContent.trim() : '';
    }

    function cellMarkdown(cell) {
      if (!cell) return '';
      const clone = cell.cloneNode(true);
      clone.querySelectorAll('a').forEach((link) => {
        const label = link.textContent.trim();
        const href = link.getAttribute('href') || '';
        link.replaceWith(document.createTextNode(`[${label}](${href})`));
      });
      return clone.textContent.trim();
    }

    const timelineRecords = rows.map((row, index) => {
      const cells = Array.from(row.cells);
      const record = {
        release_date: cellText(cells[0]),
        supplier: row.dataset.supplier || cellText(cells[1]),
        model: cellText(cells[2]),
        type: cellText(cells[3]),
        release_form: cellText(cells[4]),
        features: cellText(cells[5]),
        lineage: cellText(cells[6]),
        official_source: cellMarkdown(cells[7]),
        notes: cellText(cells[8]),
        year: row.dataset.year || '',
        multimodal: row.dataset.multimodal === 'yes',
        open_source: row.dataset.openSource === 'yes',
        _sourceText: cellText(cells[7]),
        _row: row,
        _index: index
      };
      return record;
    });

    function selectedValues(filterName) {
      return Array.from(
        document.querySelectorAll(`input[data-filter="${filterName}"]:checked`)
      ).map((input) => input.value);
    }

    function filterState() {
      return {
        supplier: selectedValues('supplier'),
        year: selectedValues('year'),
        multimodal: document.querySelector('#timeline-multimodal-filter')?.value || '',
        open_source: document.querySelector('#timeline-open-source-filter')?.value || ''
      };
    }

    function splitParameter(value) {
      return (value || '').split(',').map((item) => item.trim()).filter(Boolean);
    }

    function restoreFiltersFromUrl() {
      const params = new URLSearchParams(window.location.search);
      for (const filterName of ['supplier', 'year']) {
        const selected = new Set(splitParameter(params.get(filterName)));
        document.querySelectorAll(`input[data-filter="${filterName}"]`).forEach((input) => {
          input.checked = selected.has(input.value);
        });
      }
      for (const [filterName, elementId] of [
        ['multimodal', '#timeline-multimodal-filter'],
        ['open_source', '#timeline-open-source-filter']
      ]) {
        const element = document.querySelector(elementId);
        const value = params.get(filterName);
        if (element && (value === 'yes' || value === 'no')) element.value = value;
      }
    }

    function syncFiltersToUrl() {
      const state = filterState();
      const url = new URL(window.location.href);
      for (const filterName of ['supplier', 'year']) {
        if (state[filterName].length) {
          url.searchParams.set(filterName, state[filterName].join(','));
        } else {
          url.searchParams.delete(filterName);
        }
      }
      for (const filterName of ['multimodal', 'open_source']) {
        if (state[filterName]) {
          url.searchParams.set(filterName, state[filterName]);
        } else {
          url.searchParams.delete(filterName);
        }
      }
      window.history.replaceState(
        null,
        '',
        `${url.pathname}${url.search}${url.hash}`
      );
    }

    function matches(record, state) {
      if (state.supplier.length && !state.supplier.includes(record.supplier)) return false;
      if (state.year.length && !state.year.includes(record.year)) return false;
      if (state.multimodal && (record.multimodal ? 'yes' : 'no') !== state.multimodal) return false;
      if (state.open_source && (record.open_source ? 'yes' : 'no') !== state.open_source) return false;
      return true;
    }

    function visibleRecords() {
      const state = filterState();
      return timelineRecords.filter((record) => matches(record, state));
    }

    function applyTimelineFilters() {
      const visible = visibleRecords();
      const visibleRows = new Set(visible);
      timelineRecords.forEach((record) => {
        record._row.hidden = !visibleRows.has(record);
      });
      if (count) count.textContent = `显示 ${visible.length} / ${timelineRecords.length} 条`;
      if (emptyState) emptyState.hidden = visible.length !== 0;
      exportButtons.forEach((button) => {
        button.disabled = visible.length === 0;
        button.setAttribute('aria-disabled', String(visible.length === 0));
      });
      return visible;
    }

    function csvCell(value) {
      const text = String(value ?? '');
      return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
    }

    function exportValue(record, key) {
      return key === 'official_source' ? record._sourceText : record[key];
    }

    function toExportRecord(record) {
      const result = {};
      timelineColumnKeys.forEach((key) => { result[key] = record[key]; });
      result.year = record.year;
      result.multimodal = record.multimodal;
      result.open_source = record.open_source;
      return result;
    }

    function downloadFile(filename, content, mimeType) {
      const blob = new Blob([content], {type: `${mimeType};charset=utf-8`});
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 0);
    }

    function exportCsv(records) {
      const header = timelineColumnLabels.map(csvCell).join(',');
      const lines = records.map((record) =>
        timelineColumnKeys.map((key) => csvCell(exportValue(record, key))).join(',')
      );
      downloadFile(
        'model-release-timeline-filtered.csv',
        `\ufeff${[header, ...lines].join('\r\n')}\r\n`,
        'text/csv'
      );
    }

    function exportJson(records) {
      downloadFile(
        'model-release-timeline-filtered.json',
        JSON.stringify(records.map(toExportRecord), null, 2),
        'application/json'
      );
    }

    function markdownCell(value) {
      return String(value ?? '').replace(/\|/g, '\\|').replace(/\r?\n/g, '<br>');
    }

    function exportMarkdown(records) {
      const lines = [
        '# 模型发布时间时间线（筛选结果）',
        '',
        `| ${timelineColumnLabels.join(' | ')} |`,
        `| ${timelineColumnLabels.map(() => '---').join(' | ')} |`
      ];
      records.forEach((record) => {
        const values = timelineColumnKeys.map((key) =>
          key === 'official_source' ? record[key] : markdownCell(record[key])
        );
        lines.push(`| ${values.join(' | ')} |`);
      });
      if (!records.length) {
        lines.push('', '> 当前筛选没有匹配记录。');
      }
      downloadFile(
        'model-release-timeline-filtered.md',
        `${lines.join('\n')}\n`,
        'text/markdown'
      );
    }

    function clearFilters() {
      document.querySelectorAll('input[data-filter]').forEach((input) => { input.checked = false; });
      document.querySelectorAll('#timeline-multimodal-filter, #timeline-open-source-filter').forEach((select) => {
        select.value = '';
      });
      syncFiltersToUrl();
      applyTimelineFilters();
    }

    document.querySelectorAll('input[data-filter], #timeline-multimodal-filter, #timeline-open-source-filter')
      .forEach((control) => control.addEventListener('change', () => {
        syncFiltersToUrl();
        applyTimelineFilters();
      }));
    document.querySelector('#timeline-clear-filters')?.addEventListener('click', clearFilters);
    document.querySelector('#timeline-export-csv')?.addEventListener('click', () => exportCsv(visibleRecords()));
    document.querySelector('#timeline-export-json')?.addEventListener('click', () => exportJson(visibleRecords()));
    document.querySelector('#timeline-export-markdown')?.addEventListener('click', () => exportMarkdown(visibleRecords()));

    restoreFiltersFromUrl();
    applyTimelineFilters();
    window.timelineRecords = timelineRecords;
    window.applyTimelineFilters = applyTimelineFilters;
    window.exportTimelineCsv = exportCsv;
    window.exportTimelineJson = exportJson;
    window.exportTimelineMarkdown = exportMarkdown;
  })();
</script>
"""

THEME_BOOTSTRAP = r"""
<script>
(() => {
  const key = 'ai-docs-theme';
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  const normalize = (value) => ['light', 'dark', 'system'].includes(value) ? value : 'system';
  let preference = 'system';
  try { preference = normalize(localStorage.getItem(key)); } catch (_) {}
  function apply() {
    const theme = preference === 'system' ? (system.matches ? 'dark' : 'light') : preference;
    document.documentElement.dataset.theme = theme;
    document.documentElement.dataset.themePreference = preference;
    document.querySelectorAll('[data-theme-select]').forEach((select) => { select.value = preference; });
    window.dispatchEvent(new CustomEvent('docs-theme-change', { detail: { theme, preference } }));
  }
  window.docsTheme = {
    setPreference(value) {
      preference = normalize(value);
      try { localStorage.setItem(key, preference); } catch (_) {}
      apply();
    },
    getPreference: () => preference,
    getResolved: () => document.documentElement.dataset.theme
  };
  system.addEventListener('change', () => { if (preference === 'system') apply(); });
  window.addEventListener('storage', (event) => {
    if (event.key === key || event.key === null) {
      preference = normalize(event.newValue);
      apply();
    }
  });
  apply();
})();
</script>
"""

SITE_NAV = """
<a class="skip-link" href="#main-content">跳到正文</a>
<header class="site-header">
  <nav class="site-nav" aria-label="站点导航">
    <a class="site-name" href="/">AI 基础设施深度文档</a>
    <a class="site-home" href="/">首页</a>
    <div class="theme-control">
      <label for="theme-select">主题</label>
      <select id="theme-select" data-theme-select disabled>
        <option value="light">明亮</option>
        <option value="dark">暗色</option>
        <option value="system" selected>跟随系统</option>
      </select>
    </div>
  </nav>
</header>
"""

THEME_CONTROLS_SCRIPT = """
<script>
document.querySelectorAll('[data-theme-select]').forEach((select) => {
  select.value = window.docsTheme.getPreference();
  select.disabled = false;
  select.addEventListener('change', () => window.docsTheme.setPreference(select.value));
});
const siteHeader = document.querySelector('.site-header');
const updateHeaderHeight = () => document.documentElement.style.setProperty('--header-height', `${siteHeader.offsetHeight}px`);
updateHeaderHeight();
new ResizeObserver(updateHeaderHeight).observe(siteHeader);
</script>
"""

INDEX_SCRIPT = r"""
<script>
(() => {
  const search = document.querySelector('#doc-search');
  const category = document.querySelector('#doc-category');
  const clear = document.querySelector('#doc-clear');
  const count = document.querySelector('#doc-result-count');
  const empty = document.querySelector('#doc-empty-state');
  const cards = [...document.querySelectorAll('.doc-card')].map((node) => ({
    node,
    category: node.dataset.category,
    text: `${node.querySelector('h2').textContent} ${node.querySelector('.doc-card-summary').textContent}`.toLocaleLowerCase()
  }));
  function filter() {
    const query = search.value.trim().toLocaleLowerCase();
    let visible = 0;
    cards.forEach((card) => {
      const matches = card.text.includes(query) && (!category.value || card.category === category.value);
      card.node.hidden = !matches;
      if (matches) visible++;
    });
    count.textContent = `显示 ${visible} / ${cards.length} 篇`;
    empty.hidden = visible !== 0;
    clear.disabled = !search.value && !category.value;
  }
  search.disabled = false;
  category.disabled = false;
  search.addEventListener('input', filter);
  category.addEventListener('change', filter);
  clear.addEventListener('click', () => {
    search.value = '';
    category.value = '';
    filter();
    search.focus();
  });
  filter();
})();
</script>
"""

TOC_SCRIPT = r"""
<script>
(() => {
  const tocButton = document.querySelector('.toc-fab');
  const tocBackdrop = document.querySelector('.toc-backdrop');
  const tocSidebar = document.querySelector('#doc-sidebar');
  if (!tocButton || !tocBackdrop || !tocSidebar) return;
  const close = tocSidebar.querySelector('.toc-close');
  const mobile = window.matchMedia('(max-width: 768px)');
  const background = [...document.querySelectorAll('.site-header, .doc-hero-container, .doc-shell > main, .toc-fab')];
  let returnFocus = tocButton;
  function setTocOpen(open) {
    open = open && mobile.matches;
    const wasOpen = document.body.classList.contains('toc-open');
    if (open && !wasOpen) returnFocus = document.activeElement;
    document.body.classList.toggle('toc-open', open);
    tocButton.setAttribute('aria-expanded', String(open));
    tocBackdrop.hidden = !open;
    tocSidebar.inert = mobile.matches && !open;
    background.forEach((node) => { node.inert = open; });
    if (mobile.matches) tocSidebar.setAttribute('aria-hidden', String(!open));
    else tocSidebar.removeAttribute('aria-hidden');
    if (open) {
      tocSidebar.setAttribute('role', 'dialog');
      tocSidebar.setAttribute('aria-modal', 'true');
      close.focus();
    } else {
      tocSidebar.removeAttribute('role');
      tocSidebar.removeAttribute('aria-modal');
      if (mobile.matches && (wasOpen || tocSidebar.contains(document.activeElement))) {
        (returnFocus?.isConnected ? returnFocus : tocButton).focus();
      } else if (wasOpen) {
        tocSidebar.querySelector('a')?.focus();
      }
    }
  }
  tocButton.disabled = false;
  tocButton.addEventListener('click', () => setTocOpen(true));
  close.addEventListener('click', () => setTocOpen(false));
  tocBackdrop.addEventListener('click', () => setTocOpen(false));
  tocSidebar.addEventListener('click', (event) => {
    if (event.target.closest('a')) setTocOpen(false);
  });
  document.addEventListener('keydown', (event) => {
    if (!document.body.classList.contains('toc-open')) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      setTocOpen(false);
    } else if (event.key === 'Tab') {
      const controls = [...tocSidebar.querySelectorAll('a[href], button:not(:disabled), [tabindex="0"]')]
        .filter((node) => node.getClientRects().length);
      const first = controls[0];
      const last = controls[controls.length - 1];
      if (!tocSidebar.contains(document.activeElement) || (event.shiftKey && document.activeElement === first)) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  });
  mobile.addEventListener('change', () => setTocOpen(false));
  setTocOpen(false);
})();
</script>
"""

MERMAID_SCRIPT = r"""
<script type="module">
const diagrams = [...document.querySelectorAll('.mermaid')];
if (diagrams.length) {
  // Keep text separately: Mermaid replaces the DOM with SVG after each render.
  const sources = new Map(diagrams.map((node) => [node, node.textContent.trim()]));
  let desiredTheme = window.docsTheme.getResolved();
  let renderedTheme = null;
  let running = false;
  let serial = 0;
  let mermaid;
  const fallback = (node) => {
    node.textContent = sources.get(node);
    delete node.dataset.rendered;
    node.dataset.mermaidError = 'true';
    node.title = '图表加载或渲染失败，显示原始定义';
  };
  async function renderDiagrams() {
    if (running || !mermaid) return;
    running = true;
    try {
      // Merge rapid switches and never run Mermaid's renderer concurrently.
      while (renderedTheme !== desiredTheme) {
        const theme = desiredTheme;
        const style = getComputedStyle(document.documentElement);
        const color = (name) => style.getPropertyValue(name).trim();
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: 'strict',
          suppressErrorRendering: true,
          theme: 'base',
          themeVariables: {
            darkMode: theme === 'dark',
            background: color('--bg'),
            primaryColor: color('--bg-card'),
            primaryTextColor: color('--text'),
            primaryBorderColor: color('--border'),
            lineColor: color('--accent'),
            secondaryColor: color('--bg-code'),
            secondaryTextColor: color('--text'),
            tertiaryColor: color('--bg'),
            tertiaryTextColor: color('--text'),
            textColor: color('--text'),
            fontFamily: 'Inter, Noto Sans SC, sans-serif'
          }
        });
        for (const node of diagrams) {
          if (theme !== desiredTheme) break;
          try {
            const { svg, bindFunctions } = await mermaid.render(`docs-diagram-${++serial}`, sources.get(node));
            if (theme !== desiredTheme) break;
            node.innerHTML = svg;
            node.dataset.rendered = theme;
            delete node.dataset.mermaidError;
            node.removeAttribute('title');
            bindFunctions?.(node);
          } catch (_) {
            if (theme === desiredTheme) fallback(node);
          }
        }
        renderedTheme = theme;
      }
    } finally { running = false; }
  }
  window.addEventListener('docs-theme-change', (event) => {
    desiredTheme = event.detail.theme;
    void renderDiagrams();
  });
  try {
    ({ default: mermaid } = await import('https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs'));
    await renderDiagrams();
  } catch (_) { diagrams.forEach(fallback); }
}
</script>
"""

PYGMENTS_LIGHT_STYLE = "friendly"
PYGMENTS_DARK_STYLE = "github-dark"


def _build_pygments_css():
    """Generate theme-aware Pygments token styles scoped to .highlight blocks.

    The container background is dropped so the shared `--bg-code` surface wins;
    the dark stylesheet is emitted twice (attribute selector and media query) to
    match how the site resolves light/dark.
    """
    def defs(style):
        css = HtmlFormatter(style=style).get_style_defs(".highlight")
        css = re.sub(r"^\.highlight \{[^}]*\}\n?", "", css, flags=re.M)
        css = css.replace("pre { line-height: 125%; }\n", "")
        return css

    light = defs(PYGMENTS_LIGHT_STYLE)
    dark = defs(PYGMENTS_DARK_STYLE)
    dark_attr = re.sub(r"^\.highlight\b", ':root[data-theme="dark"] .highlight', dark, flags=re.M)
    dark_media = re.sub(r"^\.highlight\b", ':root:not([data-theme]) .highlight', dark, flags=re.M)
    return (
        "/* ─── Pygments tokens (light) ─── */\n"
        + light
        + "\n/* ─── Pygments tokens (dark) ─── */\n"
        + dark_attr
        + "\n@media (prefers-color-scheme: dark) {\n"
        + dark_media
        + "\n}\n"
    )


PYGMENTS_CSS = _build_pygments_css()

LIGHT_PALETTE = """
  color-scheme: light;
  --bg: #f8fafc;
  --bg-card: #ffffff;
  --bg-code: #eef2f6;
  --text: #172033;
  --text-secondary: #526075;
  --accent: #1759a6;
  --accent-dim: #2563b6;
  --border: #cbd5e1;
  --green: #176538;
  --orange: #805600;
  --red: #b42318;
  --purple: #7043a1;
  --surface-hover: #e8f0fb;
  --backdrop: rgba(15, 23, 42, 0.48);
  --shadow: rgba(15, 23, 42, 0.12);
"""
DARK_PALETTE = """
  color-scheme: dark;
  --bg: #0d1117;
  --bg-card: #161b22;
  --bg-code: #1a1e26;
  --text: #e6edf3;
  --text-secondary: #a2adba;
  --accent: #58a6ff;
  --accent-dim: #1f6feb;
  --border: #30363d;
  --green: #3fb950;
  --orange: #d29922;
  --red: #ff7b72;
  --purple: #bc8cff;
  --surface-hover: #1c2c42;
  --backdrop: rgba(1, 4, 9, 0.68);
  --shadow: rgba(0, 0, 0, 0.35);
"""
CSS = PYGMENTS_CSS + (
    ":root {" + LIGHT_PALETTE + "}\n"
    ':root[data-theme="dark"] {' + DARK_PALETTE + "}\n"
    "@media (prefers-color-scheme: dark) { :root:not([data-theme]) {" + DARK_PALETTE + "} }\n"
) + """

* { margin: 0; padding: 0; box-sizing: border-box; }
:root { --header-height: 64px; }

html {
  scroll-behavior: smooth;
  scroll-padding-top: calc(var(--header-height) + 24px);
}

[hidden] { display: none !important; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
input, select, button { font: inherit; }
.site-header {
  position: sticky;
  top: 0;
  z-index: 30;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
}
.site-nav {
  max-width: 1360px;
  margin: 0 auto;
  padding: 12px 32px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 24px;
}
.site-name { color: var(--text); font-weight: 700; overflow-wrap: anywhere; }
.site-home { font-size: 0.9rem; }
.theme-control { margin-left: auto; display: flex; align-items: center; gap: 8px; font-size: 0.9rem; }
.theme-control select {
  min-height: 36px;
  padding: 4px 10px;
  background: var(--bg-code);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 6px;
}
.skip-link { position: fixed; top: -100px; left: 16px; z-index: 50; padding: 8px 16px; background: var(--bg-card); }
.skip-link:focus { top: 8px; }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; animation: none !important; }
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
  max-width: 1280px;
  margin: 0 auto;
}
.doc-shell {
  display: grid;
  grid-template-columns: minmax(220px, 260px) minmax(0, 860px);
  gap: 40px;
  align-items: start;
  justify-content: center;
  padding: 0 32px 120px;
}
.doc-container {
  max-width: 1160px;
  margin: 0 auto;
  padding: 40px 32px 120px;
}
.doc-hero-container {
  padding-top: 48px;
  padding-bottom: 0;
}
.doc-shell .doc-container {
  width: 100%;
  min-width: 0;
  margin: 0;
  padding: 0;
  overflow-wrap: anywhere;
}
.doc-container img { max-width: 100%; height: auto; }
.doc-sidebar {
  position: sticky;
  top: calc(var(--header-height) + 24px);
  max-height: calc(100dvh - var(--header-height) - 48px);
  overflow: auto;
  padding-bottom: 24px;
  overflow-wrap: anywhere;
}

/* ─── Hero ─── */
.doc-hero {
  text-align: left;
  padding: 0 0 32px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 32px;
  overflow-wrap: anywhere;
}
.doc-hero h1 {
  font-size: clamp(1.8rem, 3vw, 2.25rem);
  font-weight: 700;
  color: var(--text);
  margin-bottom: 12px;
}
.doc-hero .subtitle {
  font-size: 1.15em;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.doc-hero .meta {
  font-size: 0.9em;
  color: var(--text-secondary);
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
.toc-close { display: none; }

/* ─── Blockquotes ─── */
blockquote {
  border-left: 4px solid var(--accent-dim);
  background: var(--surface-hover);
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
  white-space: pre-wrap;
  font-family: monospace;
}
.mermaid[data-rendered] { white-space: normal; font-family: inherit; }
.mermaid svg {
  max-width: 100%;
  height: auto;
}

/* ─── Tables ─── */
.table-wrap {
  width: 100%;
  overflow-x: auto;
  margin: 16px 0 24px;
  border-radius: 8px;
}
.table-wrap table { margin: 0; overflow-wrap: normal; }
.table-wrap table:has(tr > :nth-child(3)) { min-width: 640px; }
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
tr:hover { background: var(--surface-hover); }

/* ─── Model release timeline ─── */
.timeline-controls {
  display: grid;
  gap: 18px;
  margin: 24px 0 28px;
}
.timeline-filter-panel,
.timeline-export-panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
}
.timeline-panel-title {
  display: block;
  margin-bottom: 12px;
  color: var(--accent);
  font-weight: 600;
}
.timeline-filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 200px), 1fr));
  gap: 16px;
  align-items: start;
}
.timeline-fieldset {
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
}
.timeline-fieldset legend {
  padding: 0 6px;
  color: var(--text-secondary);
  font-size: 0.9em;
}
.timeline-checkbox-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}
.timeline-checkbox {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text);
  font-size: 0.9em;
  cursor: pointer;
}
.timeline-checkbox input {
  accent-color: var(--accent);
  inline-size: 1rem;
  block-size: 1rem;
}
.timeline-select-group {
  display: grid;
  gap: 7px;
  color: var(--text-secondary);
  font-size: 0.9em;
}
.timeline-select {
  width: 100%;
  min-height: 40px;
  padding: 7px 10px;
  border: 1px solid var(--border);
  border-radius: 7px;
  background: var(--bg-code);
  color: var(--text);
  font: inherit;
}
.timeline-select:focus-visible,
.timeline-button:focus-visible,
.timeline-checkbox input:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.timeline-filter-actions,
.timeline-export-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
}
.timeline-export-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.timeline-button {
  min-height: 38px;
  padding: 7px 14px;
  border: 1px solid var(--accent-dim);
  border-radius: 7px;
  background: var(--surface-hover);
  color: var(--text);
  font: inherit;
  font-size: 0.9em;
  cursor: pointer;
}
.timeline-button:hover:not(:disabled) {
  border-color: var(--accent);
  background: var(--bg-code);
}
.timeline-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}
.timeline-button-secondary {
  border-color: var(--border);
  background: transparent;
}
.timeline-result-count {
  color: var(--text-secondary);
  font-size: 0.92em;
}
.timeline-empty-state {
  margin: 0;
  padding: 14px 16px;
  border: 1px solid var(--orange);
  border-radius: 8px;
  color: var(--orange);
}
.timeline-table-wrap {
  overflow-x: auto;
  margin: 16px 0 24px;
  border-radius: 10px;
}
.timeline-table {
  min-width: 1280px;
  margin: 0;
}
.timeline-table tbody tr[hidden] {
  display: none;
}

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
  background: var(--surface-hover);
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
  border-bottom: 1px solid var(--border);
}
.toc.toc-nested > ul > li {
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
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
.index-container { max-width: 1240px; padding-top: 48px; }
.index-tools {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(180px, 240px);
  gap: 16px;
  padding: 20px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg-card);
}
.index-field { display: grid; gap: 8px; min-width: 0; }
.index-field label { font-size: 0.9rem; font-weight: 600; }
.index-field input, .index-field select {
  min-width: 0;
  width: 100%;
  min-height: 44px;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
}
.index-field input::placeholder { color: var(--text-secondary); opacity: 1; }
.index-results { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: space-between; margin-top: 16px; }
.index-result-count { color: var(--text-secondary); font-size: 0.9rem; }
.index-clear {
  padding: 6px 12px;
  min-height: 40px;
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--accent);
  background: var(--bg-card);
  cursor: pointer;
}
.index-clear:disabled { color: var(--text-secondary); cursor: default; }
.index-empty { padding: 32px 20px; margin-top: 24px; text-align: center; border: 1px dashed var(--border); border-radius: 10px; color: var(--text-secondary); }
.doc-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin: 28px 0 48px;
}
.doc-card {
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 22px 24px;
  min-height: 180px;
  min-width: 0;
  overflow-wrap: anywhere;
  color: var(--text);
  transition: border-color 0.2s, background 0.2s;
}
.doc-card:hover {
  border-bottom-color: var(--accent);
  border-color: var(--accent-dim);
  background: var(--surface-hover);
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
  display: block;
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  color: var(--text-secondary);
  font-size: 0.86em;
}
.doc-card-category {
  align-self: flex-start;
  padding: 2px 8px;
  margin-bottom: 14px;
  border-radius: 4px;
  background: var(--surface-hover);
  color: var(--accent);
  font-size: 0.78rem;
  font-weight: 500;
}

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }

/* ─── Responsive ─── */
@media (max-width: 1100px) {
  .doc-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 768px) {
  :root { --header-height: 112px; }
  .site-nav { padding: 10px 16px; gap: 8px 16px; }
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
    box-shadow: 20px 0 44px var(--shadow);
    transform: translateX(-100%);
    visibility: hidden;
    transition: transform 0.22s ease;
    overscroll-behavior: contain;
  }
  body.toc-open .doc-sidebar {
    transform: translateX(0);
    visibility: visible;
  }
  .toc-close {
    display: block;
    width: 100%;
    min-height: 44px;
    margin-bottom: 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg-card);
    color: var(--text);
    cursor: pointer;
  }
  .doc-sidebar .toc {
    max-height: none;
  }
  .toc-backdrop {
    position: fixed;
    inset: 0;
    z-index: 41;
    background: var(--backdrop);
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
    background: var(--bg-card);
    color: var(--text);
    font: inherit;
    font-size: 0.9em;
    font-weight: 600;
    line-height: 1;
    box-shadow: 0 12px 32px var(--shadow);
    backdrop-filter: blur(10px);
  }
  .toc-fab:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 4px;
  }
  body.toc-open .toc-fab { visibility: hidden; }
  .doc-hero h1 { font-size: 1.8em; }
  h2 { font-size: 1.4em; }
  table { font-size: 0.82em; }
  th, td { padding: 8px 10px; }
  .timeline-filter-grid { grid-template-columns: 1fr; }
  .timeline-filter-panel,
  .timeline-export-panel { align-items: stretch; }
  .timeline-filter-actions,
  .timeline-export-panel { flex-direction: column; align-items: stretch; }
  .timeline-export-actions { display: grid; grid-template-columns: 1fr; }
  .timeline-button { width: 100%; }
}
@media (max-width: 640px) {
  .doc-grid, .index-tools { grid-template-columns: 1fr; }
  .doc-card { padding: 20px; }
  .index-container { padding-top: 32px; }
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
        "pymdownx.superfences",
        "pymdownx.highlight",
        "toc",
        "smarty",
        "sane_lists",
        "attr_list",
        "md_in_html",
        "pymdownx.details",
    ]
    extension_configs = {
        "toc": {
            "title": "目录",
            "toc_depth": 2,
            "slugify": slugify_heading,
        },
        "pymdownx.superfences": {
            "custom_fences": [
                {"name": "mermaid", "class": "mermaid", "format": fence_div_format}
            ],
        },
        "pymdownx.highlight": {
            "guess_lang": False,
            "use_pygments": True,
            "css_class": "highlight",
            "pygments_style": PYGMENTS_LIGHT_STYLE,
            "pygments_lang_class": False,
        },
    }

    body = markdown.markdown(
        md_text,
        extensions=extensions,
        extension_configs=extension_configs,
    )
    body = rewrite_document_links(body, doc["src"])
    timeline_script = ""
    if doc.get("type") == "timeline":
        body = enhance_timeline_body(body)
        timeline_script = TIMELINE_SCRIPT
    body = wrap_tables(body)
    body, toc_html = split_body_and_toc(body)
    sidebar_html = (
        '<aside id="doc-sidebar" class="doc-sidebar" aria-label="文档目录">\n'
        '<button class="toc-close" type="button">关闭目录</button>\n'
        '<a class="toc-home-link" href="/">首页</a>\n'
        f'{toc_html}\n</aside>'
        if toc_html
        else ""
    )
    mobile_toc_controls = (
        '<button class="toc-fab" type="button" aria-controls="doc-sidebar" '
        'aria-expanded="false" disabled>目录</button>\n'
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
{THEME_BOOTSTRAP}
<style>{CSS}</style>
</head>
<body>
{SITE_NAV}
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
  <main id="main-content" class="doc-container" tabindex="-1">
  {body}
  <div class="doc-footer">
    <p>{rewrite_document_links(doc["footer"], doc["src"])}</p>
  </div>
  </main>
</div>
</div>
{THEME_CONTROLS_SCRIPT}
{MERMAID_SCRIPT}
{TOC_SCRIPT}
{timeline_script}
</body>
</html>"""

    with open(doc["dst"], "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Rendered {doc['src']} → {doc['dst']} ({len(html)} bytes)")


def render_index():
    cards = []
    for doc in DOCS:
        category = doc.get("category") or "其他"
        if category not in CATEGORIES:
            category = "其他"
        cards.append(
            f"""<a class="doc-card" href="{escape(doc["href"], quote=True)}" data-category="{escape(category, quote=True)}">
  <span class="doc-card-category">{escape(category)}</span>
  <h2>{escape(doc["title"])}</h2>
  <p class="doc-card-summary">{escape(doc["summary"])}</p>
  <span class="doc-card-meta">{escape(doc["meta"])}</span>
</a>"""
        )

    categories = list(CATEGORIES)
    if any(doc.get("category") not in CATEGORIES for doc in DOCS):
        categories.append("其他")
    category_options = "".join(
        f'<option value="{escape(category, quote=True)}">{escape(category)}</option>'
        for category in categories
    )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 基础设施深度文档</title>
{THEME_BOOTSTRAP}
<style>{CSS}</style>
</head>
<body>
{SITE_NAV}
<main id="main-content" class="doc-container index-container" tabindex="-1">
  <div class="doc-hero">
    <h1>AI 基础设施深度文档</h1>
    <p class="subtitle">LLM 推理、压测、存储、Sandbox、基础设施访问治理、异构设备、AI 调度、模型服务与 MLOps 技术分析入口</p>
    <p class="meta">{len(DOCS)} 篇文档 · 架构、实现与生产实践</p>
  </div>
  <section class="index-tools" aria-label="文档搜索与分类">
    <div class="index-field">
      <label for="doc-search">搜索文档</label>
      <input id="doc-search" type="search" placeholder="搜索标题或摘要" autocomplete="off" disabled>
    </div>
    <div class="index-field">
      <label for="doc-category">主题分类</label>
      <select id="doc-category" disabled>
        <option value="">全部分类</option>
        {category_options}
      </select>
    </div>
  </section>
  <div class="index-results">
    <span id="doc-result-count" class="index-result-count" role="status" aria-live="polite">显示 {len(DOCS)} / {len(DOCS)} 篇</span>
    <button id="doc-clear" class="index-clear" type="button" disabled>清除搜索与分类</button>
  </div>
  <noscript><p>启用 JavaScript 后可使用搜索与分类。</p></noscript>
  <p id="doc-empty-state" class="index-empty" hidden>没有找到匹配文档。请尝试其他关键词或清除搜索与分类。</p>
  <div class="doc-grid">
    {"".join(cards)}
  </div>
  <div class="doc-footer">
    <p>AI 基础设施深度文档 · 从原理到生产实践</p>
  </div>
</main>
{THEME_CONTROLS_SCRIPT}
{INDEX_SCRIPT}
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
