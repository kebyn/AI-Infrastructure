# AI 基础设施深度文档

这个仓库整理了一组 AI 基础设施 deep-dive 文档，并提供一个轻量的 Python 脚本将 Markdown 渲染为带样式、目录和 Mermaid 支持的 HTML 页面。

内容重点是 LLM 推理系统、压测评估、AI 存储与文件系统、Kubernetes AI 平台、GPU/异构资源调度、AI-native coding agent 协作与编排平台和 AI Sandbox 运行环境。源码文档位于仓库根目录，生成后的 HTML 文件会被 `.gitignore` 忽略。

## 版本与证据边界

当前文档集的审校截止日为 **2026-09-06**。正文优先固定官方最新非 draft、非 prerelease Release（Grove 保留正式 Alpha 标识），并在各文档页头或附录记录 annotated tag 解引用后的 exact source commit；lightweight tag 记录其直接 commit，没有 GitHub Release 的项目固定到审计时的分支 commit。`main`/`master` 后续能力只作为“未发布主线快照”单独说明，不计入稳定版兼容承诺。

**新稳定基线。** 本轮更新 Mooncake `v0.3.13.post1@719735896c86b56fabec6cf3e825fb2ea640597a`、Dynamo `v1.4.2@2ecbdfdf192c69c02c6d21e931d20d3b4a0bb64a`、Multica `v0.4.40@2cf5674d2e951db7733b622069e752b150dd6ab8`、vLLM `v0.28.0@2cf0a6915ce544dc493a0990f2ea38d81601128a`、EvalScope `v1.11.1@203cdc93137376df91814036bf99f486b5f4f3d1`、SGLang `v0.5.19@0bcd822377da7b5718e674eaf9c870d349424dd1`、Kubernetes `v1.37.0@f54c212e3a2f75d674b717a9b29052b20b60aefc`、Grove `v0.1.0-alpha.13@af2df1ffff0ae7a1135554564a6240a3f22f2c35`、Kueue `v0.19.3@2ade4776eadb571ecfba02f3680c4ef617a07e71`、KAI-Scheduler `v0.17.1@68dca3c4b8de3d9c433cf95c8f084372903ec84d` 与 Volcano `v1.15.2@1462fb7b4835970708717456e3aed85e697ec2eb`。重点包括 Multica runs/Runtime/Autopilot/MCP 修复、SGLang beam/speculative/DeepEP v2/HiCache-L3 与压测缓存边界、Kubernetes Workload/PodGroup v1beta1、Grove PodGangMap 重建与 1:N 映射、Kueue v0.19.3 资源转换/DRA/准入修复、KAI v0.17.1 的 FIPS/DRA/eviction 修复，以及 Volcano GHSA-j38h-7pfq-cxmw 和调度修复。

**Kubernetes Blog/RSS 历史审计。** 本轮将 [Kubernetes Blog 新特性深度综述](Kubernetes-Blog-Feature-Deep-Dive.md) 扩展到 2022 年起（约 v1.24）至 2026-09-06，仍以 Kubernetes `v1.37.0@f54c212e3a2f75d674b717a9b29052b20b60aefc` 为稳定基线。正文新增 v1.24—v1.37 版本时间线、跨版本演进矩阵，并补入 2026 年 HPA scale-to-zero、DRA Updates、KubeletInUserNamespace/rootless Beta、etcd RangeStream、Mixed Version Proxy、PSI、Route Sync、ExternalIPs、生产调试安全、Dashboard→Headlamp 和 Headlamp/Kubeflow/Volcano/Knative/CAPI 生态文章。Blog 中的 Alpha/Beta、Working Group proposal 和生态项目只记录为审计证据，不纳入 Stable 兼容承诺；RSS 审校截止 2026-09-06。

**上轮遗漏纠正。** ModelExpress `v0.5.1@eb5011575dcf56327578634f93a2ec2f7b5416fd` 实际发布于 2026-08-20，早于上轮截止日；本轮补记其 TensorRT-LLM 一等支持与 protobuf 6 客户端兼容。loader、registry、P2P transfer plane 除这两项外没有新增语义，不能把这次补记描述成 8 月 22 日之后的新发布。

