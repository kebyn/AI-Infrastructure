# AI 基础设施深度文档

这个仓库整理了一组 AI 基础设施 deep-dive 文档，并提供一个轻量的 Python 脚本将 Markdown 渲染为带样式、目录和 Mermaid 支持的 HTML 页面。

内容重点是 LLM 推理系统、压测评估、AI 存储与文件系统、基础设施身份与访问治理、Kubernetes AI 平台、GPU/异构资源调度、AI-native coding agent 协作与编排平台和 AI Sandbox 运行环境。源码文档位于仓库根目录，生成后的 HTML 文件会被 `.gitignore` 忽略。

## 版本与证据边界

当前文档集的审校截止日为 **2026-09-17**。正文优先固定官方最新非 draft、非 prerelease Release（Grove 保留正式 Alpha 标识），并在各文档页头或附录记录 annotated tag 解引用后的 exact source commit；lightweight tag 记录其直接 commit，没有 GitHub Release 的项目固定到审计时的分支 commit。`main`/`master` 后续能力只作为“未发布主线快照”单独说明，不计入稳定版兼容承诺。

**新稳定基线。** 本轮更新 ModelExpress `v0.6.0@e91f650aa6a1847959e7f7da1b39c19e16b312e3`、E2B Infra `2026.30@f32ee8a2a50052f32e3632ceb451111a98dd5104`、Agent Sandbox `v1.0.2@9a85153590e54cb980f3241f9e7a9228449412c9`、KAI-Scheduler `v0.17.2@b46e4a1168441f97997ba7d1db772891ac6695c2`、Kueue `v0.19.4@5d738f203bd0d301d4966282b144f01d5bb32437`、ollama-benchmark `v0.5.3@a6a2e419abb83fdc2f8a4d766c26567a008dbc96`、inference-perf `v0.7.0@5804ea6b7ebd2bfceff29cf113311ed3af95146e`、EvalScope `v1.12.0@f09e55de5d5f0a0953cd90aa7b0382b45859c4f5`、GuideLLM `v0.7.4@291a6e609c3eb52d6eadcedecc7a056e396cd5eb`、vLLM `v0.29.0@98dff2a81d747d1dba01a47f939f48c3526d4206`、Multica `v0.4.44@c7f259c70a60bff30011c403fada79ab382f608a` 与 Pomerium `v0.33.3@76042ed40db3bab9506b689f436716b6df624f23`。annotated tag 均记录 peeled source commit，不把 tag object 当源码。

**推理与压测。** ModelExpress v0.6.0 增加 RL reshard-refit、trainer/generator client、Prometheus、S3 provider、Helm/CRD/RBAC 与异构 CUDA/XPU source。vLLM v0.29.0 默认启用 MRV2，并增加 sharded RDT weight sync、Mamba prefix cache 与新默认值/破坏性迁移。inference-perf v0.7.0、EvalScope v1.12.0、GuideLLM v0.7.4 和 ollama-benchmark v0.5.3 分别更新 agentic/trace replay、AgentX/PD timing、warmup/cooldown token window 和安全依赖；跨版本结果必须按 token source、窗口、流式 reasoning 和失败/重试口径重建基线。

**Sandbox、访问与协作。** E2B Infra 2026.30 删除旧 access-token authentication/表和数据库只读副本支持，新增 workload identity、Secrets、动态日志路由、filesystem-only resume、集群注册与 envd 升级，并退休仓库中的 Nomad 部署配置。Agent Sandbox v1.0.2 增加 Ed25519 scoped-token v2，同时改变 `authz.Authorizer` 签名和 Router namespace。Multica v0.4.44 最终采用七个 built-in/custom status key 加四类 lifecycle，Triage 使用独立 `triage_state` 且没有 executor；release 过程中出现后撤回的 reserved `triage` key 不属于最终合同。Pomerium v0.33.2 没有发布产物，v0.33.3 取代它。

