# AI 基础设施深度文档

这个仓库整理了一组 AI 基础设施 deep-dive 文档，并提供一个轻量的 Python 脚本将 Markdown 渲染为带样式、目录和 Mermaid 支持的 HTML 页面。

内容重点是 LLM 推理系统、压测评估、AI 存储与文件系统、基础设施身份与访问治理、Kubernetes AI 平台、GPU/异构资源调度、AI-native coding agent 协作与编排平台和 AI Sandbox 运行环境。源码文档位于仓库根目录，生成后的 HTML 文件会被 `.gitignore` 忽略。

## 版本与证据边界

当前文档集的审校截止日为 **2026-09-26**。正文优先固定官方最新非 draft、非 prerelease Release（Grove 保留正式 Alpha 标识），并在各文档页头或附录记录 annotated tag 解引用后的 exact source commit；lightweight tag 记录其直接 commit，没有 GitHub Release 的项目固定到审计时的分支 commit。`main`/`master` 后续能力只作为“未发布主线快照”单独说明，不计入稳定版兼容承诺。

**新稳定基线。** 本轮更新 Dynamo `v1.5.0@b83b1d9304ebfc624709ac46db32b1b6f1ff1615`、Agent Sandbox `v1.0.4@810726d89c71da77cdc82668bca1b00f5cd21ed8`、Warpgate `v0.29.1@54f93c807be2c161a94c0df764242849125161a8`、Multica `v0.5.3@ff8b285497809e084915016c40c2bc5e5991ffbc`、Kueue `v0.19.6@f0e95cea51b5591e0177fbe0fa06a299f36db548`、KAI-Scheduler `v0.18.0@2df9a1ffca535d602d57023074b824606e312797`、Kubernetes `v1.37.1@f78e722310e50bcaca9276be22276d9e91d91308`、AIPerf `v0.13.0@794f8bb75f8582f22e412d7e650fc71ca2a3d21a`、SGLang `v0.5.20@94602c9c2b7cbdb8efd5c52802dac6a1c180089e`、ollama-benchmark `v0.5.4@9e441efe48756928e453ff26694d6e5af1a9c71d`、vLLM `v0.30.0@ced6857afa0ea7b2e3f0846a62e1394e90f15607`、KServe `v0.21.0@d1482554fc4f66dd41aee70e01f5174e24f265bd` 与 GPU Operator `v26.7.1@dbacf43d4938816fefe62690ab868a640a195282`。annotated tag 均记录 peeled source commit，不把 tag object 当源码。

**推理与压测。** Dynamo v1.5.0 把 worker selection 改为可插拔 `WorkerScorer`/`WorkerPicker` 策略，CRD storage 升至 v1beta1、Rust EPP 成为默认并移除 Go EPP，`python -m dynamo.replay` 无 shim 移除，KVBM 重申 deprecated 并把移除目标定为 v1.6.0。vLLM v0.30.0 新增 Fast Start weight cache、HiSparse host tier 与水印采样，scale-out endpoint 改为 `--enable-scale-out` opt-in 并移除 GPTQ `g_idx`。SGLang v0.5.20 退役 CUDA 12 lane、把 `/v1/responses` store 改为 `--enable-response-store` opt-in，配置层改为 `msgspec.Struct` 并移除 17 个 deprecated flag。AIPerf v0.13.0 增加 Kubernetes native execution（beta）与 `--per-chunk-usage` 口径修正；ollama-benchmark v0.5.4 无条件调用 `stop_model`。跨版本结果必须按 CUDA lane、runner、缓存层级与依赖矩阵重建基线。

**Sandbox、访问与协作。** E2B SDK 主线快照前移到 `main@ccaf9fc0ffe6ac39c7ec786af7608ab1de19467b`，官方基础设施仓库已由 `e2b-dev/infra` 更名为 `e2b-dev/runtime`（既有固定链接经 301 继续解析）；Infra `2026.30` 本身未变。Agent Sandbox v1.0.4 增加 TLS profile、生命周期 Events、全异步 Python sandboxd 与 RL fleet run isolation。Multica v0.5.3 跨入 minor 线：UI 会话改滑动过期、OpenCode 最低 `1.1.54` 并支持 2.x、Issue 的 PR 完成判定收敛为 closing keyword、cache 写入计入 hit rate；25 种 protocol family 与七状态/Triage 合同经在新 pin 复核未变。Warpgate v0.29.1 引入 session approval/JIT 与 MFA 策略，并带破坏性 API 变化（兼容 Terraform provider v1.2.0、K8s operator v0.4.11）。