**稳定版未变化。** E2B Infra `2026.29`、KServe `v0.20.0`、GPU Operator `v26.7.0@10ee5b3638b89e11e949412aafa5ba99279c3721`、HAMi `v2.10.0@4707fb02c91c545bc7343ce26dba4c32919f9a3e`、Kubeflow Community Distribution `26.03.1`、Koordinator `v1.8.0`、AIPerf `v0.12.0`、GuideLLM `v0.7.3`、inference-perf `v0.6.1`、genai-bench `v0.0.5`、LLMPerf `v2.0` 与 ollama-benchmark `v0.5.2` 经复核保持原基线。Kueue、Grove、KAI-Scheduler 与 SGLang 已在上方新稳定基线中更新；其余项目没有新的正式 release，不因 prerelease、tag-only 或主线快照改变稳定承诺。
KAI 仓库仍可见 tag-only `v0.20.1@5922dc7d1a4661d3fc43d60943f92a775c892bdc`，但没有对应正式 GitHub Release；它只作为独立审计证据，不替代 `v0.17.1` 稳定基线。

**稳定对照与未发布快照。** Agent Sandbox 已从主线快照切换到正式 `v1.0.0@bb72f49d79f009a960eed2ae6c32e1cc082399c5` 对照，重点是 v1beta1-only CRD、`<v0.5.0 → v0.5.x → v1.0.0` 存储迁移、conversion webhook 清理、path routing/session-cookie auth、`sandboxd` 与 SDK streaming upload；这些不是 E2B Infra 功能。未发布证据固定为 E2B SDK `main@5a56c87e9db0e221b138662805af7743e75f1082`、Multica `main@61ea48fd2ef0e9818de38533553e830fd36be349`、KServe `master@003f717c0bb8bb896df499cbe143172928f1665c`、KServe 官网 `main@71c8b22a05d6be72560b2cc326865930063cd0e8`、Koordinator `main@025aa5923342eb43bb10f29e7ae0cc64988cb540` 与 Volcano 官网 `master@aee652b985d25e33f59f6112e857627784b741ca`。Volcano Helm 证据改为正式 `volcano-1.15.2@c2050e3debe58dbcdf9bb75b667799eec9409513` tag；3FS 仍固定 `main@22fca04564c7cc230fd8b9523b8b92864e1dad47`。主线和网站快照仅证明审计时实现/文档形态，不扩大对应稳定版承诺。

KServe v0.20.0 仍以 LLMISVC v1alpha2 的 `spec.kvCacheOffloading`、`route.group`/`route.weight`、Anthropic `/v1/messages`、Managed DRA 和分布式 tracing 为稳定边界。rollout strategy、canary readiness、KEDA true scale-to-zero、合并配置模板后的 dry-run 校验、`oci+fetch://`、`ms://`、P/D NixlConnector、LoRA LocalModelCache 和 TLS 证书热重载仍只属于固定 master；v0.20.0 release sample 与官网快照继续存在 v1alpha1/旧 `spec.workload.kvCacheOffloading` 路径混用风险，落地应以 v1alpha2 CRD schema 为准。

## 文档索引