**Self-hosted 访问平台比较。** [Teleport、The Bastion、Warpgate 及扩展参照对比文档](Teleport-Deep-Dive.md) 以 Teleport `v18.10.0@ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d` 为主基线，同时固定 The Bastion `v3.24.01@30c8b522ddd9db2993e22b05b0ee19f961cadf1d`、Warpgate `v0.28.6@525c7caf2219d5f5e3913b5732e4cbad5d15cd34`、Boundary `v0.21.3@8c9715c868537616a11e0ea555b20042e212bdbc`、Pomerium `v0.33.3@76042ed40db3bab9506b689f436716b6df624f23`；Guacamole 使用官方 `1.6.0` tag-only 的 server/client exact commit 作为审计证据（审校日无 GitHub Release）。正文按身份、授权、协议审计、HA、迁移和许可证统一比较，明确 Teleport Community/AGPL、Boundary BSL 1.1、Apache-2.0 项目及商业/主线边界，不把 tag-only、主线或 SaaS 能力写成稳定承诺。

Teleport 的官方下载二进制仍受 **Teleport Community Edition License** 与组织规模条件约束；AGPL-3.0 源码、Community binary 和 Enterprise/Cloud entitlement 必须分别复核。OIDC/SAML、资源级 JIT、**Session/Identity Lock**、Session Sharing/Moderation、Device Trust 和 Identity Security 属于商业/edition 边界，本文不提供法律意见。

**Kubernetes Blog/RSS 历史审计。** [Kubernetes Blog 新特性深度综述](Kubernetes-Blog-Feature-Deep-Dive.md) 已覆盖 2022 年起（约 v1.24）至 2026-09-17，仍以 Kubernetes `v1.37.0@f54c212e3a2f75d674b717a9b29052b20b60aefc` 为稳定基线。9 月 8-16 日 RSS 实际新增 8 篇专题，覆盖 workload-aware scheduling、Node Lifecycle Conditions、in-place resize preemption、Native Histograms、Memory QoS、Changed Block Tracking、Pod-Level Resource Managers 与 storage hardening。Alpha/Beta、CSI 生态和 Working Group 内容只按各自成熟度记录，不扩大 Stable 承诺。

**Kubernetes 调度补丁。** Kueue v0.19.4 增加 gated TAS grouped slicing 和 MultiKueue client config 复用，并修复 DRA/effective resource、StatefulSet quota、TAS reclaim/hot-swap 与 TrainJob；KAI v0.17.2 修复 hierarchical gang floor、跨 namespace 同名 PodGroup、releasing-Pod anti-affinity 和非 GPU Pod 错误 GPU score。Kueue `v0.20.0-rc.0`、Volcano `v1.16.0-alpha.*` 和 KAI tag-only `v0.20.1@5922dc7d1a4661d3fc43d60943f92a775c892bdc` 不进入稳定基线；KAI tag-only 不替代 v0.17.2。

**稳定版未变化。** Mooncake `v0.3.13.post1@719735896c86b56fabec6cf3e825fb2ea640597a`、Dynamo `v1.4.2@2ecbdfdf192c69c02c6d21e931d20d3b4a0bb64a`、Teleport `v18.10.0@ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d`、SGLang `v0.5.19@0bcd822377da7b5718e674eaf9c870d349424dd1`、Kubernetes `v1.37.0@f54c212e3a2f75d674b717a9b29052b20b60aefc`、Grove `v0.1.0-alpha.13@af2df1ffff0ae7a1135554564a6240a3f22f2c35`、Volcano `v1.15.2@1462fb7b4835970708717456e3aed85e697ec2eb`、KServe `v0.20.0`、GPU Operator `v26.7.0@10ee5b3638b89e11e949412aafa5ba99279c3721`、HAMi `v2.10.0@4707fb02c91c545bc7343ce26dba4c32919f9a3e`、Kubeflow Community Distribution `26.03.1`、Koordinator `v1.8.0`、AIPerf `v0.12.0`、genai-bench `v0.0.5` 与 LLMPerf `v2.0` 经复核保持原基线。`v0.21.0-rc0`、vLLM `v0.29.1rc0` 等 prerelease 不改变稳定承诺。

