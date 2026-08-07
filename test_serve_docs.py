import re
import tempfile
import unittest
from pathlib import Path

import serve_docs


class RenderDocLayoutTest(unittest.TestCase):
    def test_all_deep_dives_are_registered_and_use_current_audit_date(self):
        docs_dir = Path(__file__).resolve().parent
        markdown_docs = {path.name for path in docs_dir.glob("*-Deep-Dive.md")}
        registered_docs = {Path(doc["src"]).name for doc in serve_docs.DOCS}

        self.assertEqual(len(markdown_docs), 12)
        self.assertEqual(registered_docs, markdown_docs)
        for doc in serve_docs.DOCS:
            with self.subTest(document=Path(doc["src"]).name):
                self.assertIn("2026-07-28", doc["meta"])
                self.assertNotIn("2026-07-24", doc["meta"])
                markdown_text = Path(doc["src"]).read_text(encoding="utf-8")
                self.assertIn("审校日期：2026-07-28", markdown_text)
                self.assertNotIn("2026-07-24", markdown_text)

    def test_benchmark_snapshot_uses_current_stable_releases(self):
        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "LLM-Benchmark-Deep-Dive.md"
        )
        markdown_text = Path(doc["src"]).read_text(encoding="utf-8")

        for release in ("AIPerf v0.12.0", "GuideLLM v0.7.3", "EvalScope v1.10.0"):
            self.assertIn(release, doc["meta"])
        self.assertIn("genai-bench/tree/v0.0.5", doc["footer"])
        for exact_commit in (
            "0e723bb8c984564cddf7274d19aab4eb7714f919",
            "39383552962841086d05e25c37b58a83ef06c758",
            "a40897e6500e4524adf563a91f7c880eb5296e12",
            "9d052ca0240ebf8b603c053fa44727b863ff3933",
            "4f873e03719c947a101647c6646954d5ebc3d35b",
            "fdebc938f7f4d16fe6b9f55dcd9a767cf0899ea1",
            "568afb3a13806beb53bb2e6bd518269357b237c0",
        ):
            self.assertIn(exact_commit, markdown_text)
        self.assertIn("text-to-speech", markdown_text)
        self.assertIn("Audio Throughput", markdown_text)
        self.assertIn('A(500)', markdown_text)
        self.assertIn("spec_cap_lens_histogram", markdown_text)
        self.assertIn("vllm-bench", markdown_text)
        self.assertIn("Python `vllm bench serve` 本轮没有新增对应的专用 P/D 参数", markdown_text)
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
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, markdown_text)

    def test_refreshed_stable_release_commits_are_pinned(self):
        docs_dir = Path(__file__).resolve().parent
        expected_commits = {
            "Dynamo-Deep-Dive.md": (
                "a49702e4432e7fa43cbc88175bddb31604340f19",
                "0406ac16d5daeef985de1bf4d09c9f0a5e188c1a",
            ),
            "Mooncake-Deep-Dive.md": (
                "6041a609a8c3af35e778f70db344f145c2914980",
            ),
            "Kubernetes-Native-Scheduler-Deep-Dive.md": (
                "0f29094e5b73085e3802ecc1298ecae13866bfe6",
            ),
            "Kubernetes-AI-Schedulers-Deep-Dive.md": (
                "911a822a49bcfd99c9c62203a009efa4130ad604",
                "f218c69bee5e5fc6031273ba555d09916b1ca89a",
                "0a56ed331897f5455916a44d3075671376d731d6",
            ),
            "LLM-Benchmark-Deep-Dive.md": (
                "0e723bb8c984564cddf7274d19aab4eb7714f919",
                "39383552962841086d05e25c37b58a83ef06c758",
                "a40897e6500e4524adf563a91f7c880eb5296e12",
                "9d052ca0240ebf8b603c053fa44727b863ff3933",
                "fdebc938f7f4d16fe6b9f55dcd9a767cf0899ea1",
                "568afb3a13806beb53bb2e6bd518269357b237c0",
            ),
        }
        for filename, commits in expected_commits.items():
            markdown_text = (docs_dir / filename).read_text(encoding="utf-8")
            for commit in commits:
                with self.subTest(document=filename, commit=commit):
                    self.assertIn(commit, markdown_text)

    def test_refreshed_release_behavior_is_documented(self):
        docs_dir = Path(__file__).resolve().parent
        mooncake_text = (docs_dir / "Mooncake-Deep-Dive.md").read_text(
            encoding="utf-8"
        )
        kai_text = (docs_dir / "Kubernetes-AI-Schedulers-Deep-Dive.md").read_text(
            encoding="utf-8"
        )

        for required_text in (
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
        ):
            with self.subTest(document="KAI-Scheduler", required_text=required_text):
                self.assertIn(required_text, kai_text)

        dynamo_text = (docs_dir / "Dynamo-Deep-Dive.md").read_text(
            encoding="utf-8"
        )
        for required_text in (
            "nixl==1.3.2",
            "EFA Installer `1.49.0`",
            "libfabric `2.4.0amzn5.0`",
            "Lost connection with prefill instance",
            "空 HTTP 200/零 token",
            "ModelExpress 独立稳定版 `v0.5.0",
        ):
            with self.subTest(document="Dynamo", required_text=required_text):
                self.assertIn(required_text, dynamo_text)

    def test_scheduler_release_snapshots_and_patch_boundaries_are_documented(self):
        docs_dir = Path(__file__).resolve().parent
        ai_text = (docs_dir / "Kubernetes-AI-Schedulers-Deep-Dive.md").read_text(
            encoding="utf-8"
        )
        native_text = (
            docs_dir / "Kubernetes-Native-Scheduler-Deep-Dive.md"
        ).read_text(encoding="utf-8")
        volcano_text = (
            docs_dir / "Volcano-Upgrade-Compatibility-Deep-Dive.md"
        ).read_text(encoding="utf-8")

        ai_doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "Kubernetes-AI-Schedulers-Deep-Dive.md"
        )
        volcano_doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name
            == "Volcano-Upgrade-Compatibility-Deep-Dive.md"
        )

        self.assertIn("KAI-Scheduler v0.17.0", ai_doc["meta"])
        self.assertIn("Volcano v1.15.1", ai_doc["meta"])
        self.assertIn("v1.8.2 → v1.15.1", volcano_doc["meta"])
        for revision in (
            "0a56ed331897f5455916a44d3075671376d731d6",
            "0ef50ca74346b4ef89576f9d864089b5b6b341df",
            "c2050e3debe58dbcdf9bb75b667799eec9409513",
        ):
            self.assertIn(revision, volcano_text)

        for required_text in (
            "OnDemand PVC informer race",
            "NeedContinueAllocating",
            "DRA count saturating arithmetic",
            "golang.org/x/crypto",
            "scalar resource milli-unit",
        ):
            self.assertIn(required_text, volcano_text)

        self.assertIn("KAI-Scheduler v0.17.0", native_text)
        self.assertIn("Volcano v1.15.1", native_text)
        self.assertIn("preemption delay", native_text)
        self.assertIn("PVC informer race", native_text)

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
            "557445ffddda8d9a27f6f529a3f4d7732cf81a13/"
            "packages/orchestrator/pkg/proxy/proxy.go",
            markdown_text,
        )
        self.assertIn(
            "https://github.com/e2b-dev/infra/blob/"
            "557445ffddda8d9a27f6f529a3f4d7732cf81a13/"
            "tests/integration/internal/tests/proxies/traffic_access_token_test.go",
            markdown_text,
        )
        self.assertIn(
            "https://github.com/e2b-dev/e2b/blob/"
            "88f41f392722a2f56971ea6c1084f0fc574ef1f4/"
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
            "Infra 2026.29 没有名为 Router 的独立服务",
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
            "Agent Sandbox Go Router（对照，不是 E2B 能力）",
            "108be73b56d9bff55a0cc626c9e89100d797a9bc",
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
            "默认 `allow-all`",
            "scoped-token",
            "两者都不要求进入 Pod 的容器镜像解析 `X-Sandbox-Port`",
            "`X-Sandbox-Port` 不是 E2B 的兼容 Header",
            "在请求进入 Client Proxy 前成对转换",
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
            "557445ffddda8d9a27f6f529a3f4d7732cf81a13/"
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
            "iac/provider-gcp/nomad-cluster/network/main.tf",
        ):
            with self.subTest(source_path=source_path):
                self.assertIn(infra_commit_base + source_path, markdown_text)

        sdk_commit_base = (
            "https://github.com/e2b-dev/e2b/blob/"
            "88f41f392722a2f56971ea6c1084f0fc574ef1f4/"
        )
        for source_path in (
            "packages/js-sdk/src/connectionConfig.ts",
            "packages/js-sdk/src/sandbox/index.ts",
            "packages/python-sdk/e2b/connection_config.py",
            "packages/python-sdk/e2b/sandbox_sync/main.py",
        ):
            with self.subTest(source_path=source_path):
                self.assertIn(sdk_commit_base + source_path, markdown_text)

        agent_sandbox_commit_base = (
            "https://github.com/kubernetes-sigs/agent-sandbox/blob/"
            "108be73b56d9bff55a0cc626c9e89100d797a9bc/"
        )
        for source_path in (
            "clients/python/agentic-sandbox-client/sandbox-router/README.md",
            "clients/python/agentic-sandbox-client/sandbox-router/sandbox_router.py",
            "sandbox-router/README.md",
            "sandbox-router/proxy/headers.go",
            "sandbox-router/proxy/proxy.go",
        ):
            with self.subTest(source_path=source_path):
                self.assertIn(agent_sandbox_commit_base + source_path, markdown_text)

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
            {"557445ffddda8d9a27f6f529a3f4d7732cf81a13"},
        )

        commit_base = (
            "https://github.com/e2b-dev/infra/blob/"
            "557445ffddda8d9a27f6f529a3f4d7732cf81a13/"
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
        for summary_term in ("状态存储", "团队配额", "可靠计量", "预算", "内部成本分摊"):
            with self.subTest(summary_term=summary_term):
                self.assertIn(summary_term, doc["summary"])
        self.assertIn(
            "https://github.com/e2b-dev/infra/tree/"
            "557445ffddda8d9a27f6f529a3f4d7732cf81a13",
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

    def test_kserve_v0_20_separates_release_and_unreleased_main(self):
        doc = next(
            doc
            for doc in serve_docs.DOCS
            if Path(doc["src"]).name == "KServe-Deep-Dive.md"
        )
        markdown_text = Path(doc["src"]).read_text(encoding="utf-8")

        self.assertIn("KServe v0.20.0", doc["meta"])
        self.assertIn("master@b15ac29", doc["meta"])
        self.assertIn("website@b561e05", doc["meta"])
        for revision in (
            "1fb781055dd1567164358233e1125142ca6ef1fe",
            "b15ac29c6443340e2f4389a8e376f65fbcf8c6ec",
            "b561e05b36abcae07508a83eaf0244f153531c97",
        ):
            self.assertIn(revision, markdown_text)

        self.assertIn("v0.20.0 v1alpha2 稳定 API", markdown_text)
        self.assertIn("字段路径是 `spec.kvCacheOffloading`", markdown_text)
        self.assertIn("`spec.router.route.group` / `weight`", markdown_text)
        self.assertIn("`v0.20.0` tag 尚无 `pkg/tls`", markdown_text)
        for unreleased_feature in (
            "Controller TLS profile",
            "Tokenizer 与 llm-d-router 后续兼容",
            "Python 3.13 与 transformer CA bundle",
        ):
            self.assertIn(unreleased_feature, markdown_text)
        self.assertIn("不把它扩展为 v0.20.0 的兼容承诺", markdown_text)
        self.assertNotIn("b0eda63d2c105479140af8ec9149d992b7e44be5", markdown_text)
        self.assertNotIn("f8a0ac1c85c3d06e7f4a9b6872f2778a556c7886", markdown_text)

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
        self.assertIn("v1.36.3", doc["meta"])
        self.assertIn("0f29094", doc["meta"])
        self.assertIn(
            "https://kubernetes.io/docs/concepts/scheduling-eviction/",
            doc["footer"],
        )
        self.assertIn(
            "https://github.com/kubernetes/kubernetes/tree/v1.36.3",
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
        self.assertIn("Kubernetes v1.36.3", html)
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
            '<a href="#8-8-v1-36-3-feature-maturity-矩阵">'
            "8.8 v1.36.3 feature maturity 矩阵</a>",
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
