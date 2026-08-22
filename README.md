# AI 基础设施深度文档

这个仓库整理了一组 AI 基础设施 deep-dive 文档，并提供一个轻量的 Python 脚本将 Markdown 渲染为带样式、目录和 Mermaid 支持的 HTML 页面。

内容重点是 LLM 推理系统、压测评估、AI 存储与文件系统、Kubernetes AI 平台、GPU/异构资源调度、AI-native coding agent 协作与编排平台和 AI Sandbox 运行环境。源码文档位于仓库根目录，生成后的 HTML 文件会被 `.gitignore` 忽略。

## 版本与证据边界

当前文档集的审校截止日为 **2026-08-22**。正文优先固定官方最新非 draft、非 prerelease Release（Alpha 项目保留正式 Alpha 标识），并在各文档页头或附录记录 annotated tag 解引用后的 exact source commit；lightweight tag 记录其直接 commit，没有 GitHub Release 的项目固定到审计时的分支 commit。`main`/`master` 后续能力只作为“未发布主线快照”单独说明，不计入稳定版兼容承诺。

本轮确认 6 个正文稳定基线发生变化：Multica `v0.4.32@d60775aa9394b911b18701a326f655465604e7d1`、SGLang `v0.5.18@71de97b264b04dcd514cf904003028aefe9775c8`、GPU Operator `v26.7.0@10ee5b3638b89e11e949412aafa5ba99279c3721`、HAMi `v2.10.0@4707fb02c91c545bc7343ce26dba4c32919f9a3e`、Kubernetes `v1.36.4@bb826b1d48562f110659e64e8ec444327433db95` 与 Kueue `v0.19.2@8eab68778fc1b52affe165fdf5af29d1e9b4f3cb`。Dynamo `v1.4.0@03014943323e78feb5bd672ef08b72caea0918ac` 继续保持稳定基线。Dynamo v1.4.0 的 Router、Frontend、多模态、Planner、Operator、可观测性与 KVBM 弃用边界见专篇；Multica v0.4.32 合并 DeepSeek Harness、本地目录执行模式、路径/超时治理、Private Skill Plugin 和 Runtime 权限变化。Kueue v0.19.2 是 v0.19.0 上的补丁升级，不能跳过 v0.19.0 的 API、feature gate、Ray 配额和 Helm 清理前置要求；vLLM v0.27.1 是包含 v0.27.0 benchmark 变化后的 DSpark patch release。

辅助证据更新为 E2B SDK `main@b8029973aa7da5f741f7bb01a9f833b38a0885438`、Agent Sandbox `main@2fd412d55ecae90861a101a5424a75473de97c36`、KServe `master@aaac4e294dae2c7b1aa1886447793f3aa1c30912`、KServe 官网 `main@05b83a6cf9d6c4045a83d79eb8d0029605d655e7`、Koordinator `main@a48991792bcf9d1f8559f4cff7792bb0de6497c8`、Grove `main@fcc3b3bbbc5e6a2a797cd080bdbc6983b1ccec24` 与 Volcano 官网 `master@c8148836e8718e84387f88e8ef3f73b6b78cf5a8`；Volcano Helm Charts 经复核仍为 `main@c2050e3debe58dbcdf9bb75b667799eec9409513`。E2B SDK 主线新增 IAM workload identity、`Secret.iamToken`/`iam_token`、network transform callback token placeholder、token name 校验与 Python `http2` 参数；Agent Sandbox 主线补充 WarmPool status、ServiceMonitor、PodScheduled image、Pi 示例和 Podman kind 支持；KServe 主线补充 `ms://` ModelScope storage provider、依赖安全修复与 weighted InferencePool 测试。上述快照只用于固定未发布实现、调用形态或官网/Chart 证据，不扩大 E2B Infra、KServe 或 Volcano 稳定版的兼容承诺；Volcano 官网本轮只有 Mermaid 支持变化，不制造正文能力变化。

KServe v0.20.0 已把 LLMISVC v1alpha2 的 `spec.kvCacheOffloading`、`route.group`/`route.weight`、Anthropic `/v1/messages`、Managed DRA 和分布式 tracing 纳入稳定 Release。rollout strategy、canary readiness、KEDA true scale-to-zero、合并配置模板后的 dry-run 校验和 `oci+fetch://` 仍只属于固定 master，不能据此扩大 v0.20.0 的兼容承诺；v0.20.0 release sample 与官网快照仍混用 v1alpha1 和旧 `spec.workload.kvCacheOffloading` 路径，落地应以 v1alpha2 CRD schema 为准。