**稳定对照与未发布快照。** Agent Sandbox 固定 `v1.0.2@9a85153590e54cb980f3241f9e7a9228449412c9`，继承 v1.0.0 的 v1beta1-only CRD/storage migration，并新增 scoped-token v2、SDK 直连和 WarmPool/RL；这些不是 E2B Infra 功能。未发布证据固定为 E2B SDK `main@3e5a48b00eb133ac1e98697d549574301c605e81`、Multica `main@7e4758ac1a94e9ff843696333364610bb8d4bbf7`、KServe `master@85991f1693d4713f498702f8e2b350a9ef520db2`、KServe 官网 `main@71c8b22a05d6be72560b2cc326865930063cd0e8`、Koordinator `main@96cef825562c27d4d8e8c177ad998d908f4d05a2` 与 Volcano 官网 `master@aee652b985d25e33f59f6112e857627784b741ca`。Volcano Helm 固定 `volcano-1.15.2@c2050e3debe58dbcdf9bb75b667799eec9409513`，3FS 固定 `main@22fca04564c7cc230fd8b9523b8b92864e1dad47`。主线和网站快照只证明审计时实现/文档形态。

KServe v0.20.0 仍以 LLMISVC v1alpha2 的 `spec.kvCacheOffloading`、`route.group`/`route.weight`、Anthropic `/v1/messages`、Managed DRA 和分布式 tracing 为稳定边界。rollout strategy、canary readiness、KEDA true scale-to-zero、合并配置模板后的 dry-run 校验、`oci+fetch://`、`ms://`、P/D NixlConnector、LoRA LocalModelCache 和 TLS 证书热重载仍只属于固定 master；v0.20.0 release sample 与官网快照继续存在 v1alpha1/旧 `spec.workload.kvCacheOffloading` 路径混用风险，落地应以 v1alpha2 CRD schema 为准。

## 文档索引

