# AI 基础设施深度文档

这个仓库整理了一组 AI 基础设施 deep-dive 文档，并提供一个轻量的 Python 脚本将 Markdown 渲染为带样式、目录和 Mermaid 支持的 HTML 页面。

内容重点是 LLM 推理系统、压测评估、AI 存储与文件系统、基础设施身份与访问治理、Kubernetes AI 平台、GPU/异构资源调度、AI-native coding agent 协作与编排平台和 AI Sandbox 运行环境。源码文档位于仓库根目录，生成后的 HTML 文件会被 `.gitignore` 忽略。

## 版本与证据边界

基础设施文档与模型时间线本轮统一以 **2026-10-13** 为审校截止日；本轮完成固定范围内的官方上游 release、预览线和主线快照复核，并按稳定版、预览版、tag-only 与未发布主线分别记录，不把预览能力写成稳定兼容承诺。

各领域文档保留完整版本、annotated tag 解引用后的 exact source commit、官方来源与迁移限制。正式 Release、Grove Alpha、Beta API、Guacamole tag-only 和未发布主线快照分别记录；主线能力不计入稳定版兼容承诺。Kubeflow `26.03.1` 所带组件及安装 patch 与独立 KServe `v0.21.0` 分别固定，不能把后者能力推定为前者已集成。

旧专题已合并为下列 7 篇领域文档，旧 Markdown、页面入口和 HTML 产物已移除。综合文档使用“分篇 → 章节 → 小节”编号；左侧目录展示分篇和章节，小节仍有可定位锚点。旧文件及每个旧标题的保留、合并或去重落点记录在 [docs_migration.json](docs_migration.json)，供维护与内容验收使用，不提供旧地址重定向。

## 文档索引

| 文档 | 版本基线 | 主题 | 适合读者 | 覆盖重点 |
| --- | --- | --- | --- | --- |
| [推理系统与压测](AI-Inference-Deep-Dive.md) | Mooncake `v0.3.13.post1`；Dynamo `v1.5.1`；ModelExpress `v0.7.0`；AIPerf `v0.13.0`；SGLang `v0.5.21`；vLLM `v0.31.0`；EvalScope `v1.13.0` | 推理架构与容量评估 | 推理系统与性能工程师 | 公共概念、Mooncake、Dynamo、压测工具与评估方法、组合架构与选型 |
| [Kubernetes AI 平台](Kubernetes-AI-Platform-Deep-Dive.md) | Kubernetes `v1.37.1`（预览线 `v1.38.0-alpha.2`）；GPU Operator `v26.7.1`；HAMi `v2.10.0`；Kueue `v0.20.1`；Grove `alpha.15`；KAI `v0.18.5`；Volcano `v1.15.3`（升级 `v1.8.2 → v1.15.3`）；KServe `v0.21.0`；Kubeflow `26.03.1` | Kubernetes AI 平台 | 平台与 GPU 运维工程师 | 版本演进、原生调度、节点设备、AI 调度、Volcano 升级、KServe、Kubeflow 与统一选型 |
| [AI 存储与文件系统：Lustre 与 3FS](Lustre-3FS-Deep-Dive.md) | Lustre 官方资料；3FS `main@22fca04` | Lustre 与 3FS 深度技术文档 | 关注 AI 存储、HPC 并行文件系统、RDMA/NVMe 共享存储和 KVCache 落盘的工程师 | Lustre MDS/OSS/OST/LNet、3FS Meta/Storage/CRAQ/USRBIO、dataloader、checkpoint、KV cache、生产选型 |
| [基础设施访问治理：Self-hosted 平台对比](Teleport-Deep-Dive.md) | Teleport `v18.10.0@ddaa46b`；The Bastion `v3.24.01`；Warpgate `v0.29.2`；Boundary `v0.21.3`；Pomerium `v0.33.4`；Guacamole `1.6.0` tag-only | Self-hosted 基础设施访问平台对比 | 需要在 OpenSSH/VPN/堡垒机、Teleport、The Bastion、Warpgate、Boundary、Pomerium 与 Guacamole 间做选型的平台、安全和运维工程师 | 统一能力矩阵、信任边界、身份/凭据生命周期、SSH/Kubernetes/DB/HTTP/RDP/VNC 协议深度、录制/SIEM、HA/故障、迁移验收与许可证边界 |
| [Agent 协作与编排：Multica](Multica-Deep-Dive.md) | `v0.6.2@7ab92d76`；main 同 commit | AI-native 团队任务管理与 coding agent 编排平台 | 关注 coding agent 团队协作、本地 CLI 执行、自托管和权限治理的工程师 | Issue lifecycle/Triage、Task/runs、Codex usage/thread、Channel/Desktop、25 种 protocol family、Squad、Autopilot、MCP 与无 Sandbox 边界 |
| [Sandbox 与执行环境：E2B](E2B-Deep-Dive.md) | Infra `2026.30`；SDK `main@62a17dfc`；Agent Sandbox `v1.0.6` | E2B AI Sandbox 与自托管架构 | 关注代码执行沙箱、microVM、安全隔离、团队配额和私有化部署的工程师 | Firecracker、fork、filesystem-only resume、workload identity、Secrets、Kubernetes 分发与 Agent Sandbox scoped-token/迁移对照 |
| [model_release_timeline.md](model_release_timeline.md) | 2022—2026-10-13；审校 2026-10-13 | 模型发布时间时间线 | 需要按厂商、年份或开放形态检索主线模型的读者 | 九大阵营、首次公开日期、发布形态、官方来源；页面支持供应商/年份/多模态/开放权重筛选和 CSV/JSON/Markdown 导出 |

## 推荐阅读路径