其余已登记稳定 Release 经复核未变化：Mooncake `v0.3.12.post1`、ModelExpress `v0.5.0@0406ac16d5daeef985de1bf4d09c9f0a5e188c1a`、E2B Infra `2026.29`、KServe `v0.20.0`、HAMi `v2.10.0`、Kubeflow Community Distribution `26.03.1`、Koordinator `v1.8.0`、Grove `v0.1.0-alpha.11`、KAI-Scheduler `v0.17.0`、Volcano `v1.15.1`、Kubernetes `v1.36.4`、AIPerf `v0.12.0`、GuideLLM `v0.7.3`、inference-perf `v0.6.1`、genai-bench `v0.0.5`、LLMPerf `v2.0`、ollama-benchmark `v0.5.2`、EvalScope `v1.10.0` 与 GPU Operator `v26.7.0`。KAI 的 `v0.16.9@724da8388358b7673495a935948ea0a67a86140b` 只是旧维护分支补丁，GitHub latest 不替代正文的 `v0.17.0`；Grove `v0.1.0-alpha.12-rc1` 是 prerelease，不替代当前正式 Alpha 基线；3FS 仍固定 `main@22fca04564c7cc230fd8b9523b8b92864e1dad47`，Lustre 继续以官方 Wiki/手册为准。

## 文档索引

| 文档 | 版本基线 | 主题 | 适合读者 | 覆盖重点 |
| --- | --- | --- | --- | --- |
| [Mooncake-Deep-Dive.md](Mooncake-Deep-Dive.md) | `v0.3.12.post1` | Mooncake 分离式 LLM 推理架构 | 关注 KVCache、prefill/decode 分离、推理性能优化的工程师 | Transfer Engine、Mooncake Store、Conductor、HiCache、SSD/DFS 持久化、缓存治理 |
| [Dynamo-Deep-Dive.md](Dynamo-Deep-Dive.md) | Dynamo `v1.4.0`；ModelExpress `v0.5.0` | Dynamo 数据中心级 LLM 推理编排 | 关注多节点推理服务、KV 路由和生产编排的工程师 | Request/Control/Storage 三平面、跨数据中心 prefix routing、KV relay、Frontend、多模态、Planner、Operator、可观测性与 KVBM 弃用边界 |
| [E2B-Deep-Dive.md](E2B-Deep-Dive.md) | Infra `2026.29`；SDK `main@b802997`；Agent Sandbox `main@2fd412d` | E2B AI Sandbox 与自托管架构 | 关注代码执行沙箱、microVM、安全隔离、团队配额和私有化部署的工程师 | Firecracker microVM、Orchestrator、envd、模板构建、网络隔离、状态存储、团队配额、可靠计量、SDK IAM 主线与 Agent Sandbox 对照边界 |
| [Multica-Deep-Dive.md](Multica-Deep-Dive.md) | `v0.4.32` | AI-native 团队任务管理与 coding agent 编排平台 | 关注 coding agent 团队协作、本地 CLI 执行、自托管和权限治理的工程师 | Issue/Task、21 种 provider、DeepSeek Harness、in_place/worktree、Private Skill Plugin、Squad、Autopilot、Chat/Channel/Inbox、自托管与无 Sandbox 安全边界 |
| [LLM-Benchmark-Deep-Dive.md](LLM-Benchmark-Deep-Dive.md) | AIPerf `v0.12.0`；GuideLLM `v0.7.3`；SGLang `v0.5.18`；vLLM `v0.27.1`；EvalScope `v1.10.0`；其余见正文 | LLM 压测工具深度对比 | 需要选择或设计推理压测方案的工程师 | AgentX、adaptive scale、长上下文前缀、inference-perf、genai-bench、SGLang/vLLM Bench、LLMPerf、Ollama Benchmark |
| [Lustre-3FS-Deep-Dive.md](Lustre-3FS-Deep-Dive.md) | Lustre 官方资料；3FS `main@22fca04` | Lustre 与 3FS 深度技术文档 | 关注 AI 存储、HPC 并行文件系统、RDMA/NVMe 共享存储和 KVCache 落盘的工程师 | Lustre MDS/OSS/OST/LNet、3FS Meta/Storage/CRAQ/USRBIO、dataloader、checkpoint、KV cache、生产选型 |
| [NVIDIA-GPU-Operator-Deep-Dive.md](NVIDIA-GPU-Operator-Deep-Dive.md) | `v26.7.0` | NVIDIA GPU Operator 节点软件栈与生命周期管理 | 负责 Kubernetes GPU 驱动、设备接入、共享隔离和生产运维的平台工程师 | Controller 调谐、ClusterPolicy、Driver/Toolkit/Device Plugin、CDI/NRI、MIG、Time-Slicing/MPS、DCGM、升级排障 |
| [HAMi-Deep-Dive.md](HAMi-Deep-Dive.md) | `v2.10.0` | Kubernetes 异构 AI 设备虚拟化与调度 | 关注 GPU 共享、设备隔离、多厂商设备管理的 Kubernetes 平台工程师 | MutatingWebhook、Scheduler Extender、Device Plugin、HAMi-Core、Annotation 协议、多厂商设备 |
| [Kubernetes-Native-Scheduler-Deep-Dive.md](Kubernetes-Native-Scheduler-Deep-Dive.md) | Kubernetes `v1.36.4` | Kubernetes 原生调度器深度解析 | 负责 Kubernetes 调度、GPU 集群和 AI 平台选型的工程师 | SchedulingQueue、Scheduling Framework、DRA 对象与生命周期、DynamicResources、PodGroup/Gang/TAS、工作负载级抢占、AI 调度器对比 |
| [Kubernetes-AI-Schedulers-Deep-Dive.md](Kubernetes-AI-Schedulers-Deep-Dive.md) | Koordinator `v1.8.0`；Kueue `v0.19.2`；Grove `alpha.11`；KAI `v0.17.0`；Volcano `v1.15.1` | Kubernetes AI 调度器深度对比 | 负责 GPU 集群、训练/推理平台、批任务队列和调度器选型的平台工程师 | Gang、队列公平、拓扑、KAI preemption delay、Volcano 补丁边界、组合架构与升级治理 |
| [Volcano-Upgrade-Compatibility-Deep-Dive.md](Volcano-Upgrade-Compatibility-Deep-Dive.md) | `v1.8.2 → v1.15.1` | Volcano 升级与 Feature 兼容性 | 负责 Volcano 升级、Queue 治理、Webhook 和共置能力的平台工程师 | Helm/Manifest、proportion/capacity、Agent、Cloud Native Colocation、DRA、gang-aware eviction、安全与调度修复 |
| [KServe-Deep-Dive.md](KServe-Deep-Dive.md) | `v0.20.0`；master `aaac4e2`；官网 `05b83a6` | KServe 生成式 AI 与预测式 AI 推理服务平台 | 关注 Kubernetes 上模型服务、推理网关和缓存能力的平台工程师 | InferenceService、LLMInferenceService v1alpha2、Gateway API、LocalModelCache、稳定 KV offloading/流量切分、主线 `ms://` 与 schema 警告边界 |
| [Kubeflow-Deep-Dive.md](Kubeflow-Deep-Dive.md) | Community Distribution `26.03.1` | Kubeflow Community Distribution 与端到端 MLOps 平台 | 关注多租户 MLOps、Notebook、Pipeline、训练和推理集成的平台工程师 | Dashboard、Profiles、Pipelines、Notebooks、Katib、Trainer、KServe 节点、Istio/OAuth2/Dex |