**Self-hosted 访问平台比较。** [Teleport、The Bastion、Warpgate 及扩展参照对比文档](Teleport-Deep-Dive.md) 以 Teleport `v18.10.0@ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d` 为主基线，同时固定 The Bastion `v3.24.01@30c8b522ddd9db2993e22b05b0ee19f961cadf1d`、Warpgate `v0.29.1@54f93c807be2c161a94c0df764242849125161a8`、Boundary `v0.21.3@8c9715c868537616a11e0ea555b20042e212bdbc`、Pomerium `v0.33.3@76042ed40db3bab9506b689f436716b6df624f23`；Guacamole 使用官方 `1.6.0` tag-only 的 server/client exact commit 作为审计证据（审校日无 GitHub Release）。正文按身份、授权、协议审计、HA、迁移和许可证统一比较，明确 Teleport Community/AGPL、Boundary BSL 1.1、Apache-2.0 项目及商业/主线边界，不把 tag-only、主线或 SaaS 能力写成稳定承诺。

Teleport 的官方下载二进制仍受 **Teleport Community Edition License** 与组织规模条件约束；AGPL-3.0 源码、Community binary 和 Enterprise/Cloud entitlement 必须分别复核。OIDC/SAML、资源级 JIT、**Session/Identity Lock**、Session Sharing/Moderation、Device Trust 和 Identity Security 属于商业/edition 边界，本文不提供法律意见。

**Kubernetes Blog/RSS 历史审计。** [Kubernetes Blog 新特性深度综述](Kubernetes-Blog-Feature-Deep-Dive.md) 已覆盖 2022 年起（约 v1.24）至 2026-09-26，以 Kubernetes `v1.37.1@f78e722310e50bcaca9276be22276d9e91d91308` 为稳定基线。9 月 17-25 日 RSS 实际新增 2 篇专题：PVC last-used-time（`Unused` condition，Beta/default-on）与 SIG Apps spotlight（社区访谈，KEP-4443 复活仅是计划）。v1.37.1 补丁不改 feature gate 与成熟度。Alpha/Beta、CSI 生态和 Working Group 内容只按各自成熟度记录，不扩大 Stable 承诺。

**Kubernetes 调度补丁。** Kueue v0.19.6 要求升级前上调 SparkApplication ClusterQueue 配额（现按 `cores` 与至少 384Mi 额外内存记账，且 memory 必须用 Spark Java 格式），DRA 残余资源记账收紧，`TASPartialSlices` gate 以 Alpha 默认开启；v1.19.5 同步修复 TAS leader 可行性与 FindMatchingWorkloads 越权。KAI v0.18.0 把 NvFractions GPU sharing、半抢占（alpha）与 in-place resize 记账纳入稳定版，`global.fips` 更名 `global.fipsMode`，镜像 base 改为 `scratch`。Kueue `v0.20.0-rc.1`、Volcano `v1.16.0-alpha.*`、vLLM `v0.30.1rc0` 与 KAI tag-only `v0.20.1@5922dc7d1a4661d3fc43d60943f92a775c892bdc` 不进入稳定基线；KAI tag-only 不替代 v0.18.0。

**稳定版未变化。** Mooncake `v0.3.13.post1@719735896c86b56fabec6cf3e825fb2ea640597a`、ModelExpress `v0.6.0@e91f650aa6a1847959e7f7da1b39c19e16b312e3`、E2B Infra `2026.30@f32ee8a2a50052f32e3632ceb451111a98dd5104`、Teleport `v18.10.0@ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d`、The Bastion `v3.24.01@30c8b522ddd9db2993e22b05b0ee19f961cadf1d`、Boundary `v0.21.3@8c9715c868537616a11e0ea555b20042e212bdbc`、Pomerium `v0.33.3@76042ed40db3bab9506b689f436716b6df624f23`、Grove `v0.1.0-alpha.13@af2df1ffff0ae7a1135554564a6240a3f22f2c35`、Volcano `v1.15.2@1462fb7b4835970708717456e3aed85e697ec2eb`、HAMi `v2.10.0@4707fb02c91c545bc7343ce26dba4c32919f9a3e`、Kubeflow Community Distribution `26.03.1`、Koordinator `v1.8.0`、GuideLLM `v0.7.4@291a6e609c3eb52d6eadcedecc7a056e396cd5eb`、inference-perf `v0.7.0@5804ea6b7ebd2bfceff29cf113311ed3af95146e`、genai-bench `v0.0.5`、EvalScope `v1.12.0@f09e55de5d5f0a0953cd90aa7b0382b45859c4f5` 与 LLMPerf `v2.0` 经复核保持原基线。Guacamole 使用官方 `1.6.0` tag-only 的 server/client exact commit 作为审计证据（审校日无 GitHub Release）。

