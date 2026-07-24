# AI 基础设施深度文档

这个仓库整理了一组 AI 基础设施 deep-dive 文档，并提供一个轻量的 Python 脚本将 Markdown 渲染为带样式、目录和 Mermaid 支持的 HTML 页面。

内容重点是 LLM 推理系统、压测评估、AI 存储与文件系统、Kubernetes AI 平台、GPU/异构资源调度和 AI Sandbox 运行环境。源码文档位于仓库根目录，生成后的 HTML 文件会被 `.gitignore` 忽略。

## 版本与证据边界

当前文档集的审校截止日为 **2026-07-24**。正文优先固定官方最新稳定 release（Alpha 项目保留 Alpha 标识），并在各文档页头或附录记录 tag 解引用后的 exact source commit；没有 GitHub Release 的项目固定到审计时的分支 commit。`main`/`master` 后续能力只作为“未发布主线快照”单独说明，不计入稳定版兼容承诺。

本轮确认 8 个稳定版本发生变化：Dynamo `v1.3.0@8ce9e22f11576402102ea9d8b8e46233f5430a0d`、Mooncake `v0.3.12@c7ae97fd24251ed0aaaa613e8251859f170f1ae7`、Kueue `v0.19.0@911a822a49bcfd99c9c62203a009efa4130ad604`、KAI-Scheduler `v0.16.6@f9c97c087ab5aae409e6c7ab7b39f9affc12cf9d`、Kubernetes `v1.36.3@0f29094e5b73085e3802ecc1298ecae13866bfe6`、GuideLLM `v0.7.2@c71b5a17919170110e9d6e18d4dcfbf2471356f7`、inference-perf `v0.6.1@a40897e6500e4524adf563a91f7c880eb5296e12`、EvalScope `v1.9.1@9d1b353b7b6669c416d79bb259710082283d4c23`。其余稳定 release 未变化；3FS `main`、Volcano 官网与 Helm Charts 分支 HEAD 也未变化。KServe、KServe 官网、E2B SDK 与 Agent Sandbox 只更新审计快照，仍不扩大稳定兼容承诺。

## 文档索引

| 文档 | 主题 | 适合读者 | 覆盖重点 |
| --- | --- | --- | --- |
| [Mooncake-Deep-Dive.md](Mooncake-Deep-Dive.md) | Mooncake 分离式 LLM 推理架构 | 关注 KVCache、prefill/decode 分离、推理性能优化的工程师 | Transfer Engine、Mooncake Store、Conductor、HiCache、SSD/DFS 持久化、缓存治理 |
| [Dynamo-Deep-Dive.md](Dynamo-Deep-Dive.md) | Dynamo 数据中心级 LLM 推理编排 | 关注多节点推理服务、KV 路由和生产编排的工程师 | Request/Control/Storage 三平面、KV-Aware Router、KVBM、Planner、Operator、部署模式 |
| [E2B-Deep-Dive.md](E2B-Deep-Dive.md) | E2B AI Sandbox 与自托管架构 | 关注代码执行沙箱、microVM、安全隔离、团队配额和私有化部署的工程师 | Firecracker microVM、Orchestrator、envd、模板构建、网络隔离、状态存储、团队配额、可靠计量、预算、内部成本分摊、Terraform/Nomad 自托管 |
| [LLM-Benchmark-Deep-Dive.md](LLM-Benchmark-Deep-Dive.md) | LLM 压测工具深度对比 | 需要选择或设计推理压测方案的工程师 | AIPerf、GuideLLM、inference-perf、genai-bench v0.0.5、SGLang Bench、LLMPerf、vLLM Bench、EvalScope、Ollama Benchmark |
| [Lustre-3FS-Deep-Dive.md](Lustre-3FS-Deep-Dive.md) | Lustre 与 3FS 深度技术文档 | 关注 AI 存储、HPC 并行文件系统、RDMA/NVMe 共享存储和 KVCache 落盘的工程师 | Lustre MDS/OSS/OST/LNet、3FS Meta/Storage/CRAQ/USRBIO、dataloader、checkpoint、KV cache、生产选型 |
| [NVIDIA-GPU-Operator-Deep-Dive.md](NVIDIA-GPU-Operator-Deep-Dive.md) | NVIDIA GPU Operator 节点软件栈与生命周期管理 | 负责 Kubernetes GPU 驱动、设备接入、共享隔离和生产运维的平台工程师 | Controller 调谐、ClusterPolicy、Driver/Toolkit/Device Plugin、CDI/NRI、MIG、Time-Slicing/MPS、DCGM、升级排障 |
| [HAMi-Deep-Dive.md](HAMi-Deep-Dive.md) | Kubernetes 异构 AI 设备虚拟化与调度 | 关注 GPU 共享、设备隔离、多厂商设备管理的 Kubernetes 平台工程师 | MutatingWebhook、Scheduler Extender、Device Plugin、HAMi-Core、Annotation 协议、多厂商设备 |
| [Kubernetes-Native-Scheduler-Deep-Dive.md](Kubernetes-Native-Scheduler-Deep-Dive.md) | Kubernetes 原生调度器深度解析 | 负责 Kubernetes 调度、GPU 集群和 AI 平台选型的工程师 | SchedulingQueue、Scheduling Framework、DRA 对象与生命周期、DynamicResources、PodGroup/Gang/TAS、工作负载级抢占、AI 调度器对比 |
| [Kubernetes-AI-Schedulers-Deep-Dive.md](Kubernetes-AI-Schedulers-Deep-Dive.md) | Kubernetes AI 调度器深度对比 | 负责 GPU 集群、训练/推理平台、批任务队列和调度器选型的平台工程师 | Koordinator、Kueue、Grove、KAI-Scheduler、Volcano、Gang、队列公平、拓扑、组合架构、升级治理 |
| [Volcano-Upgrade-Compatibility-Deep-Dive.md](Volcano-Upgrade-Compatibility-Deep-Dive.md) | Volcano 升级与 Feature 兼容性 | 负责 Volcano 升级、Queue 治理、Webhook 和共置能力的平台工程师 | v1.8.2→v1.15.0、Helm/Manifest、proportion/capacity、Agent、Cloud Native Colocation、DRA、gang-aware eviction |
| [KServe-Deep-Dive.md](KServe-Deep-Dive.md) | KServe 生成式 AI 与预测式 AI 推理服务平台 | 关注 Kubernetes 上模型服务、推理网关和缓存能力的平台工程师 | InferenceService、LLMInferenceService、ServingRuntime、Gateway API、LocalModelCache、LMCache 与未发布主线 KV cache offloading 边界 |
| [Kubeflow-Deep-Dive.md](Kubeflow-Deep-Dive.md) | Kubeflow Community Distribution 与端到端 MLOps 平台 | 关注多租户 MLOps、Notebook、Pipeline、训练和推理集成的平台工程师 | Dashboard、Profiles、Pipelines、Notebooks、Katib、Trainer、KServe 节点、Istio/OAuth2/Dex |