- LLM 推理与容量评估：按[公共概念](AI-Inference-Deep-Dive.md#inference-concepts) → [Mooncake](AI-Inference-Deep-Dive.md#mooncake) → [Dynamo](AI-Inference-Deep-Dive.md#dynamo) → [压测工具](AI-Inference-Deep-Dive.md#benchmark) → [组合选型](AI-Inference-Deep-Dive.md#inference-selection) 阅读。
- 模型版本检索：读 [model_release_timeline.md](model_release_timeline.md)；它按首次公开日期整理九大阵营的主线模型，生成页面可按供应商、年份、多模态和开放权重筛选，并把当前结果导出为 CSV、JSON 或 Markdown。筛选状态会写入 URL，便于分享和复用。
- AI 存储与文件系统：读 [Lustre-3FS-Deep-Dive.md](Lustre-3FS-Deep-Dive.md)。它适合理解 Lustre、3FS、RDMA/NVMe 共享存储、checkpoint、dataloader 和 KV cache on disk 的架构取舍。
- 基础设施身份与访问治理：读 [Teleport、The Bastion、Warpgate 对比文档](Teleport-Deep-Dive.md)。它先解释 Teleport 的 Auth/Proxy/Agent、短期证书、Role/标签、MFA、反向隧道和多协议审计，再用统一矩阵比较 The Bastion 的 Unix DAC/syslog/ttyrec、Warpgate 的单二进制与 SQLite、Boundary 的 Vault session broker、Pomerium 的 HTTP/TCP 零信任入口和 Guacamole 的浏览器 RDP/VNC 网关；Teleport 及这些平台都不替 Kubernetes/KServe/Kubeflow 的原生 RBAC、E2B 的 microVM 隔离、Multica 的 agent 协作编排或目标数据库/云 IAM 授权。
- Kubernetes AI 平台：按[版本演进](Kubernetes-AI-Platform-Deep-Dive.md#k8s-history) → [原生调度](Kubernetes-AI-Platform-Deep-Dive.md#k8s-scheduler) → [GPU Operator](Kubernetes-AI-Platform-Deep-Dive.md#gpu-operator) / [HAMi](Kubernetes-AI-Platform-Deep-Dive.md#hami) → [AI 调度器](Kubernetes-AI-Platform-Deep-Dive.md#ai-schedulers) → [Volcano 升级](Kubernetes-AI-Platform-Deep-Dive.md#volcano-upgrade) → [KServe](Kubernetes-AI-Platform-Deep-Dive.md#kserve) / [Kubeflow](Kubernetes-AI-Platform-Deep-Dive.md#kubeflow) → [统一选型](Kubernetes-AI-Platform-Deep-Dive.md#platform-selection) 阅读。
- Agent 协作与执行平台：读 [Multica-Deep-Dive.md](Multica-Deep-Dive.md)。它聚焦 Issue/Task、Agent/Runtime、Squad 和 Autopilot 如何编排本机 coding agent CLI；Multica 默认不提供 Sandbox，不能把工作目录或 provider adapter 当作隔离边界。
- Sandbox 与执行环境：读 [E2B-Deep-Dive.md](E2B-Deep-Dive.md)。它聚焦 Firecracker microVM 通用隔离 Sandbox、自托管部署取舍，以及 Team/Project 配额、可靠计量、预算与内部成本分摊的补建边界，与 Multica 的协作编排和本地 CLI 执行路径不同。

## 本地预览

`serve_docs.py` 会把已注册的 Markdown 文档（包括 `*-Deep-Dive.md` 和模型发布时间时间线）渲染为 HTML，并生成首页 `index.html`。脚本默认监听 `80` 端口，根路径 `/` 会返回首页。

首页、深度文档和模型时间线共用顶部导航与「明亮 / 暗色 / 跟随系统」主题。首次访问跟随系统，手动选择保存在浏览器本地，刷新、跨页和同源标签页之间保持一致；选择「跟随系统」时会实时响应系统配色。浏览器禁止本地存储时，仍可切换当前页面主题；未启用 JavaScript 时由 CSS 跟随系统配色。

首页可以搜索标题和摘要，并按推理与压测、模型时间线、存储、访问治理、Kubernetes 平台、Agent 协作、Sandbox 分类筛选。搜索忽略大小写，与分类共同限制结果；页面显示匹配数量，无结果时可使用「清除搜索与分类」恢复全部文档。自定义 `DOCS` 条目可填写可选的 `category` 字段，未填写或不在上述分类中的条目归入「其他」。

文档页在桌面显示左侧目录，手机使用左下角「目录」按钮打开抽屉。抽屉支持键盘焦点循环、关闭按钮、Escape 与遮罩关闭，关闭后焦点返回原控件。长表格和代码块可以在各自区域横向滚动。Mermaid 图随主题重新渲染，加载或渲染失败时保留可读的原始图定义。时间线继续支持筛选、URL 状态与 CSV / JSON / Markdown 导出。

首次运行使用 uv 创建虚拟环境并安装锁定的依赖：

```bash
uv sync --locked
```

日常命令无需手动激活虚拟环境；如需交互式 shell，可选执行 `source .venv/bin/activate`。

运行测试：

```bash
uv run --locked python -m unittest test_serve_docs.py
```

浏览器交互测试为可选测试，不增加项目运行依赖。需要验证主题持久化、标签页同步、Mermaid 切换、搜索分类、移动目录和时间线导出时，可安装 Chromium 后运行完整测试：

```bash
uv run --locked --with playwright python -m playwright install --with-deps chromium
uv run --locked --with playwright python -m unittest test_serve_docs.py
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
- `model_release_timeline.html` 是模型发布时间时间线的独立页面。
- `*.html` 已在 `.gitignore` 中忽略，不需要提交。
- Python 缓存文件 `__pycache__/` 和 `*.py[cod]` 也已忽略。