**稳定对照与未发布快照。** Agent Sandbox 固定 `v1.0.4@810726d89c71da77cdc82668bca1b00f5cd21ed8`，继承 v1.0.0 的 v1beta1-only CRD/storage migration；这些不是 E2B Infra 功能。未发布证据固定为 E2B SDK `main@ccaf9fc0ffe6ac39c7ec786af7608ab1de19467b`、Multica `main@12f8f3f31111564e5e1b9aac3f7f916e8bba4039`、KServe `master@bb22cc477a6bd317bb2c7e357a85efcab8c7462a`、KServe 官网 `main@71c8b22a05d6be72560b2cc326865930063cd0e8`、Koordinator `main@618b581b32668e317b0d18523d46cf9f55b549d8` 与 Volcano 官网 `master@f5258704d7ef5bda28f31ba51950cdea9adbe921`。Volcano Helm 固定 `volcano-1.15.2@c2050e3debe58dbcdf9bb75b667799eec9409513`，3FS 固定 `main@22fca04564c7cc230fd8b9523b8b92864e1dad47`。主线和网站快照只证明审计时实现/文档形态。

KServe v0.21.0 把上一轮全部主线观察项纳入稳定版：LLMISVC rollout strategy（`spec.rolloutStrategy`）、canary readiness gating、KEDA true scale-to-zero、`oci+fetch://`、`ms://`、P/D NixlConnector、LoRA LocalModelCache、controller TLS 热重载、渲染后模板校验与 Python 3.13 均已随 release 提供；依赖升至 KEDA v2.20.2、Envoy AI Gateway v1.1.0、llm-d router v0.10.0。release 仓库 llmisvc sample 已迁移 v1alpha2/顶层 `spec.kvCacheOffloading`；固定官网快照仍保留 v1alpha1 旧示例，落地应以 v1alpha2 CRD schema 为准。`v0.21.0-rc0`/`rc1` 已被正式 Release 取代。

## 文档索引