## 推荐阅读路径

- LLM 推理架构：先读 [Mooncake-Deep-Dive.md](Mooncake-Deep-Dive.md)，再读 [Dynamo-Deep-Dive.md](Dynamo-Deep-Dive.md)。前者聚焦 KVCache 与分离式推理机制，后者聚焦数据中心级编排和路由。
- 压测与容量评估：读 [LLM-Benchmark-Deep-Dive.md](LLM-Benchmark-Deep-Dive.md)。它适合在选型推理引擎、比较吞吐/延迟指标、设计 SLO/goodput 压测方案前阅读。
- AI 存储与文件系统：读 [Lustre-3FS-Deep-Dive.md](Lustre-3FS-Deep-Dive.md)。它适合理解 Lustre、3FS、RDMA/NVMe 共享存储、checkpoint、dataloader 和 KV cache on disk 的架构取舍。
- Kubernetes AI 平台：按 [NVIDIA-GPU-Operator-Deep-Dive.md](NVIDIA-GPU-Operator-Deep-Dive.md)、[HAMi-Deep-Dive.md](HAMi-Deep-Dive.md)、[Kubernetes-Native-Scheduler-Deep-Dive.md](Kubernetes-Native-Scheduler-Deep-Dive.md)、[Kubernetes-AI-Schedulers-Deep-Dive.md](Kubernetes-AI-Schedulers-Deep-Dive.md)、[Volcano-Upgrade-Compatibility-Deep-Dive.md](Volcano-Upgrade-Compatibility-Deep-Dive.md)、[KServe-Deep-Dive.md](KServe-Deep-Dive.md)、[Kubeflow-Deep-Dive.md](Kubeflow-Deep-Dive.md) 的顺序阅读。它们依次覆盖 NVIDIA 驱动与设备栈、GPU 共享和异构设备、原生调度基线、AI 队列与调度扩展、Volcano 升级兼容、模型推理服务以及上层 MLOps 平台。
- Sandbox 与执行环境：读 [E2B-Deep-Dive.md](E2B-Deep-Dive.md)。它适合理解 AI Agent 代码执行环境、隔离边界、自托管部署取舍，以及 Team/Project 配额、可靠计量、预算与内部成本分摊的补建边界。

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