| 文档 | 版本基线 | 主题 | 适合读者 | 覆盖重点 |
| --- | --- | --- | --- | --- |
| [Mooncake-Deep-Dive.md](Mooncake-Deep-Dive.md) | `v0.3.13.post1` | Mooncake 分离式 LLM 推理架构 | 关注 KVCache、prefill/decode 分离、推理性能优化的工程师 | Transfer Engine/TENT 新 transport、Mooncake Store、NVMe/DFS、HA OpLog、Conductor、结构化对象与多租户 |
| [Dynamo-Deep-Dive.md](Dynamo-Deep-Dive.md) | Dynamo `v1.4.2`；ModelExpress `v0.5.1` | Dynamo 数据中心级 LLM 推理编排 | 关注多节点推理服务、KV 路由和生产编排的工程师 | Request/Control/Storage 三平面、classify/pooling、NIXL loader、KV relay、Frontend、多模态、Planner、Operator 与 KVBM 弃用边界 |
| [E2B-Deep-Dive.md](E2B-Deep-Dive.md) | Infra `2026.29`；SDK `main@5a56c87`；Agent Sandbox `v1.0.0` | E2B AI Sandbox 与自托管架构 | 关注代码执行沙箱、microVM、安全隔离、团队配额和私有化部署的工程师 | Firecracker microVM、Orchestrator、envd、网络隔离、团队配额、SDK IAM 主线与 Agent Sandbox v1beta1/迁移对照 |
| [Multica-Deep-Dive.md](Multica-Deep-Dive.md) | `v0.4.40` | AI-native 团队任务管理与 coding agent 编排平台 | 关注 coding agent 团队协作、本地 CLI 执行、自托管和权限治理的工程师 | Issue/Task/runs、25 种 protocol family、Plugin Public API v1、ZeroClaw/CodeArts、Runtime claim、进程树/daemon 恢复、Squad、Autopilot、MCP 与无 Sandbox 边界 |
| [LLM-Benchmark-Deep-Dive.md](LLM-Benchmark-Deep-Dive.md) | AIPerf `v0.12.0`；GuideLLM `v0.7.3`；SGLang `v0.5.19`；vLLM `v0.28.0`；EvalScope `v1.11.1`；其余见正文 | LLM 压测工具深度对比 | 需要选择或设计推理压测方案的工程师 | AgentX、adaptive scale、SGLang beam/speculative/DeepEP/HiCache 与缓存迁移、vLLM dataset/timed trace、EvalScope warmup/SSE/指标正确性与多工具对比 |
| [Lustre-3FS-Deep-Dive.md](Lustre-3FS-Deep-Dive.md) | Lustre 官方资料；3FS `main@22fca04` | Lustre 与 3FS 深度技术文档 | 关注 AI 存储、HPC 并行文件系统、RDMA/NVMe 共享存储和 KVCache 落盘的工程师 | Lustre MDS/OSS/OST/LNet、3FS Meta/Storage/CRAQ/USRBIO、dataloader、checkpoint、KV cache、生产选型 |
| [NVIDIA-GPU-Operator-Deep-Dive.md](NVIDIA-GPU-Operator-Deep-Dive.md) | `v26.7.0` | NVIDIA GPU Operator 节点软件栈与生命周期管理 | 负责 Kubernetes GPU 驱动、设备接入、共享隔离和生产运维的平台工程师 | Controller 调谐、ClusterPolicy、GPUCluster/DRA、Driver/Toolkit/Device Plugin、CDI/NRI、MIG、Time-Slicing/MPS、DCGM、升级排障 |
| [HAMi-Deep-Dive.md](HAMi-Deep-Dive.md) | `v2.10.0` | Kubernetes 异构 AI 设备虚拟化与调度 | 关注 GPU 共享、设备隔离、多厂商设备管理的 Kubernetes 平台工程师 | MutatingWebhook、Scheduler Extender、Device Plugin、HAMi-Core、独立 DRA driver、init-container 记账、PodGroup/MIG/mutex/NUMA、多厂商设备 |
| [Kubernetes-Blog-Feature-Deep-Dive.md](Kubernetes-Blog-Feature-Deep-Dive.md) | Kubernetes v1.24—v1.37；Blog/RSS 截止 2026-09-06 | Kubernetes Blog/RSS 跨 SIG 特性历史审计 | 需要理解 Kubernetes 版本演进、成熟度、升级和 AI 平台组合的工程师 | v1.24—v1.37 时间线与演进链、HPA Scale-to-Zero、DRA、Gang Scheduling、Storage Version Migration、RangeStream、证书、rootless、KYAML、Gateway API、Agent Sandbox |
| [Kubernetes-Native-Scheduler-Deep-Dive.md](Kubernetes-Native-Scheduler-Deep-Dive.md) | Kubernetes `v1.37.0` | Kubernetes 原生调度器深度解析 | 负责 Kubernetes 调度、GPU 集群和 AI 平台选型的工程师 | SchedulingQueue、Scheduling Framework、DRA v1.37 扩展、Workload/PodGroup v1beta1、CompositePodGroup、Gang/TAS 与工作负载级抢占 |
| [Kubernetes-AI-Schedulers-Deep-Dive.md](Kubernetes-AI-Schedulers-Deep-Dive.md) | Koordinator `v1.8.0`；Kueue `v0.19.3`；Grove `alpha.13`；KAI `v0.17.1`；Volcano `v1.15.2` | Kubernetes AI 调度器深度对比 | 负责 GPU 集群、训练/推理平台、批任务队列和调度器选型的平台工程师 | Kueue v0.19.3 DRA/准入修复、Grove PodGangMap/KAI backend、KAI v0.17.1 DRA/eviction/FIPS、Volcano GHSA 修复、组合架构与升级治理 |
| [Volcano-Upgrade-Compatibility-Deep-Dive.md](Volcano-Upgrade-Compatibility-Deep-Dive.md) | `v1.8.2 → v1.15.2` | Volcano 升级与 Feature 兼容性 | 负责 Volcano 升级、Queue 治理、Webhook 和共置能力的平台工程师 | Helm/Manifest、proportion/capacity、Agent、Cloud Native Colocation、DRA O(1) 安全修复、reclaim/preempt 与 gang-aware eviction |
| [KServe-Deep-Dive.md](KServe-Deep-Dive.md) | `v0.20.0`；master `003f717`；官网 `71c8b22` | KServe 生成式 AI 与预测式 AI 推理服务平台 | 关注 Kubernetes 上模型服务、推理网关和缓存能力的平台工程师 | InferenceService、LLMInferenceService v1alpha2、Gateway API、LocalModelCache、稳定 KV offloading/流量切分、主线 `ms://`/NIXL/LoRA cache 与 schema 警告边界 |
| [Kubeflow-Deep-Dive.md](Kubeflow-Deep-Dive.md) | Community Distribution `26.03.1` | Kubeflow Community Distribution 与端到端 MLOps 平台 | 关注多租户 MLOps、Notebook、Pipeline、训练和推理集成的平台工程师 | Dashboard、Profiles、Pipelines、Notebooks、Katib、Trainer、KServe 节点、Istio/OAuth2/Dex |