| 文档 | 版本基线 | 主题 | 适合读者 | 覆盖重点 |
| --- | --- | --- | --- | --- |
| [Mooncake-Deep-Dive.md](Mooncake-Deep-Dive.md) | `v0.3.13.post1` | Mooncake 分离式 LLM 推理架构 | 关注 KVCache、prefill/decode 分离、推理性能优化的工程师 | Transfer Engine/TENT 新 transport、Mooncake Store、NVMe/DFS、HA OpLog、Conductor、结构化对象与多租户 |
| [Dynamo-Deep-Dive.md](Dynamo-Deep-Dive.md) | Dynamo `v1.5.0`；ModelExpress `v0.6.0` | Dynamo 数据中心级 LLM 推理编排 | 关注多节点推理服务、KV 路由和生产编排的工程师 | Request/Control/Storage 三平面、classify/pooling、NIXL loader、KV relay、Planner、Operator、KVBM 边界与 ModelExpress RL refit |
| [E2B-Deep-Dive.md](E2B-Deep-Dive.md) | Infra `2026.30`；SDK `main@ccaf9fc0`；Agent Sandbox `v1.0.4` | E2B AI Sandbox 与自托管架构 | 关注代码执行沙箱、microVM、安全隔离、团队配额和私有化部署的工程师 | Firecracker、fork、filesystem-only resume、workload identity、Secrets、Kubernetes 分发与 Agent Sandbox scoped-token/迁移对照 |
| [Teleport-Deep-Dive.md](Teleport-Deep-Dive.md) | Teleport `v18.10.0@ddaa46b`；The Bastion `v3.24.01`；Warpgate `v0.29.1`；Boundary `v0.21.3`；Pomerium `v0.33.3`；Guacamole `1.6.0` tag-only | Self-hosted 基础设施访问平台对比 | 需要在 OpenSSH/VPN/堡垒机、Teleport、The Bastion、Warpgate、Boundary、Pomerium 与 Guacamole 间做选型的平台、安全和运维工程师 | 统一能力矩阵、信任边界、身份/凭据生命周期、SSH/Kubernetes/DB/HTTP/RDP/VNC 协议深度、录制/SIEM、HA/故障、迁移验收与许可证边界 |
| [Multica-Deep-Dive.md](Multica-Deep-Dive.md) | `v0.5.3`；main `12f8f3f3` | AI-native 团队任务管理与 coding agent 编排平台 | 关注 coding agent 团队协作、本地 CLI 执行、自托管和权限治理的工程师 | Issue lifecycle/Triage、Task/runs、Codex usage/thread、Channel/Desktop、25 种 protocol family、Squad、Autopilot、MCP 与无 Sandbox 边界 |
| [LLM-Benchmark-Deep-Dive.md](LLM-Benchmark-Deep-Dive.md) | AIPerf `v0.13.0`；GuideLLM `v0.7.4`；inference-perf `v0.7.0`；SGLang `v0.5.20`；vLLM `v0.30.0`；EvalScope `v1.12.0` | LLM 压测工具深度对比 | 需要选择或设计推理压测方案的工程师 | AgentX/agentic trace、token source/window、SGLang 缓存、vLLM MRV2/weight sync、EvalScope PD/流式指标与工具对比 |
| [Lustre-3FS-Deep-Dive.md](Lustre-3FS-Deep-Dive.md) | Lustre 官方资料；3FS `main@22fca04` | Lustre 与 3FS 深度技术文档 | 关注 AI 存储、HPC 并行文件系统、RDMA/NVMe 共享存储和 KVCache 落盘的工程师 | Lustre MDS/OSS/OST/LNet、3FS Meta/Storage/CRAQ/USRBIO、dataloader、checkpoint、KV cache、生产选型 |
| [NVIDIA-GPU-Operator-Deep-Dive.md](NVIDIA-GPU-Operator-Deep-Dive.md) | `v26.7.1` | NVIDIA GPU Operator 节点软件栈与生命周期管理 | 负责 Kubernetes GPU 驱动、设备接入、共享隔离和生产运维的平台工程师 | Controller 调谐、ClusterPolicy、GPUCluster/DRA、Driver/Toolkit/Device Plugin、CDI/NRI、MIG、Time-Slicing/MPS、DCGM、升级排障 |
| [HAMi-Deep-Dive.md](HAMi-Deep-Dive.md) | `v2.10.0` | Kubernetes 异构 AI 设备虚拟化与调度 | 关注 GPU 共享、设备隔离、多厂商设备管理的 Kubernetes 平台工程师 | MutatingWebhook、Scheduler Extender、Device Plugin、HAMi-Core、独立 DRA driver、init-container 记账、PodGroup/MIG/mutex/NUMA、多厂商设备 |
| [Kubernetes-Blog-Feature-Deep-Dive.md](Kubernetes-Blog-Feature-Deep-Dive.md) | Kubernetes v1.24—v1.37；Blog/RSS 截止 2026-09-26 | Kubernetes Blog/RSS 跨 SIG 特性历史审计 | 需要理解 Kubernetes 版本演进、成熟度、升级和 AI 平台组合的工程师 | v1.24—v1.37 演进链、Workload/Gang、Node lifecycle、resize preemption、Native Histograms、Memory QoS、CBT、storage hardening 与 rootless |
| [Kubernetes-Native-Scheduler-Deep-Dive.md](Kubernetes-Native-Scheduler-Deep-Dive.md) | Kubernetes `v1.37.1` | Kubernetes 原生调度器深度解析 | 负责 Kubernetes 调度、GPU 集群和 AI 平台选型的工程师 | SchedulingQueue、Scheduling Framework、DRA v1.37 扩展、Workload/PodGroup v1beta1、CompositePodGroup、Gang/TAS 与工作负载级抢占 |
| [Kubernetes-AI-Schedulers-Deep-Dive.md](Kubernetes-AI-Schedulers-Deep-Dive.md) | Koordinator `v1.8.0`；Kueue `v0.19.6`；Grove `alpha.13`；KAI `v0.18.0`；Volcano `v1.15.2` | Kubernetes AI 调度器深度对比 | 负责 GPU 集群、训练/推理平台、批任务队列和调度器选型的平台工程师 | Kueue TAS/MultiKueue/DRA/配额、Grove PodGangMap、KAI gang floor/namespace/anti-affinity/GPU score、Volcano GHSA 与升级治理 |
| [Volcano-Upgrade-Compatibility-Deep-Dive.md](Volcano-Upgrade-Compatibility-Deep-Dive.md) | `v1.8.2 → v1.15.2` | Volcano 升级与 Feature 兼容性 | 负责 Volcano 升级、Queue 治理、Webhook 和共置能力的平台工程师 | Helm/Manifest、proportion/capacity、Agent、Cloud Native Colocation、DRA O(1) 安全修复、reclaim/preempt 与 gang-aware eviction |
| [KServe-Deep-Dive.md](KServe-Deep-Dive.md) | `v0.21.0`；master `bb22cc47`；官网 `71c8b22` | KServe 生成式 AI 与预测式 AI 推理服务平台 | 关注 Kubernetes 上模型服务、推理网关和缓存能力的平台工程师 | InferenceService、LLMInferenceService v1alpha2、Gateway API、LocalModelCache、稳定 KV offloading/流量切分、主线 `ms://`/NIXL/LoRA cache 与 schema 警告边界 |
| [Kubeflow-Deep-Dive.md](Kubeflow-Deep-Dive.md) | Community Distribution `26.03.1` | Kubeflow Community Distribution 与端到端 MLOps 平台 | 关注多租户 MLOps、Notebook、Pipeline、训练和推理集成的平台工程师 | Dashboard、Profiles、Pipelines、Notebooks、Katib、Trainer、KServe 节点、Istio/OAuth2/Dex |