## 推荐阅读路径

- LLM 推理架构：先读 [Mooncake-Deep-Dive.md](Mooncake-Deep-Dive.md)，再读 [Dynamo-Deep-Dive.md](Dynamo-Deep-Dive.md)。前者聚焦 KVCache 与分离式推理机制，后者聚焦数据中心级编排和路由。
- 压测与容量评估：读 [LLM-Benchmark-Deep-Dive.md](LLM-Benchmark-Deep-Dive.md)。它适合在选型推理引擎、比较吞吐/延迟指标、设计 SLO/goodput 压测方案前阅读。
- AI 存储与文件系统：读 [Lustre-3FS-Deep-Dive.md](Lustre-3FS-Deep-Dive.md)。它适合理解 Lustre、3FS、RDMA/NVMe 共享存储、checkpoint、dataloader 和 KV cache on disk 的架构取舍。
- Kubernetes AI 平台：按 [NVIDIA-GPU-Operator-Deep-Dive.md](NVIDIA-GPU-Operator-Deep-Dive.md)、[HAMi-Deep-Dive.md](HAMi-Deep-Dive.md)、[Kubernetes-Native-Scheduler-Deep-Dive.md](Kubernetes-Native-Scheduler-Deep-Dive.md)、[Kubernetes-AI-Schedulers-Deep-Dive.md](Kubernetes-AI-Schedulers-Deep-Dive.md)、[Volcano-Upgrade-Compatibility-Deep-Dive.md](Volcano-Upgrade-Compatibility-Deep-Dive.md)、[KServe-Deep-Dive.md](KServe-Deep-Dive.md)、[Kubeflow-Deep-Dive.md](Kubeflow-Deep-Dive.md) 的顺序阅读。它们依次覆盖 NVIDIA 驱动与设备栈、GPU 共享和异构设备、原生调度基线、AI 队列与调度扩展、Volcano 升级兼容、模型推理服务以及上层 MLOps 平台。
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