| 文档 | 版本基线 | 主题 | 适合读者 | 覆盖重点 |
| --- | --- | --- | --- | --- |
| [Mooncake-Deep-Dive.md](Mooncake-Deep-Dive.md) | `v0.3.13.post1` | Mooncake 分离式 LLM 推理架构 | 关注 KVCache、prefill/decode 分离、推理性能优化的工程师 | Transfer Engine/TENT 新 transport、Mooncake Store、NVMe/DFS、HA OpLog、Conductor、结构化对象与多租户 |
| [Dynamo-Deep-Dive.md](Dynamo-Deep-Dive.md) | Dynamo `v1.4.2`；ModelExpress `v0.6.0` | Dynamo 数据中心级 LLM 推理编排 | 关注多节点推理服务、KV 路由和生产编排的工程师 | Request/Control/Storage 三平面、classify/pooling、NIXL loader、KV relay、Planner、Operator、KVBM 边界与 ModelExpress RL refit |
| [E2B-Deep-Dive.md](E2B-Deep-Dive.md) | Infra `2026.30`；SDK `main@3e5a48b`；Agent Sandbox `v1.0.2` | E2B AI Sandbox 与自托管架构 | 关注代码执行沙箱、microVM、安全隔离、团队配额和私有化部署的工程师 | Firecracker、fork、filesystem-only resume、workload identity、Secrets、Kubernetes 分发与 Agent Sandbox scoped-token/迁移对照 |
| [Teleport-Deep-Dive.md](Teleport-Deep-Dive.md) | Teleport `v18.10.0@ddaa46b`；The Bastion `v3.24.01`；Warpgate `v0.28.6`；Boundary `v0.21.3`；Pomerium `v0.33.3`；Guacamole `1.6.0` tag-only | Self-hosted 基础设施访问平台对比 | 需要在 OpenSSH/VPN/堡垒机、Teleport、The Bastion、Warpgate、Boundary、Pomerium 与 Guacamole 间做选型的平台、安全和运维工程师 | 统一能力矩阵、信任边界、身份/凭据生命周期、SSH/Kubernetes/DB/HTTP/RDP/VNC 协议深度、录制/SIEM、HA/故障、迁移验收与许可证边界 |
| [Multica-Deep-Dive.md](Multica-Deep-Dive.md) | `v0.4.44`；main `7e4758a` | AI-native 团队任务管理与 coding agent 编排平台 | 关注 coding agent 团队协作、本地 CLI 执行、自托管和权限治理的工程师 | Issue lifecycle/Triage、Task/runs、Codex usage/thread、Channel/Desktop、25 种 protocol family、Squad、Autopilot、MCP 与无 Sandbox 边界 |
| [LLM-Benchmark-Deep-Dive.md](LLM-Benchmark-Deep-Dive.md) | AIPerf `v0.12.0`；GuideLLM `v0.7.4`；inference-perf `v0.7.0`；SGLang `v0.5.19`；vLLM `v0.29.0`；EvalScope `v1.12.0` | LLM 压测工具深度对比 | 需要选择或设计推理压测方案的工程师 | AgentX/agentic trace、token source/window、SGLang 缓存、vLLM MRV2/weight sync、EvalScope PD/流式指标与工具对比 |
| [Lustre-3FS-Deep-Dive.md](Lustre-3FS-Deep-Dive.md) | Lustre 官方资料；3FS `main@22fca04` | Lustre 与 3FS 深度技术文档 | 关注 AI 存储、HPC 并行文件系统、RDMA/NVMe 共享存储和 KVCache 落盘的工程师 | Lustre MDS/OSS/OST/LNet、3FS Meta/Storage/CRAQ/USRBIO、dataloader、checkpoint、KV cache、生产选型 |
| [NVIDIA-GPU-Operator-Deep-Dive.md](NVIDIA-GPU-Operator-Deep-Dive.md) | `v26.7.0` | NVIDIA GPU Operator 节点软件栈与生命周期管理 | 负责 Kubernetes GPU 驱动、设备接入、共享隔离和生产运维的平台工程师 | Controller 调谐、ClusterPolicy、GPUCluster/DRA、Driver/Toolkit/Device Plugin、CDI/NRI、MIG、Time-Slicing/MPS、DCGM、升级排障 |
| [HAMi-Deep-Dive.md](HAMi-Deep-Dive.md) | `v2.10.0` | Kubernetes 异构 AI 设备虚拟化与调度 | 关注 GPU 共享、设备隔离、多厂商设备管理的 Kubernetes 平台工程师 | MutatingWebhook、Scheduler Extender、Device Plugin、HAMi-Core、独立 DRA driver、init-container 记账、PodGroup/MIG/mutex/NUMA、多厂商设备 |
| [Kubernetes-Blog-Feature-Deep-Dive.md](Kubernetes-Blog-Feature-Deep-Dive.md) | Kubernetes v1.24—v1.37；Blog/RSS 截止 2026-09-17 | Kubernetes Blog/RSS 跨 SIG 特性历史审计 | 需要理解 Kubernetes 版本演进、成熟度、升级和 AI 平台组合的工程师 | v1.24—v1.37 演进链、Workload/Gang、Node lifecycle、resize preemption、Native Histograms、Memory QoS、CBT、storage hardening 与 rootless |
| [Kubernetes-Native-Scheduler-Deep-Dive.md](Kubernetes-Native-Scheduler-Deep-Dive.md) | Kubernetes `v1.37.0` | Kubernetes 原生调度器深度解析 | 负责 Kubernetes 调度、GPU 集群和 AI 平台选型的工程师 | SchedulingQueue、Scheduling Framework、DRA v1.37 扩展、Workload/PodGroup v1beta1、CompositePodGroup、Gang/TAS 与工作负载级抢占 |
| [Kubernetes-AI-Schedulers-Deep-Dive.md](Kubernetes-AI-Schedulers-Deep-Dive.md) | Koordinator `v1.8.0`；Kueue `v0.19.4`；Grove `alpha.13`；KAI `v0.17.2`；Volcano `v1.15.2` | Kubernetes AI 调度器深度对比 | 负责 GPU 集群、训练/推理平台、批任务队列和调度器选型的平台工程师 | Kueue TAS/MultiKueue/DRA/配额、Grove PodGangMap、KAI gang floor/namespace/anti-affinity/GPU score、Volcano GHSA 与升级治理 |
| [Volcano-Upgrade-Compatibility-Deep-Dive.md](Volcano-Upgrade-Compatibility-Deep-Dive.md) | `v1.8.2 → v1.15.2` | Volcano 升级与 Feature 兼容性 | 负责 Volcano 升级、Queue 治理、Webhook 和共置能力的平台工程师 | Helm/Manifest、proportion/capacity、Agent、Cloud Native Colocation、DRA O(1) 安全修复、reclaim/preempt 与 gang-aware eviction |
| [KServe-Deep-Dive.md](KServe-Deep-Dive.md) | `v0.20.0`；master `85991f1`；官网 `71c8b22` | KServe 生成式 AI 与预测式 AI 推理服务平台 | 关注 Kubernetes 上模型服务、推理网关和缓存能力的平台工程师 | InferenceService、LLMInferenceService v1alpha2、Gateway API、LocalModelCache、稳定 KV offloading/流量切分、主线 `ms://`/NIXL/LoRA cache 与 schema 警告边界 |
| [Kubeflow-Deep-Dive.md](Kubeflow-Deep-Dive.md) | Community Distribution `26.03.1` | Kubeflow Community Distribution 与端到端 MLOps 平台 | 关注多租户 MLOps、Notebook、Pipeline、训练和推理集成的平台工程师 | Dashboard、Profiles、Pipelines、Notebooks、Katib、Trainer、KServe 节点、Istio/OAuth2/Dex |