## 推荐阅读路径

- LLM 推理架构：先读 [Mooncake-Deep-Dive.md](Mooncake-Deep-Dive.md)，再读 [Dynamo-Deep-Dive.md](Dynamo-Deep-Dive.md)。前者聚焦 KVCache 与分离式推理机制，后者聚焦数据中心级编排和路由。
- 压测与容量评估：读 [LLM-Benchmark-Deep-Dive.md](LLM-Benchmark-Deep-Dive.md)。它以 SGLang `v0.5.20`、vLLM `v0.30.0` 和 EvalScope `v1.12.0` 为关键基线，适合在选型推理引擎、比较吞吐/延迟指标、设计 SLO/goodput 压测方案前阅读。
- AI 存储与文件系统：读 [Lustre-3FS-Deep-Dive.md](Lustre-3FS-Deep-Dive.md)。它适合理解 Lustre、3FS、RDMA/NVMe 共享存储、checkpoint、dataloader 和 KV cache on disk 的架构取舍。
- 基础设施身份与访问治理：读 [Teleport、The Bastion、Warpgate 对比文档](Teleport-Deep-Dive.md)。它先解释 Teleport 的 Auth/Proxy/Agent、短期证书、Role/标签、MFA、反向隧道和多协议审计，再用统一矩阵比较 The Bastion 的 Unix DAC/syslog/ttyrec、Warpgate 的单二进制与 SQLite、Boundary 的 Vault session broker、Pomerium 的 HTTP/TCP 零信任入口和 Guacamole 的浏览器 RDP/VNC 网关；Teleport 及这些平台都不替 Kubernetes/KServe/Kubeflow 的原生 RBAC、E2B 的 microVM 隔离、Multica 的 agent 协作编排或目标数据库/云 IAM 授权。
- Kubernetes AI 平台：按 [Kubernetes-Blog-Feature-Deep-Dive.md](Kubernetes-Blog-Feature-Deep-Dive.md) → [Kubernetes-Native-Scheduler-Deep-Dive.md](Kubernetes-Native-Scheduler-Deep-Dive.md) → [Kubernetes-AI-Schedulers-Deep-Dive.md](Kubernetes-AI-Schedulers-Deep-Dive.md) → [Volcano-Upgrade-Compatibility-Deep-Dive.md](Volcano-Upgrade-Compatibility-Deep-Dive.md) → [KServe-Deep-Dive.md](KServe-Deep-Dive.md) / [Kubeflow-Deep-Dive.md](Kubeflow-Deep-Dive.md) 阅读；需要节点设备和共享隔离细节时，再补读 [NVIDIA-GPU-Operator-Deep-Dive.md](NVIDIA-GPU-Operator-Deep-Dive.md) 与 [HAMi-Deep-Dive.md](HAMi-Deep-Dive.md)。这条路径依次覆盖 v1.24—v1.37 Blog/RSS 特性演进、原生调度基线、Kueue `v0.19.6`/Grove `alpha.13`/KAI `v0.18.0` AI 队列与调度扩展、Volcano 升级兼容、模型推理服务以及上层 MLOps 平台。
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