## 推荐阅读路径

- LLM 推理架构：先读 [Mooncake-Deep-Dive.md](Mooncake-Deep-Dive.md)，再读 [Dynamo-Deep-Dive.md](Dynamo-Deep-Dive.md)。前者聚焦 KVCache 与分离式推理机制，后者聚焦数据中心级编排和路由。
- 压测与容量评估：读 [LLM-Benchmark-Deep-Dive.md](LLM-Benchmark-Deep-Dive.md)。它以 SGLang `v0.5.19`、vLLM `v0.28.0` 和 EvalScope `v1.11.1` 为关键基线，适合在选型推理引擎、比较吞吐/延迟指标、设计 SLO/goodput 压测方案前阅读。
- AI 存储与文件系统：读 [Lustre-3FS-Deep-Dive.md](Lustre-3FS-Deep-Dive.md)。它适合理解 Lustre、3FS、RDMA/NVMe 共享存储、checkpoint、dataloader 和 KV cache on disk 的架构取舍。
- Kubernetes AI 平台：按 [Kubernetes-Blog-Feature-Deep-Dive.md](Kubernetes-Blog-Feature-Deep-Dive.md) → [Kubernetes-Native-Scheduler-Deep-Dive.md](Kubernetes-Native-Scheduler-Deep-Dive.md) → [Kubernetes-AI-Schedulers-Deep-Dive.md](Kubernetes-AI-Schedulers-Deep-Dive.md) → [Volcano-Upgrade-Compatibility-Deep-Dive.md](Volcano-Upgrade-Compatibility-Deep-Dive.md) → [KServe-Deep-Dive.md](KServe-Deep-Dive.md) / [Kubeflow-Deep-Dive.md](Kubeflow-Deep-Dive.md) 阅读；需要节点设备和共享隔离细节时，再补读 [NVIDIA-GPU-Operator-Deep-Dive.md](NVIDIA-GPU-Operator-Deep-Dive.md) 与 [HAMi-Deep-Dive.md](HAMi-Deep-Dive.md)。这条路径依次覆盖 v1.24—v1.37 Blog/RSS 特性演进、原生调度基线、Kueue `v0.19.3`/Grove `alpha.13`/KAI `v0.17.1` AI 队列与调度扩展、Volcano 升级兼容、模型推理服务以及上层 MLOps 平台。
- Agent 协作与执行平台：读 [Multica-Deep-Dive.md](Multica-Deep-Dive.md)。它聚焦 Issue/Task、Agent/Runtime、Squad 和 Autopilot 如何编排本机 coding agent CLI；Multica 默认不提供 Sandbox，不能把工作目录或 provider adapter 当作隔离边界。
- Sandbox 与执行环境：读 [E2B-Deep-Dive.md](E2B-Deep-Dive.md)。它聚焦 Firecracker microVM 通用隔离 Sandbox、自托管部署取舍，以及 Team/Project 配额、可靠计量、预算与内部成本分摊的补建边界，与 Multica 的协作编排和本地 CLI 执行路径不同。

## 本地预览

`serve_docs.py` 会把所有 `*-Deep-Dive.md` 渲染为 HTML，并生成首页 `index.html`。脚本默认监听 `80` 端口，根路径 `/` 会返回首页。

首次运行使用 uv 创建虚拟环境并安装锁定的依赖：

```bash
uv sync --locked
```

日常命令无需手动激活虚拟环境；如需交互式 shell，可选执行 `source .venv/bin/activate`。

运行测试：

```bash
uv run --locked python -m unittest test_serve_docs.py
```

启动服务：

```bash
uv run --locked python serve_docs.py
```

访问首页：

```text
http://127.0.0.1/
```

如果已经用 `screen` 在后台运行服务，可以用下面的命令查看或停止：

```bash
screen -r serve_docs
screen -S serve_docs -X quit
```

## 生成产物

- `index.html` 是文档首页。
- `*-Deep-Dive.html` 是每篇 Markdown 对应的渲染结果。
- `*.html` 已在 `.gitignore` 中忽略，不需要提交。
- Python 缓存文件 `__pycache__/` 和 `*.py[cod]` 也已忽略。