## 推荐阅读路径

- LLM 推理架构：先读 [Mooncake-Deep-Dive.md](Mooncake-Deep-Dive.md)，再读 [Dynamo-Deep-Dive.md](Dynamo-Deep-Dive.md)。前者聚焦 KVCache 与分离式推理机制，后者聚焦数据中心级编排和路由。
- 压测与容量评估：读 [LLM-Benchmark-Deep-Dive.md](LLM-Benchmark-Deep-Dive.md)。它以 SGLang `v0.5.19`、vLLM `v0.29.0` 和 EvalScope `v1.12.0` 为关键基线，适合在选型推理引擎、比较吞吐/延迟指标、设计 SLO/goodput 压测方案前阅读。
- AI 存储与文件系统：读 [Lustre-3FS-Deep-Dive.md](Lustre-3FS-Deep-Dive.md)。它适合理解 Lustre、3FS、RDMA/NVMe 共享存储、checkpoint、dataloader 和 KV cache on disk 的架构取舍。
- 基础设施身份与访问治理：读 [Teleport、The Bastion、Warpgate 对比文档](Teleport-Deep-Dive.md)。它先解释 Teleport 的 Auth/Proxy/Agent、短期证书、Role/标签、MFA、反向隧道和多协议审计，再用统一矩阵比较 The Bastion 的 Unix DAC/syslog/ttyrec、Warpgate 的单二进制与 SQLite、Boundary 的 Vault session broker、Pomerium 的 HTTP/TCP 零信任入口和 Guacamole 的浏览器 RDP/VNC 网关；Teleport 及这些平台都不替 Kubernetes/KServe/Kubeflow 的原生 RBAC、E2B 的 microVM 隔离、Multica 的 agent 协作编排或目标数据库/云 IAM 授权。
- Kubernetes AI 平台：按 [Kubernetes-Blog-Feature-Deep-Dive.md](Kubernetes-Blog-Feature-Deep-Dive.md) → [Kubernetes-Native-Scheduler-Deep-Dive.md](Kubernetes-Native-Scheduler-Deep-Dive.md) → [Kubernetes-AI-Schedulers-Deep-Dive.md](Kubernetes-AI-Schedulers-Deep-Dive.md) → [Volcano-Upgrade-Compatibility-Deep-Dive.md](Volcano-Upgrade-Compatibility-Deep-Dive.md) → [KServe-Deep-Dive.md](KServe-Deep-Dive.md) / [Kubeflow-Deep-Dive.md](Kubeflow-Deep-Dive.md) 阅读；需要节点设备和共享隔离细节时，再补读 [NVIDIA-GPU-Operator-Deep-Dive.md](NVIDIA-GPU-Operator-Deep-Dive.md) 与 [HAMi-Deep-Dive.md](HAMi-Deep-Dive.md)。这条路径依次覆盖 v1.24—v1.37 Blog/RSS 特性演进、原生调度基线、Kueue `v0.19.4`/Grove `alpha.13`/KAI `v0.17.2` AI 队列与调度扩展、Volcano 升级兼容、模型推理服务以及上层 MLOps 平台。
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
