# Kubernetes Blog 新特性深度综述

> **Kubernetes v1.36/v1.37、Gateway API、AI/Agent 平台、控制面性能、安全与运维的 RSS 综述**
>
> 本文基于 [Kubernetes Blog RSS](https://kubernetes.io/feed.xml) 中 2026 年截至 2026-09-06 的文章，以及对应的官方 Blog 页面、Release 页面、文档、KEP 和 v1.37.0 源码整理。它关注跨 SIG 的平台能力，不替代本仓库的 [Kubernetes 原生调度器深度技术文档](Kubernetes-Native-Scheduler-Deep-Dive.html) 或 [Kubernetes AI 调度器深度对比](Kubernetes-AI-Schedulers-Deep-Dive.html)。
>
> 稳定版本基线：Kubernetes <code>v1.37.0@f54c212e3a2f75d674b717a9b29052b20b60aefc</code>；v1.36 作为仍影响 v1.37 升级和生产落地的前置版本回溯；审校日期：2026-09-06。<code>v1.37.0</code> 是 annotated tag，正文以解引用后的 source commit 为准，不把 tag object 当作源码提交。

> **先给结论：** v1.37 的重要变化不是某一个孤立 API，而是把平台的“可管理单位”逐步从单个 Pod 推向 Workload、设备、资源拓扑、控制面状态和工作负载身份。Stable 能力已经可以进入常规生产基线；Beta 仍要逐集群验证默认 gate、组件版本和生态实现；Alpha 以及 Blog 中的生态项目只能作为试验或架构方向，不能自动写入稳定兼容承诺。

---

## 目录

- [自动生成目录占位](#自动生成目录占位)

---

## 第一章：RSS 范围与证据边界

### 1.1 这篇综述读取了什么

RSS 是发现入口，不是版本合同。本文的时间窗口是 2026 年 RSS 中截至 2026-09-06 已发布的文章，重点选择以下四类：

| 类型 | 纳入方式 | 证据边界 |
| --- | --- | --- |
| Kubernetes release/feature Blog | 纳入 v1.36、v1.37 的 API、feature gate、控制器和节点能力 | 以对应文章、Release 页面、KEP 与目标 source commit 交叉核对 |
| Gateway API/etcd 等上游项目文章 | 纳入与 Kubernetes 平台直接相关的版本和迁移影响 | 项目版本独立于 Kubernetes minor 版本，不能只看 Kubernetes release |
| AI/Agent/Headlamp 生态文章 | 提炼 CRD、扩展接口、操作模型和采用边界 | 明确标为生态/提案/教程，不把它们写成 Kubernetes Core API |
| 观点、访谈、路线图和预告 | 只保留能影响平台决策的事实 | “计划”“建议”“roadmap”不等于已发布实现 |

RSS XML 的 <code>description</code> 是文章摘要或 HTML 片段，不能代替网页正文；正文以对应官方页面为准。链接、日期和成熟度也应以审校时的 RSS 与 Release 页面为准，未来文章发布不会自动改变本文的历史截止边界。

### 1.2 截至 2026-09-06 的近期文章地图

下表列出本文的主要证据入口。它不是把 RSS 文章长段复制到仓库，而是把相互关联的文章按平台问题重新组织。

| RSS 日期 | 官方文章 | 本文归类 | 主要结论 |
| --- | --- | --- | --- |
| 2026-09-04 | [KubeletInUserNamespace Graduates to Beta](https://kubernetes.io/blog/2026/09/04/kubernetes-v1-37-rootless-beta/) | v1.37 / 节点安全 | 节点组件可在预先建立的 Linux user namespace 中以非 root 主机用户运行；gate 默认开启不等于集群自动 rootless |
| 2026-09-03 | [DRA Updates](https://kubernetes.io/blog/2026/09/03/kubernetes-v1-37-dra-updates/) | v1.37 / 设备资源 | DRA extended resource、设备状态、设备 taint/toleration 和标准 NUMA 属性进入 Stable；Workload claim 与更多设备配对能力仍分层演进 |
| 2026-09-02 | [HPA Scale-to-Zero](https://kubernetes.io/blog/2026/09/02/kubernetes-v1-37-hpa-scale-to-zero-beta/) | v1.37 / 弹性 | <code>HPAScaleToZero</code> 进入 Beta，支持对象指标或外部指标驱动的 <code>minReplicas: 0</code> |
| 2026-09-01 | [etcd RangeStream](https://kubernetes.io/blog/2026/09/01/kubernetes-v1-37-etcd-range-stream/) | v1.37 / 控制面 | 与 etcd 3.7 配合，把大集合读取从一次性缓冲改为分块流式读取 |
| 2026-08-31 | [Storage Version Migration Enabled by Default](https://kubernetes.io/blog/2026/08/31/kubernetes-v1-37-storage-version-migration-ga/) | v1.37 / API 生命周期 | <code>storagemigration.k8s.io/v1</code> 和内置迁移控制器进入 GA 并默认启用 |
| 2026-08-28 | [Pod Certificates and Cluster Trust Bundles](https://kubernetes.io/blog/2026/08/28/kubernetes-v1-37-pod-certificates-and-cluster-trust-bundles/) | v1.37 / 身份 | Pod 可通过 projected volume 获得由 signer 签发和轮换的 X.509 凭据与 trust bundle |
| 2026-08-27 | [Metrics API graduates to stable](https://kubernetes.io/blog/2026/08/27/kubernetes-v1-37-metrics-api-ga/) | v1.37 / 可观测性 | <code>metrics.k8s.io/v1</code> Stable；资源类型和字段与 <code>v1beta1</code> 相同 |
| 2026-08-26 | [Kubernetes v1.37: Garhwal](https://kubernetes.io/blog/2026/08/26/kubernetes-v1-37-release/) | v1.37 / 总览 | 67 项增强：16 Stable、23 Beta、27 Alpha、1 项弃用/移除 |
| 2026-08-11 | [KYAML](https://kubernetes.io/blog/2026/08/11/how-to-pretty-print-kubernetes-yaml-as-kyaml/) | v1.37 / CLI | KYAML 是兼容 YAML 的更严格子集，<code>kubectl get -o kyaml</code> 进入 Stable |
| 2026-08-03 | [Gateway API v1.6](https://kubernetes.io/blog/2026/08/03/gateway-api-v1-6-release/) | 网络 / API | TCPRoute 和 UDPRoute 进入 Standard；实验资源迁移到独立的 <code>x-k8s</code> API group |
| 2026-07-29 | [controller-runtime Cache](https://kubernetes.io/blog/2026/07/29/controller-runtime-cache-explained/) | 控制器开发 | <code>Get/List</code> 默认走本地 list/watch cache，低 API 请求成本与内存、陈旧读、隐藏扫描是同一个设计的两面 |
| 2026-07-14 | [Custom Metrics Exporter](https://kubernetes.io/blog/2026/07/14/custom-metrics-exporter-kubernetes/) | 可观测性 / HPA | 自定义指标适配器是 HPA 的外部依赖，不是 Kubernetes Core 指标 API 的自动扩展 |
| 2026-07-13 | [Headlamp Kubeflow Plugin](https://kubernetes.io/blog/2026/07/13/introducing-headlamp-plugin-for-kubeflow/) | AI 平台生态 | 让 Notebook、TrainJob、Katib 等 CRD 在通用 Kubernetes UI 中可观测 |
| 2026-06-25 | [Headlamp Volcano Plugin](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/) 与 [Headlamp Knative Plugin](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/) | 运维生态 | 插件改善批任务和 serverless 资源的操作体验，不改变底层调度或伸缩语义 |
| 2026-05-13 至 2026-04-22 | [v1.36 Workload-Aware Scheduling](https://kubernetes.io/blog/2026/05/13/kubernetes-v1-36-advancing-workload-aware-scheduling/)、[DRA](https://kubernetes.io/blog/2026/05/07/kubernetes-v1-36-dra-136-updates/)、[Server-Side Sharded List and Watch](https://kubernetes.io/blog/2026/05/06/kubernetes-v1-36-server-side-sharded-list-and-watch/)、[Declarative Validation](https://kubernetes.io/blog/2026/05/05/kubernetes-v1-36-declarative-validation-ga/)、[Memory QoS](https://kubernetes.io/blog/2026/04/29/kubernetes-v1-36-memory-qos-tiered-protection/) 等 | v1.36 前置能力 | v1.37 的 Workload、设备、控制面和 cgroups v2 变化都建立在这批 Alpha/Beta/GA 演进上 |
| 2026-03-20 至 2026-03-09 | [Agent Sandbox](https://kubernetes.io/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/)、[Ingress2Gateway 1.0](https://kubernetes.io/blog/2026/03/20/ingress2gateway-1-0-release/)、[AI Gateway Working Group](https://kubernetes.io/blog/2026/03/09/announcing-ai-gateway-wg/) | AI/网络生态 | AI agent 的隔离状态工作负载、迁移工具和 AI 流量标准仍处于生态项目/提案边界 |

RSS 里还有大量社区 spotlight、项目维护和教程文章。它们可以帮助理解生态方向，但本文不会把 Headlamp 插件、AI Gateway proposal、Agent Sandbox CRD 或某个 Gateway controller 的实现误写成 Kubernetes <code>v1.37.0</code> 的 Core API。

### 1.3 成熟度的读法

| 标签 | 可以说明什么 | 不能说明什么 |
| --- | --- | --- |
| Stable / GA | API 或行为达到长期兼容承诺，默认状态和弃用策略由 Kubernetes API policy 约束 | 不保证 CSI、CRI、CNI、DRA driver 或 Gateway controller 已经实现 |
| Beta | API 形态相对稳定，通常已有集成测试；可能默认开启，也可能仍默认关闭 | 不等于所有平台都应该打开；版本混跑、性能和回滚仍需验证 |
| Alpha | 设计或实现仍可能变化，通常默认关闭 | 不能作为生产兼容合同、跨 minor 回滚依据或第三方生态前置条件 |
| Ecosystem / proposal | 上游项目或社区正在围绕 Kubernetes 构建能力 | 不属于 Kubernetes Core 的 feature gate、API server 或 kubelet 默认行为 |

特别要区分“进入 Beta”和“默认开启”。例如 v1.37 的 <code>GenericWorkload</code>、<code>DRAWorkloadResourceClaims</code>、<code>PodLevelResourceManagers</code>、<code>PodAndContainerStatsFromCRI</code> 虽然是 Beta，但最终配置仍有默认关闭的项目；反过来 <code>HPAScaleToZero</code>、<code>MemoryQoS</code> 和 <code>EtcdRangeStream</code> 是 Beta 且默认开启。最终判断以目标版本 source 中的 <code>defaultVersionedKubernetesFeatureGates</code> 和组件配置为准。

---

## 第二章：Kubernetes v1.37 总览

### 2.1 Garhwal release 的数量和主线

官方 v1.37 Release 页面把本版本命名为 Garhwal，并统计：

| 维度 | 数量 | 解读 |
| --- | ---: | --- |
| 全部增强 | 67 | 包含 API、控制器、kubelet、scheduler、CLI 和弃用/移除 |
| Stable | 16 | 多为把已有 Beta 能力固定为生产接口或默认路径 |
| Beta | 23 | 重点集中在 HPA、Workload/DRA、控制面读路径、Memory QoS、统计和安全 |
| Alpha | 27 | 包括复杂 Workload 组合、DRA 拓扑/可见性、StatefulSet Recreate 等 |
| 弃用/移除 | 1 | 需要结合 v1.37 的 deprecation/removal notes 做升级盘点 |

从平台工程视角，v1.37 有五条主线：

1. **大规模控制面更可预测。** <code>RangeStream</code>、watch cache 初始化保护、并发 watch object decode 和 API 指标把“大列表/大 watch”从内存尖峰问题推进到可观测、可退化路径。
2. **资源管理从 Pod 级走向 Workload 和设备拓扑。** Workload/PodGroup、Gang Scheduling、workload-aware preemption、DRA claim、NUMA 属性和节点资源管理开始组合成一条链。
3. **弹性从“至少一个 Pod”走向真正闲时为零。** HPA scale-to-zero 将队列、批处理和 GPU worker 的 idle 成本治理纳入 Core，但要求有独立于 Pod 的对象/外部指标。
4. **安全从静态凭据和粗权限走向身份、隔离和恢复。** User Namespaces、rootless kubelet、Pod Certificates、ClusterTrustBundles、细粒度 kubelet API 授权和不可解密资源处置各自解决不同层面的 blast radius。
5. **网络和开发体验开始收敛接口。** Gateway API 的 Standard channel 扩展、KYAML、<code>metrics.k8s.io/v1</code>、contextual logging 和 controller-runtime 的缓存认知，减少实现特有配置和操作盲点。

### 2.2 稳定能力、默认能力和生态能力的分层

下面三层是 v1.37 落地时最实用的心智模型：

    Stable API / locked gate
        ├─ 可进入平台基线，但仍需验证 driver/controller 兼容
    Beta API / default on
        ├─ 可在灰度集群试用，记录指标和退回开关
    Beta API / default off
        ├─ 先做显式 gate、版本混跑、回滚和数据对象演练
    Alpha 或生态项目
        └─ 只在隔离环境验证，不能写入 Stable 兼容承诺

v1.37 不是把所有“新特性”同时打开。尤其对于 AI 平台，要把 <code>GenericWorkload</code>、<code>DRAWorkloadResourceClaims</code>、<code>TopologyAwareWorkloadScheduling</code>、<code>PodLevelResourceManagers</code> 和 DRA 的若干 Alpha gate 当作独立开关，并验证它们的依赖关系。

### 2.3 与已有两篇调度文档的分工

| 文档 | 关注点 | 本文只保留的交集 |
| --- | --- | --- |
| [Kubernetes 原生调度器深度技术文档](Kubernetes-Native-Scheduler-Deep-Dive.html) | scheduler queue、Scheduling Framework、DRA 插件、Workload/PodGroup 调度周期和源码 | 只总结 v1.37 的成熟度、升级和跨 SIG 依赖 |
| [Kubernetes AI 调度器深度对比](Kubernetes-AI-Schedulers-Deep-Dive.html) | Koordinator、Kueue、Grove、KAI-Scheduler、Volcano 的架构和选型 | 只说明这些项目可以如何消费上游 Workload、DRA、Gateway 和 metrics 能力 |
| 本文 | Blog/RSS 中跨 SIG 的 API、节点、网络、安全、存储和生态变化 | 给出全局平台组合、成熟度和升级检查 |

---

## 第三章：控制面与 API Server

### 3.1 etcd RangeStream：大列表的内存峰值从“整页”变成“分块”

传统 etcd unary <code>Range</code> 会先把结果集合组装在内存中，再一次性通过 gRPC 返回。对于包含大量 Pod、CRD 或较大对象的 list，etcd 侧的 key-value slice、序列化 protobuf 和发送 buffer 可能同时存在；API server 还要持有并解码这批数据。分页只限制 key 数，不能保证每页字节数稳定。

v1.37 的 <code>EtcdRangeStream</code> 把读取路径改为 server-streaming RPC：

- etcd 3.7 的 <code>RangeStream</code> 复用 <code>RangeRequest</code>，把结果分成多个 chunk；
- chunk 大小依据对象 value 大小自适应，释放已解码的 chunk；
- API server 在同一个 MVCC revision 上合并结果，保持 snapshot consistency；
- watch cache 初始化和不能从 cache 服务的直接 list 都可以消费流；
- API server 在 etcd 返回 <code>Unimplemented</code> 时回退到 unary <code>Range</code>，所以旧 etcd 不会因为这个 gate 直接失去 list 能力。

它是 <code>kube-apiserver</code> 侧的 Beta 能力，<code>EtcdRangeStream</code> 在 v1.37 默认开启，但要真正使用需要 etcd <code>v3.7+</code>：

    client List
       │
       ▼
    kube-apiserver ── watch cache init / direct list
       │
       ├── EtcdRangeStream=true + etcd >= 3.7 ──► chunk 1 ─► decode/release
       │                                           chunk 2 ─► decode/release
       │                                           ...
       └── old etcd / Unimplemented ─────────────► unary Range fallback

可以用下面的指标检查流式路径是否实际命中：

    etcd_request_duration_seconds_count{operation="listStream"}

生产含义：

1. RangeStream 降低的是大集合读取的内存占用和尖峰，不是把所有 list/watch 变成低成本操作；错误的高频全量 list 仍然会伤害 API server。
2. 应把 etcd 3.7 升级、API server gate、<code>apiserver_storage_list_duration_seconds</code> 和 etcd listStream 指标作为一个变更单元。
3. 兼容旧 etcd 的 fallback 有利于渐进升级，但混合状态下性能不一致，容量测试不能只在 fallback 路径完成。
4. 通过 <code>MaxRequestBytes</code>、对象大小和大规模 Pod/CRD 数据集进行压测，才能判断实际峰值，而不是只验证 RPC 成功。

证据：[RangeStream Blog](https://kubernetes.io/blog/2026/09/01/kubernetes-v1-37-etcd-range-stream/)、[KEP-5966](https://kep.k8s.io/5966)、[v1.37 source](https://github.com/kubernetes/kubernetes/tree/f54c212e3a2f75d674b717a9b29052b20b60aefc)。

### 3.2 Resilient Watch Cache Initialization：把恢复风暴变成有界拒绝

watch cache 在 API server 启动和重新初始化时需要从 etcd 读取资源全集。旧行为可能让大量 list/watch 同时压到 etcd，或者在 cache 尚未 ready 时让请求积压，最终消耗 API Priority and Fairness 容量。

v1.37 完成了 resilient watch cache initialization 的成熟化：

- <code>ResilientWatchCacheInitialization</code> 已在 v1.34 Stable；
- <code>WatchCacheInitializationPostStartHook</code> 在 v1.37 进入 Stable 并锁定为开启；
- v1.36 起默认启用，启动和恢复时会对请求进行有界处理；
- API server 可以对暂时无法服务的请求返回 <code>HTTP 429</code>，客户端必须尊重 <code>Retry-After</code> 并采用指数退避；
- <code>ConcurrentWatchObjectDecode</code> 在 v1.37 默认开启的 Beta 路径中，用有界 worker pool 并发 decode/transform，再按原顺序交付事件。

并发 decode 能减少 CRD conversion webhook 或单个慢事件阻塞整个冷 cache 的风险，但它会把转换并发度从单路提高到默认约十路。升级前应确认 conversion webhook 自己的并发限制、CPU 额度、超时和失败策略，不能只看到 API server 初始化变快。

这里的关键不是“所有 429 都是故障”，而是客户端是否有可恢复的 backoff 设计。自研 controller、operator 和数据采集器若把 429 当作永久错误，会把一个有界的控制面保护机制放大成业务中断。

### 3.3 Storage Version Migration：API 版本升级必须有存储迁移闭环

<code>Storage Version Migration</code>（SVM）在 v1.37 进入 GA，API 为 <code>storagemigration.k8s.io/v1</code>，内置 <code>StorageVersionMigrator</code> controller 默认启用。它解决的是“API 已经有新 preferred/storage version，但 etcd 中仍有旧序列化对象”的问题。

典型场景是 CRD 从 <code>v1alpha1</code>/<code>v1beta1</code> 迁移到 <code>v1</code>，或者启用/轮换 encryption at rest 后需要通过 API server 重写已有对象。只更新 CRD <code>storage: true</code> 并不会自动保证每个旧对象都已经被重新序列化。

迁移流程可以是：

    apiVersion: storagemigration.k8s.io/v1
    kind: StorageVersionMigration
    metadata:
      name: crontabs-migration
    spec:
      resource:
        group: example.com
        resource: crontabs

控制面会观察 <code>StorageVersionMigration</code>，逐步重写目标资源并更新 status。生产检查至少包括：

- <code>status.conditions</code> 中 <code>Succeeded=True</code>；
- CRD 的 <code>.status.storedVersions</code> 已不再包含准备移除的旧版本；
- 迁移期间没有并发修改 CRD storage version 或 conversion webhook 合同；
- 迁移后的对象能用新版本读写，并经过 admission、conversion 和业务 controller 回归；
- encryption key rotation 后，按安全团队要求验证旧密钥不可用时的恢复路径。

SVM 是通用的存储迁移 API，不是升级工具的万能自动修复。对于 v1.36 Workload/PodGroup 的 <code>scheduling.k8s.io/v1alpha2</code> 到 v1.37 <code>v1beta1</code> 迁移，必须遵守该 API 自己的移除和对象清理要求；不能假设 SVM 会在不再 served 的版本上替代 API 兼容迁移。

证据：[Storage Version Migration Blog](https://kubernetes.io/blog/2026/08/31/kubernetes-v1-37-storage-version-migration-ga/)、[KEP-4192](https://kep.k8s.io/4192)、[Storage Version Migration 文档](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/storage-version-migration/)。

### 3.4 Server-side sharded list/watch：把过滤前移到 API server

v1.36 引入的 Server-side sharded list/watch 是 Alpha，feature gate 为 <code>ShardedListAndWatch</code>，默认关闭。它针对的是横向扩展 controller 的常见浪费：每个 replica 都接收全集事件、反序列化全集，然后丢弃不属于自己的对象。

开启后，客户端在 <code>ListOptions</code> 中传递 <code>shardSelector</code>，API server 使用确定性的 64-bit FNV-1a hash 过滤资源。当前支持的字段路径是：

- <code>object.metadata.uid</code>
- <code>object.metadata.namespace</code>

示意：

    shardSelector := "shardRange(object.metadata.uid, '0x0000000000000000', '0x8000000000000000')"
    factory := informers.NewSharedInformerFactoryWithOptions(
        client,
        resyncPeriod,
        informers.WithTweakListOptions(func(opts *metav1.ListOptions) {
            opts.ShardSelector = shardSelector
        }),
    )

如果响应 metadata 带有 <code>shardInfo.selector</code>，说明 API server 确实应用了 shard；没有该字段时，客户端要准备好收到完整集合并做 client-side fallback。生产 controller 还要解决 shard ownership、replica 变更、hash range 重平衡、watch 重连和对象迁移期间的重复/遗漏审计。它不是“给所有 list 加一个 selector”就结束的性能开关。

证据：[v1.36 Server-Side Sharded List and Watch](https://kubernetes.io/blog/2026/05/06/kubernetes-v1-36-server-side-sharded-list-and-watch)、[KEP-5866](https://kep.k8s.io/5866)。

### 3.5 Declarative Validation：把 native API 约束变成可读的契约

Declarative Validation 在 v1.36 进入 GA。它通过 <code>+k8s:</code> marker 把 required、minimum、maximum、list type、union、immutable 等规则写在 Go type 定义附近，由 <code>validation-gen</code> 生成验证代码。<code>DeclarativeValidation</code> gate 在 v1.36 已默认开启并锁定。

这会改善三件事：

1. API reviewer 和客户端可以在类型定义、OpenAPI 和生成代码之间建立更清晰的对应关系；
2. 新 API 不必继续堆积大量手写验证函数；
3. validation ratcheting 可以在更新旧对象时区分“字段未变”和“新写入非法值”，减小收紧规则对存量对象的冲击。

它不是允许客户端绕过 webhook、CEL 或 CRD schema 的新通道。自定义 API 仍要分别检查 OpenAPI schema、CEL、conversion、admission 和 controller 对字段的语义。升级后如果对象在过去依赖宽松验证，必须对 update、patch、server-side apply 和旧 client 做回归。

证据：[Declarative Validation Blog](https://kubernetes.io/blog/2026/05/05/kubernetes-v1-36-declarative-validation-ga)、[API validation 文档](https://kubernetes.io/docs/reference/using-api/declarative-validation/)。

### 3.6 Manifest-based admission：在 API server 启动前加载不可由 API 删除的策略

<code>ManifestBasedAdmissionControlConfig</code> 在 v1.36 是 Alpha，v1.37 升为 Beta 并默认开启。管理员可以在 <code>AdmissionConfiguration</code> 中设置 <code>staticManifestsDir</code>，让 API server 从磁盘读取 <code>ValidatingAdmissionPolicy</code>、binding 和 admission webhook 等资源。

最重要的特性不是“换一种写 YAML 的方式”，而是两个启动/自保护性质：

- 这些策略在 API server 开始对外服务前加载，即使 etcd 暂时不可用也可以执行；
- 静态 manifest 中的策略可以保护 API 中的 admission 配置资源，防止有权限的用户把关键策略删除或修改；
- 静态对象要求使用 <code>.static.k8s.io</code> 后缀，避免和 API 管理的对象发生名称混淆；
- 修复策略的恢复路径在文件系统和 API server 重启，不依赖被策略本身拦截的 API 操作。

示意：

    apiVersion: apiserver.config.k8s.io/v1
    kind: AdmissionConfiguration
    plugins:
    - name: ValidatingAdmissionPolicy
      configuration:
        apiVersion: apiserver.config.k8s.io/v1
        kind: ValidatingAdmissionPolicyConfiguration
        staticManifestsDir: /etc/kubernetes/admission/validating-policies/

这把策略文件分发、权限、checksum、原子替换、回滚和启动失败处理都纳入控制面供应链。生产中应把目录内容纳入 GitOps 或镜像构建，测试坏 YAML、坏 CEL、冲突名称和 API server 重启；不要让“无法由 API 删除”演化成“没有紧急修复负责人”。

证据：[Admission Policies That Can't Be Deleted](https://kubernetes.io/blog/2026/05/04/kubernetes-v1-36-manifest-based-admission-control)、[KEP-5793](https://kep.k8s.io/5793)。

### 3.7 Node Declared Features：让控制面感知节点的能力边界

Node Declared Features 在 v1.37 进入 Stable。kubelet 根据启动时的 feature gate 和静态配置填充 <code>Node.status.declaredFeatures</code>，scheduler、admission controller 或 API server 可以据此处理节点版本混跑。

对平台的价值是把“这台 Node 是否具备某个节点侧 Beta 能力”从 label 猜测变成 Kubernetes 认识的状态。对运维的要求是：

- gate 或静态配置变化通常需要重启 kubelet 才会重新计算；
- 特性进入 Stable 且版本 skew 窗口可以假定所有节点支持后，节点可能不再报告该特性；
- DRA 的 node allocatable 等能力依赖节点声明时，调度端不能只检查 control-plane gate；
- rootless、cgroups v2、DRA driver 和 CPU/Topology manager 的实际能力仍要结合运行时检查。

这项能力减少了混合节点版本的误判，但不替代节点镜像、CRI、CNI、CSI 和 device plugin 的兼容矩阵。

---

## 第四章：弹性、调度和资源管理

### 4.1 HPA Scale-to-Zero：<code>minReplicas: 0</code> 的条件和边界

<code>HPAScaleToZero</code> 在 v1.37 进入 Beta，<code>kube-apiserver</code> 和 <code>kube-controller-manager</code> 默认开启。HPA 可以在配置了对象指标或外部指标时，把 workload 从一个或多个副本缩到零，再在指标恢复时扩回去。

最小可读示例：

    apiVersion: autoscaling/v2
    kind: HorizontalPodAutoscaler
    metadata:
      name: queue-worker
    spec:
      scaleTargetRef:
        apiVersion: apps/v1
        kind: Deployment
        name: queue-worker
      minReplicas: 0
      maxReplicas: 10
      metrics:
      - type: External
        external:
          metric:
            name: queue_consumer_lag
            selector:
              matchLabels:
                name: worker_tasks
          target:
            type: Value
            value: "30"

必须同时理解这些条件：

1. CPU 和 memory resource metrics 依赖运行中的 Pod；Pod 为零时没有可计算的 worker signal。因此 <code>minReplicas: 0</code> 至少需要 object metric 或 external metric。
2. 外部指标必须在 <code>external.metrics.k8s.io</code> 可读，通常需要 Prometheus Adapter 或其他 metrics adapter。adapter 不可用时，HPA 会显示 <code>ScalingActive=False</code>，不会凭空唤醒 worker。
3. HPA 用 <code>ScaledToZero=True</code> 区分“自己缩到零”和“管理员手动把 Deployment 设为零”。后者仍被视为暂停，不应被 HPA 自动唤醒。
4. 默认 downscale stabilization window 仍然生效，短暂的队列下降不应立即清空所有 worker；需要结合队列持久性、冷启动时间和 <code>spec.behavior.scaleDown</code> 调整。
5. Kubernetes Service 不会在没有 ready Pod 时替 HTTP 请求做持久缓冲。在线同步推理、Agent 对话和 streaming API 要么保持 warm replica，要么引入队列/网关/激活器，不能把 scale-to-zero 当作无感知 serverless。

升级和回滚顺序很明确：在两类控制面组件都支持并开启 <code>HPAScaleToZero</code> 前，不要新建 <code>minReplicas: 0</code> HPA；禁用 gate 或回滚到没有 condition 语义的版本前，把 HPA 改回至少 1，并把当前为零的 workload 手动拉起。

这项能力最适合队列消费者、批处理 worker、低频 GPU worker 和可接受冷启动的内部服务。对请求驱动的 LLM serving，冷启动包括指标发现、调度、镜像/模型加载和 cache 预热，必须单独测量。

### 4.2 Workload/PodGroup 与 Gang Scheduling：调度单位上移

v1.36 把 Workload API 的静态模板语义与 PodGroup 的运行时状态语义分开，并引入新的 PodGroup scheduling cycle。v1.37 将核心 Workload/PodGroup API 提升到 <code>scheduling.k8s.io/v1beta1</code>，基础 Gang Scheduling 和 workload-aware preemption 进入 Beta 路径。

基础链路可抽象为：

    Job / JobSet / TrainJob / RayJob / LWS controller
            │
            ├─ Workload：声明 PodSets、priority、scheduling policy
            └─ PodGroup：记录运行时 admission、placement、status
                             │
                             ▼
                      kube-scheduler PodGroup cycle
                             │
                     all-or-nothing / preemption
                             │
                             ▼
                       individual Pod binding

这里有三个常被混淆的点：

- **API maturity 与默认开启独立。** <code>GenericWorkload</code> 在 v1.37 是 Beta，但默认关闭；关闭时不能因为 API 类型存在就把 Gang 行为当成默认调度合同。
- **Gang 与队列准入不同。** Gang 负责一组 Pod 的原子调度/最小可运行规模；Kueue、Volcano 或其他系统负责 queue、quota、fair sharing 和跨 workload 准入时，还要处理两层状态的一致性。
- **workload-aware preemption 与普通 Pod 抢占不同。** 它可以按 PodGroup 选择 victims，使被抢占的 workload 更可能整体获得进展，但不等于提供租户级队列公平或不会造成业务中断。

v1.36 产生的 <code>scheduling.k8s.io/v1alpha2</code> 存量对象是 v1.37 升级重点。升级前应导出并删除不再 served 的 v1alpha2 Workload/PodGroup，再用 v1beta1 schema 重建；不要依靠通用 storage migration 掩盖 API 版本已被移除的对象问题。

### 4.3 DRA 组合：从扩展资源到 Workload 共享 claim

DRA 核心在 v1.34 已 GA，v1.37 的变化是把老的 extended-resource 请求、设备状态、设备维护和跨 driver 拓扑组合做得更完整。

#### Stable 能力

| 能力 | v1.37 语义 | 实际落地注意 |
| --- | --- | --- |
| DRA Extended Resource | DeviceClass 可以绑定 <code>example.com/gpu</code> 这类传统 extended resource，Pod 无需显式 ResourceClaim 也能由 DRA driver 完成设备匹配 | 旧 workload YAML 可保持不变，但 driver、DeviceClass 和节点 ResourceSlice 必须先验证 |
| ResourceClaim <code>.status.devices</code> | driver 可以报告每个已分配设备的状态，网络设备还可以暴露 interface、MAC、IP 等信息 | controller 要区分 allocation status、device status 和 Pod condition，不能只看 claim 是否 Bound |
| DRA device taints/tolerations | driver 或 <code>DeviceTaintRule</code> 可以把设备标为维护、退化或不可分配；claim 可以声明容忍 | 既有 Pod 是否被驱逐取决于 taint/toleration 和 driver/controller 策略，需要演练维护窗口 |
| <code>resource.kubernetes.io/numaNode</code> | 统一跨 driver 的 NUMA node device attribute | 只是统一命名/注册，不自动保证 scheduler 已做完整 NUMA placement |
| DRA resource health | kubelet/DRA health API 和 Pod/Container status 可以传达设备健康 | 驱动侧接口和 helper 版本要与 kubelet 版本一起升级 |

<code>DRAExtendedResource</code>、<code>DRAResourceClaimDeviceStatus</code> 以及设备 taint 相关 gate 在 v1.37 已到 Stable/default-on 路径；部分 gate 的 LockToDefault 时间不同，升级时仍应阅读最终 feature-gate 表。

#### Beta：Workload 级 ResourceClaim

<code>DRAWorkloadResourceClaims</code> 在 v1.37 进入 Beta，但默认关闭，并依赖 <code>DynamicResourceAllocation</code> 和 <code>GenericWorkload</code>。开启后，Workload/PodGroup 可以关联 ResourceClaim 或 ResourceClaimTemplate，使一个 claim 在一组 Pod 间共享或由 PodGroup 自动创建，而不是为每个 Pod 单独保留一份 claim。

这解决了大规模 workload 的 per-Pod reservation 上限和重复 claim 问题，但带来新的生命周期合同：

- claim owner 是 Pod、PodGroup 还是 Workload；
- PodGroup 扩缩时 claim 的 reservedFor 如何变化；
- controller 重试和删除时谁负责清理 template-created claim；
- scheduler、kubelet、driver 对共享和 consumer 数量是否支持；
- 失败时是整组重试、部分回滚还是由 controller 进入 suspended。

#### Alpha：更细的设备配对和资源可见性

v1.37 DRA Blog 还列出一组 Alpha/Alpha 2 能力：

| 能力 | Feature gate | 价值 | 不能承诺的部分 |
| --- | --- | --- | --- |
| List type attributes | <code>DRAListTypeAttributes</code> | 一个属性可以持有多个值，表达跨 PCIe root 或重叠拓扑 | driver、selector、distinct semantics 仍可能变化 |
| Node allocatable resource requests | <code>DRANodeAllocatableResources</code> | 把 DRA 管理的 CPU、memory、hugepages 与普通节点资源统一计量，避免重复计算 | 仍需 scheduler、kubelet、Node Declared Features、driver 协同 |
| Resource availability visibility | <code>DRAResourcePoolStatus</code> | 用 <code>ResourcePoolStatusRequest</code> 获取时间点快照 | 不是连续监控 API；刷新要删除并重建 request |
| Optional Node Operations | <code>DRAOptionalNodeOperations</code> | 不需要本地准备/清理的 allocation 可以跳过 kubelet prepare/unprepare | driver 必须明确声明真的没有 node-local side effect |
| Derived Attributes | <code>DRADerivedAttributes</code> | 用 CEL 从设备属性派生虚拟属性，跨 vendor 配对 GPU/NIC/NUMA | CEL 规则、错误和性能都要纳入 driver 测试 |
| Device Compatibility Groups | <code>DRADeviceCompatibilityGroups</code> | 让 scheduler 在分配前识别 MIG/vGPU 等不可共存 partition | 默认关闭；不兼容的 driver 不能仅靠此 gate 自愈 |
| PreQueueingHint | <code>SchedulerPreQueueingHints</code> | DRA ResourceClaim 事件只重新评估受影响 Pod，减少全量扫描 | v1.37 final source 中为 Alpha、默认关闭，不能按早期 release note 的 Beta 预告配置 |

<code>DRAFractionalCapacityRange</code> 在 v1.37 进入 Beta，用于 CapacityRequestPolicyRange 的 fractional/milli-unit 值；它和 consumable capacity 的整数溢出、负数、精度及 allocator 回溯都需要定向测试。

### 4.4 Pod-level Resource Managers：NUMA 对齐的对象从 container 变成 Pod

Pod-level resource requests 在 v1.34 已进入 Beta；v1.36 引入 <code>PodLevelResourceManagers</code> Alpha，v1.37 升为 Beta，但最终 gate 默认关闭。开启后，Topology Manager、CPU Manager 和 Memory Manager 可以在 Pod 总资源预算上做对齐，同时仍为特定 container 划分独占资源。

它解决的是现代 AI Pod 的常见矛盾：主 worker 需要独占、NUMA-aligned 的 CPU/memory，sidecar、日志 agent、监控 exporter 又不值得各自拿一组整数 CPU。Pod 级资源管理可以先为整个 Pod 预留一个 NUMA-aligned pool，再给主容器独占部分，剩余给 sidecar 共享。

生产试验必须固定：

- <code>PodLevelResources</code> 与 <code>PodLevelResourceManagers</code> 的 gate 和 API schema；
- Topology Manager scope、CPU Manager policy、Memory Manager policy；
- sidecar 是否会进入共享池、是否被 in-place resize 影响；
- QoS class、OOM score、<code>memory.min</code>/<code>memory.low</code> 和 cgroup 层级；
- DRA node allocatable resource 与 Pod-level resource 是否重复计账。

不能因为 release Blog 的 use case 是 AI/ML 就直接在所有 GPU 节点打开。先对单节点、单 NUMA、混合 sidecar、in-place resize 和节点重启做 e2e。

### 4.5 Memory QoS 与 cgroups v2

Memory QoS 在 v1.37 进入 Beta，<code>MemoryQoS</code> 默认开启，但只对 Linux cgroups v2 有意义。它使用 <code>memory.min</code>、<code>memory.low</code> 和 <code>memory.high</code> 为请求、QoS class 和阈值提供不同层次的保护。

v1.36 将 reservation 与 throttling 分开：

- <code>memoryReservationPolicy: None</code> 是默认，不写 <code>memory.min</code>/<code>memory.low</code>；
- <code>TieredReservation</code> 才会按 Guaranteed、Burstable、BestEffort 写入不同强度的保护；
- v1.37 的 <code>memoryThrottlingFactor</code> 默认是 <code>nil</code>，因此 <code>memory.high</code> 不会仅因升级就被意外设置；需要显式配置才开启 throttling threshold；
- memory QoS、in-place resize、DRA node allocatable 和 Pod-level managers 会共同作用到 cgroup，必须观测实际文件和 OOM 行为。

迁移检查：

    stat -fc %T /sys/fs/cgroup
    mount | grep cgroup
    kubectl get --raw /api/v1/nodes

cgroups v1 仍有兼容路径，但上游已把它放在维护/退场方向。不能用 cgroup v1 的历史行为推断 Memory QoS、Pod-level resource manager 或新 DRA accounting 的效果。

### 4.6 cAdvisor-less、CRI-full stats

<code>PodAndContainerStatsFromCRI</code> 在 v1.37 是 Beta、默认关闭。目标是让 kubelet 直接从 CRI 获取 Kubernetes 所需的 Pod/container stats，减少 cAdvisor 与 CRI 两套来源之间的歧义和重复采集。

它要求：

- CRI runtime 实现所需的统计接口和字段；
- kubelet、runtime、metrics-server/监控 pipeline 一起测试；
- 对 filesystem、network、CPU、memory、restart 和 container lifecycle 的历史指标做差异基线；
- gate 关闭时保留旧路径，不能把“Beta”当作所有 runtime 都已经 CRI-full。

对于依赖 <code>kubectl top</code> 或 HPA 的集群，应该把 Metrics API <code>v1</code> 的 API 版本迁移和底层 stats source 迁移拆成两个变更，避免同时发生时无法定位指标变化。

### 4.7 其他与调度/资源相关的 v1.37 变化

- <code>PodGroupPreemptionPolicy</code> 是默认关闭的 Alpha，用于表达 PodGroup 级 preemption policy；不要把它和已经进入 Beta 的 workload-aware preemption 混成一个成熟度。
- <code>TopologyAwareWorkloadScheduling</code> 仍是默认关闭的 Alpha，支持在多个 placement 中选择更合适的拓扑布局；它依赖 <code>GenericWorkload</code>。
- <code>CompositePodGroup</code> 是默认关闭的 Alpha，用层级 group 表达多级 gang、拓扑和抢占；它依赖 <code>GenericWorkload</code> 与拓扑调度。
- Job controller 的 <code>WorkloadWithJob</code> 仍是 Alpha/default-off 方向；显式 <code>spec.scheduling</code> 允许 Job 选择 Basic/Gang 等策略，但 controller integration 不等于所有 Job 自动拥有 gang 语义。
- <code>InPlacePodVerticalScalingSchedulerPreemption</code> 是 Alpha，解决 in-place resize 因节点容量不足而 Deferred 后由 scheduler 触发抢占的问题；必须单独验证 disruption。

---

## 第五章：安全、身份和隔离

### 5.1 User Namespaces GA：Pod 内的 root 不再等于主机 root

v1.36 将 Pod User Namespaces 提升到 GA。Pod 设置：

    apiVersion: v1
    kind: Pod
    metadata:
      name: isolated-workload
    spec:
      hostUsers: false
      containers:
      - name: app
        image: example/app:stable
        securityContext:
          runAsUser: 0

<code>hostUsers: false</code> 让 Pod 内的 UID/GID 和 capabilities 处于 Linux user namespace 中。容器内的 UID 0 可以管理 namespace 内资源，但不再直接等同于主机 UID 0；ID-mapped mount 还可以避免为大卷递归 <code>chown</code>。

它是 Linux-only 的隔离层，不是万能 sandbox：

- 内核漏洞、错误的 hostPath、设备直通、特权配置和错误的 runtime 仍可能扩大风险；
- CSI/CNI、存储所有权、host network、host PID、GPU/RDMA、调试和监控 agent 都要单独验证；
- <code>hostUsers: false</code> 是 Pod 级 user namespace，不代表 kubelet、CRI、CNI 已经 rootless；
- 结合 seccomp、Pod Security、RBAC、NetworkPolicy 和节点隔离使用，不能单靠 user namespace 处理不可信代码。

### 5.2 KubeletInUserNamespace：节点组件 rootless Beta

v1.37 将 <code>KubeletInUserNamespace</code> 提升到 Beta，并默认开启 feature gate。它与 Pod User Namespaces 是两个不同的功能：

| 能力 | 对象 | 作用 |
| --- | --- | --- |
| User Namespaces / <code>hostUsers: false</code> | Pod workload | 把容器进程放进 user namespace，节点组件通常仍是 root |
| <code>KubeletInUserNamespace</code> | kubelet、CRI/OCI runtime、CNI、kube-proxy | 让这些节点组件在预先建立的 Linux user namespace 中以非 root 主机用户运行 |

rootless mode 的 user namespace 必须在 Kubernetes 外部准备，所有相关节点组件还要位于相容的 namespace/runtime 环境。feature gate 本身主要让 kubelet 忽略在 user namespace 中无法设置部分 sysctl、读取 <code>/dev/kmsg</code> 等 root-only 操作；开启 gate 不会自动把一个 rootful 节点变成 rootless。

v1.37 还在 Node system info 中报告 <code>runningInUserNamespace</code>，管理员可以据此设置 label/taint，避免把需要真实 host root 的 CNI installer、CSI driver、GPU/RDMA 初始化器调度到 rootless 节点。

兼容性清单：

- Linux kernel、ID-mapped mount、cgroup namespace 和 writable cgroup；
- rootless Docker/containerd/Podman/nerdctl 与 OCI runtime；
- CNI 是否需要修改 host link、iptables/nftables、sysctl 或加载内核模块；
- CSI 是否需要 host mount、device node、udev 或特权 helper；
- NVIDIA device plugin、MIG、RDMA、InfiniBand、VFIO、GPU Operator/HAMi；
- kube-proxy、NodeLocal DNS、监控 agent 和 debug/exec 路径；
- 容器内 UID/GID、volume ownership 和日志/审计采集。

因此 Rootless mode 更适合隔离开发集群、共享机器、嵌套 Kubernetes 和高风险 agent 试验；生产推广要以节点池分区、污点、驱动兼容矩阵和可回滚镜像为前提。

证据：[KubeletInUserNamespace Blog](https://kubernetes.io/blog/2026/09/04/kubernetes-v1-37-rootless-beta/)、[KEP-2033](https://kep.k8s.io/2033)、[Pod User Namespaces 文档](https://kubernetes.io/docs/concepts/workloads/pods/user-namespaces/)。

### 5.3 Pod Certificates 与 ClusterTrustBundles：从 bearer JWT 到可轮换 X.509

Pod Certificates 和 <code>ClusterTrustBundles</code> 在 v1.37 进入 Stable。它们为 Pod 提供一套可轮换的 X.509/mTLS 投影机制：

1. Pod spec 声明 <code>podCertificate</code> projected volume 和 signer name；
2. kubelet 为 Pod 生成私钥并创建 <code>PodCertificateRequest</code>；
3. signer controller 根据自己的授权策略签发 certificate chain，并设置 refresh 时间；
4. kubelet 把私钥和证书 bundle 写入 Pod 文件系统；
5. Pod 可通过 <code>clusterTrustBundle</code> projected volume 取得匹配的 trust anchors；
6. signer/controller 与 kubelet 负责刷新，应用必须通过 inotify 或 polling 重新加载。

GA 的是 Kubernetes 这套 request、projection、rotation 和 trust bundle 机械结构，不等于集群自动拥有一个适合所有用途的 CA/signer。生产还要定义：

- signer name 的租户边界、subject/SAN 和用途；
- signer controller 的 RBAC、审批、审计和高可用；
- 私钥生成位置、文件权限和应用 reload 行为；
- 证书最大生命周期、刷新窗口和 signer 故障时的服务行为；
- 与 SPIFFE、service account token、Gateway TLS、外部 CA 的互操作。

证书轮换对长生命周期的 AI agent、模型 gateway、内部工具 API 和跨 namespace 服务特别重要，但应用如果只在启动时读一次证书，GA API 也不能替它完成热更新。

证据：[Pod Certificates and Cluster Trust Bundles Blog](https://kubernetes.io/blog/2026/08/28/kubernetes-v1-37-pod-certificates-and-cluster-trust-bundles/)、[KEP-4317](https://kep.k8s.io/4317)、[KEP-3257](https://kep.k8s.io/3257)。

### 5.4 Fine-Grained Kubelet API Authorization：不要再广泛授予 <code>nodes/proxy</code>

Fine-grained kubelet API authorization 在 v1.36 GA，<code>KubeletFineGrainedAuthz</code> 已锁定为开启。它允许监控、日志和健康检查只申请对应 kubelet 子资源，而不是为读 metrics 获得可间接访问 exec 的广泛 <code>nodes/proxy</code>。

常见映射包括：

| kubelet endpoint | RBAC resource/subresource |
| --- | --- |
| <code>/stats/*</code> | <code>nodes/stats</code> |
| <code>/metrics/*</code> | <code>nodes/metrics</code> |
| <code>/logs/*</code> | <code>nodes/log</code> |
| <code>/pods</code>、<code>/runningPods/</code> | <code>nodes/pods</code>，兼容 fallback 为 <code>nodes/proxy</code> |
| <code>/healthz</code> | <code>nodes/healthz</code>，兼容 fallback 为 <code>nodes/proxy</code> |
| <code>/configz</code> | <code>nodes/configz</code>，兼容 fallback 为 <code>nodes/proxy</code> |
| <code>/spec/*</code> | <code>nodes/spec</code> |
| <code>/checkpoint/*</code> | <code>nodes/checkpoint</code> |
| 其他未细分路径 | <code>nodes/proxy</code> |

新授权检查失败时，部分 endpoint 仍会回退到 <code>nodes/proxy</code> 以保持旧 workload 兼容。因此升级后不能只看请求“仍然成功”，要审计旧 ClusterRole，把监控 agent、日志 collector 和 metrics scraper 迁移到最小权限，确认它们没有不必要的 <code>pods/exec</code>、<code>pods/portforward</code> 或 kubelet proxy 能力。

### 5.5 不可解密资源的 API 处置

v1.37 为无法被 API server 解密的资源提供 Beta 处置路径。过去 encryption key 丢失或配置错误时，资源可能仍留在 etcd 中，但 API server 无法正常读取、更新或删除，管理员被迫直接修改 etcd 文件。

新路径允许管理员通过 Kubernetes API 识别并删除确认不可解密的资源，并提供核验保护。它不是解密工具，也不恢复丢失的密钥。生产流程应是：

1. 先恢复/确认 encryption provider、key material、配置和权限；
2. 列出受影响的 resource type、namespace、name 和审计证据；
3. 通过隔离身份和人工审批确认确实不可恢复；
4. 备份可用元数据，记录删除原因；
5. 删除后观察 controller、ownerReference、quota 和业务数据的一致性。

此能力面向灾难恢复，不应被普通 operator 自动调用。它与 manifest-based admission 一样，把“恢复路径不依赖正常 API 读写”作为安全设计的一部分。

### 5.6 Admission Policy 与生产调试的安全边界

ValidatingAdmissionPolicy、webhook、RBAC、Pod Security 和审计日志分别负责不同层：

- Admission 决定对象能否进入 API；
- RBAC 决定主体可以对哪些资源执行哪些 verb；
- Pod Security 限制 workload 的安全上下文；
- NetworkPolicy 控制网络路径；
- 审计记录谁在什么时间做了什么；
- 生产 debug 的临时权限还需要过期时间、审批、命令限制和 session 记录。

官方生产调试建议的 JIT access broker 可以放在 Kubernetes RBAC 之上，给 on-call 工程师短时、身份绑定的 <code>pods/log</code>、<code>pods/exec</code>、<code>pods/portforward</code> 权限。RBAC 能限制“是否能 exec”，但不能限制 exec session 内实际执行的 shell 命令；不要把一个长期 <code>cluster-admin</code> token 或共享 bastion 当作调试方案。

对 AI agent 尤其要保持边界：Admission Policy 可以阻止危险 Pod，User Namespace 可以降低部分 host root 风险，Agent Sandbox 可以提供另一个工作负载抽象，但三者都不能替代 egress 控制、工具授权、短期凭据、命令审计和隔离执行环境。

---

## 第六章：存储、网络和工作负载生命周期

### 6.1 Volume Group Snapshots：CSI 侧的崩溃一致性恢复点

v1.36 将 Volume Group Snapshots 提升到 GA。它依赖 CSI group snapshot extension APIs，用 label selector 把多个 PVC 组织成组，在同一时间点创建 crash-consistent snapshots，并支持用这组 snapshots 恢复新卷或恢复现有卷。

它只适用于支持相应 CSI group snapshot RPC/API 的 driver。Kubernetes API 达到 GA 不表示所有云盘、分布式文件系统或本地存储都实现同样的 crash-consistency。生产验证：

- driver 是否实现 group snapshot controller/node 能力；
- 多 PVC 是否属于同一应用恢复边界；
- snapshot class、保留策略和跨 namespace 访问；
- restore 后数据一致性、应用日志 replay 和 checkpoint；
- snapshot 创建期间 I/O、Pod disruption 和容量成本。

对分布式训练和大模型服务，volume group snapshot 可以给 checkpoint、tokenizer/cache 和元数据提供一致恢复点，但不等于 GPU memory、KV cache 或外部对象存储事务也被快照。

证据：[v1.36 Volume Group Snapshots Blog](https://kubernetes.io/blog/2026/05/08/kubernetes-v1-36-volume-group-snapshot-ga)、[CSI Snapshotter 文档](https://kubernetes-csi.github.io/docs/snapshot-controller.html)。

### 6.2 SELinux 高效 volume relabel：快，但可能暴露共享标签冲突

SELinux mount/relabel 路径在 v1.37 进入 Stable/default-on 路径，但广泛 mount 行为需要 CSI driver opt-in。满足条件时，kubelet 通过 <code>-o context=&lt;label&gt;</code> 在 mount 级别应用标签，避免对 volume 中每个 inode 递归 relabel。

改变行为的核心字段和条件：

- CSI driver 的 <code>CSIDriver.spec.seLinuxMount: true</code>；
- Pod/PodTemplate 的 <code>spec.securityContext.seLinuxChangePolicy</code>；
- Pod 或 container 提供足够的 SELinux level；
- Linux kernel、runtime、volume plugin 支持 mount context；
- SELinux 确实处于启用/enforcing 相关路径。

风险是一个 mount 只能承载一个 SELinux context。过去依赖递归 relabel、让不同 SELinux label 的 Pod 共享同一 volume 的 workload 可能在升级后无法启动。若业务必须保留旧模型，可对特定 Pod 设置：

    spec:
      securityContext:
        seLinuxChangePolicy: Recursive

没有 SELinux 的节点不受影响；有 SELinux 的集群必须对共享 PVC、ReadWriteOncePod、不同 namespace、privileged/unprivileged Pod 和滚动更新做实测。性能收益应与安全标签语义一起验收，不能只看 mount 时间。

证据：[SELinux Volume Label Changes](https://kubernetes.io/blog/2026/04/22/breaking-changes-in-selinux-volume-labeling)、[KEP-1710](https://kep.k8s.io/1710)。

### 6.3 StatefulSet <code>Recreate</code> Alpha 与 <code>maxUnavailable</code> 恢复

v1.37 新增 <code>StatefulSetRecreateStrategy</code> Alpha。StatefulSet 过去主要是 <code>RollingUpdate</code> 和 <code>OnDelete</code>；Recreate 会先删除该 StatefulSet 的所有 Pod，再创建使用新 template 的 Pod。

它适合需要整组停机、避免新旧版本同时运行或状态协议不支持滚动切换的 workload，但会产生明确 downtime。PVC 通常保留，Pod identity 会按 ordinal 重建；应用要处理 leader、fencing、连接重建和数据恢复。

同时，<code>maxUnavailable</code> 行为在 v1.37 默认重新启用。v1.36 曾出现 faulty initial revision 卡住、纠正后的 revision 无法推进、Pod 长期 <code>CrashLoopBackOff</code> 的问题；升级后应重新验证：

- <code>MaxUnavailableStatefulSet</code> gate 和 controller 行为；
- <code>maxUnavailable</code> 与 partition、readiness、PDB 的组合；
- 首个 revision 不 ready 后修复 template 的恢复；
- Recreate 与 PVC、headless Service、应用 leader election 的交互。

<code>Recreate</code> 的 feature gate、<code>maxUnavailable</code> 的默认行为和应用数据恢复必须写入回滚手册。Alpha API 不应成为所有 StatefulSet 的默认 strategy。

### 6.4 Gateway API v1.5/v1.6：标准网络 API 的边界继续扩大

Gateway API 是独立于 Kubernetes Core release 的 SIG Network 项目。Kubernetes Blog 中的 v1.5/v1.6 文章说明了标准 channel 的演进，但实际可用性仍取决于 Gateway controller 的版本和 conformance。

#### v1.5：六项进入 Standard

Gateway API v1.5（项目于 2026-02-27 发布，Blog 于 2026-04-21 介绍）把这些能力推进 Standard：

- ListenerSet；
- TLSRoute；
- HTTPRoute CORS Filter；
- Client Certificate Validation；
- Certificate Selection for Gateway TLS Origination；
- ReferenceGrant。

同时项目采用 release train，feature freeze 时只交付已经准备好实现和文档的能力。生产升级要把 CRD bundle、controller、conformance 和回滚顺序固定在同一 release。

#### v1.6：TCPRoute/UDPRoute 标准化

Gateway API v1.6.0 于 2026-06-30 发布，Blog 于 2026-08-03 发布。核心变化是：

- TCPRoute 和 UDPRoute 从 Experimental 进入 Standard；
- API version 使用 <code>gateway.networking.k8s.io/v1</code>；
- 原 <code>v1alpha2</code> 版本进入 deprecated，未来会移除；
- 实验资源迁移到 <code>gateway.networking.x-k8s.io</code>，通过 <code>X</code> 前缀把实验边界显式化；
- <code>XBackend</code> 为 ExternalHostname/egress 等扩展提供实验性方向，但不是生产 Standard API。

TCP/UDP 业务的最小形态是 Gateway listener 声明 <code>protocol: TCP/UDP</code> 和 <code>allowedRoutes</code>，Route 再通过 <code>parentRefs</code>、<code>sectionName</code>、<code>backendRefs</code> 指向 Service。Raw L4 路由不会理解 L7 HTTP 语义，数据库、DNS、VoIP、游戏和 IoT 等场景仍要验证 load balancer、health check、proxy protocol、TLS passthrough 和 connection draining。

### 6.5 Ingress-NGINX retirement 与 Ingress2Gateway

官方 Blog 已宣布 Ingress-NGINX 在 2026 年 3 月退休，并连续发布行为迁移提醒。要区分：

- Ingress-NGINX 是 Kubernetes 社区维护的 controller；
- NGINX Ingress 是 F5 的另一个产品，两者不是同一个项目；
- Kubernetes Core 的 <code>networking.k8s.io/v1 Ingress</code> API 不会因为一个 controller retirement 自动被删除；
- Ingress annotations、ConfigMap、regex、rewrite、CORS、timeout、backend TLS 等 implementation-specific 行为不能靠 API 类型一对一翻译。

Ingress2Gateway 1.0 是迁移助手，不是无审查的一键替换。它可以识别并转换大量常见 Ingress-NGINX annotation，输出 Gateway API manifest，并对无法转换的配置发出 warning；官方还为支持的 annotation 组合做 controller-level integration test。

安全迁移流程：

1. 盘点 Ingress class、annotation、ConfigMap、CRD、TLS、rewrite、regex 和 session 行为；
2. 用 <code>ingress2gateway print</code> 生成候选 Gateway/HTTPRoute；
3. 逐条阅读 warning，处理没有等价 Gateway API 字段的配置；
4. 在双 controller、影子流量和真实长连接/streaming 场景测试；
5. 对响应码、重试、header、timeout、WebSocket、HTTP/2、TLS 和源 IP 做行为对比；
6. 最后再切换 DNS/load balancer 和删除旧 controller。

证据：[Ingress2Gateway 1.0](https://kubernetes.io/blog/2026/03/20/ingress2gateway-1-0-release)、[Ingress-NGINX 迁移行为](https://kubernetes.io/blog/2026/02/27/ingress-nginx-before-you-migrate/)、[Gateway API 官网](https://gateway-api.sigs.k8s.io/)。

### 6.6 kube-proxy nftables：规则管理性能和本地 NodePort

v1.37 对 nftables backend 有两类变化：

- kube-proxy 默认使用 kernel netlink 操作和读取 nftables rule，减少调用/解析 <code>nft</code> 命令的开销；<code>NFTablesNetlink</code> 是 Beta/default-on 路径；
- <code>KubeProxyNFTablesLocalhostNodePorts</code> 是 Alpha，可在 <code>--nodeport-addresses</code> 包含 <code>localhost</code> 或 loopback 时，通过 userspace proxy 让 localhost IPv4/IPv6 NodePort 可访问。

这不会改变 iptables/ipvs backend 的既有行为。迁移时要测量大量 Service、规则同步时间、长 Service name、NodePort 本地访问、hostNetwork Pod 和发行版 nftables 版本，不要把 nftables rule programming 变快误解成业务流量一定变快。

v1.37 还开始弃用 kube-proxy 的 ipvs mode，后续版本计划关闭默认并最终移除。现有 ipvs 集群应记录 mode、iptables 依赖、CNI 和 cloud load balancer 行为，为 nftables 或其他受支持路径做迁移验证。

---

## 第七章：AI、Agent 和云原生平台生态

### 7.1 Agent Sandbox：面向长生命周期 agent singleton 的生态 API

[Running Agents on Kubernetes with Agent Sandbox](https://kubernetes.io/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/) 描述了 SIG Apps 旗下仍在快速开发的 <code>kubernetes-sigs/agent-sandbox</code> 项目。它针对的是和普通 stateless Deployment 不完全相同的对象：

- 一个 agent 通常是 singleton、stateful、长时间存在但大部分时间 idle；
- 它需要稳定的网络身份、持久 workspace、可暂停/恢复的生命周期；
- 它可能执行不可信代码，且会被 LLM 长时间调用外部工具；
- Pod 启动冷延迟可能影响交互体验，因此项目还讨论 <code>SandboxTemplate</code>、<code>SandboxClaim</code> 和 warm pool。

这类 CRD 可以改善 controller、identity、workspace、suspend/resume 和 pre-warm 的表达，但要记住：

1. Agent Sandbox 是生态项目，不是 Kubernetes v1.37 Core API，也没有由 Kubernetes 自动提供 microVM；
2. <code>Sandbox</code> 的工作负载隔离等级取决于 Pod security、runtime、User Namespace、节点池或外部 sandbox；
3. stable identity 不等于 stable certificate、网络策略、工具权限或数据保留；
4. warm pool 解决冷启动，不解决多租户配额、secret 注入、逃逸风险和成本计量；
5. 要把 agent 的工作目录、执行权限、egress、审计和回收分开建模。

本仓库的 [E2B AI Sandbox 深度文档](E2B-Deep-Dive.html) 讨论 Firecracker microVM 和自托管；[Multica 深度文档](Multica-Deep-Dive.html) 讨论本地 coding agent 编排。Agent Sandbox Blog 的 CRD 不应被解读成这两套系统的替代或内建隔离证明。

### 7.2 AI Gateway Working Group：标准化 AI 流量基础设施，而不是发布一个产品

[AI Gateway Working Group](https://kubernetes.io/blog/2026/03/09/announcing-ai-gateway-wg/) 的目标是在 Gateway API 基础上讨论 AI traffic 的标准和最佳实践。文章提出的需求包括：

- token-based rate limiting；
- inference API 的细粒度访问控制；
- 对完整 request/response payload 做 inspection、transform、guardrail；
- 依据语义做 routing、cache 和 RAG context enhancement；
- 可靠地把请求 egress 到 OpenAI、Vertex AI、Bedrock 等外部服务；
- token injection、区域合规、跨集群路由和 failover。

截至本文审校日，这些仍是 Working Group charter、proposal 和各 gateway 项目的实现方向。不能因为 Blog 使用 “AI Gateway” 这个名字，就为 Kubernetes API server、Gateway API <code>v1</code> 或某个 controller 添加一个不存在的 Core kind。生产采用时应把：

    Gateway API Standard
        ├─ HTTPRoute/TCPRoute/UDPRoute stable routing
        ├─ controller-specific policy/extensions
        ├─ AI inference extension / endpoint selection
        └─ organization-specific auth, quota, payload and egress policy

分开记录版本、conformance、权限和回滚。

### 7.3 Gateway API Inference Extension：模型感知路由的上下文

[Gateway API Inference Extension](https://kubernetes.io/blog/2025/06/05/introducing-gateway-api-inference-extension/) 是 RSS 历史文章中仍影响 2026 AI 平台讨论的重要上下文。它在 Gateway API 的 Gateways/HTTPRoutes 模型之上定义了 inference-specific CRD 和 Endpoint Selection Extension：

- <code>InferencePool</code> 面向平台管理员，描述一组 model server Pod 及其负载/扩缩/均衡；
- <code>InferenceModel</code> 面向模型 owner，把公开模型名映射到 pool 内的模型、adapter 或优先级；
- endpoint selection 可以根据 queue length、memory、loaded adapter 等实时信息选择具体 Pod；
- roadmap 讨论 prefix-cache aware routing、LoRA rollout、criticality/fairness、HPA aggregate metrics、异构 accelerator 和 disaggregated serving。

这些对象是 Gateway API ecosystem extension，不是 <code>gateway.networking.k8s.io/v1</code> 的稳定 Core resource。KServe、llm-d、Envoy Gateway、独立 EPP 或自研 controller 的支持矩阵必须独立审计。它适合解释为什么 LLM 请求不能只用 round-robin，但不提供一个可跨 controller 无条件迁移的 API 合同。

### 7.4 AI 平台插件生态：Headlamp、Kubeflow、Volcano、Knative

2026 RSS 的 Headlamp 文章体现了另一类平台演进：不是增加底层 scheduler，而是把 CRD 的“操作真相”呈现给不同角色。

| 项目/插件 | 展示对象 | 价值 | 边界 |
| --- | --- | --- | --- |
| Headlamp Kubeflow | Notebook、Pipeline/Run、Katib、TrainJob、TrainingRuntime | 从 ML 用户视图回到 Pod、PVC、事件和失败原因 | 不改变 Kubeflow controller、Kueue 或 scheduler |
| Headlamp Volcano | Volcano Job、PodGroup、Queue、Pod 状态 | 快速查看批任务、队列和调度上下文 | 不替代 Volcano scheduler 或 queue quota |
| Headlamp Knative | Service、Revision、Route、autoscaling 状态 | 操作 serverless 服务及其 Kubernetes 底层对象 | 不使 HPA scale-to-zero 或 KEDA 语义自动一致 |
| Headlamp/Cluster API | CAPI cluster、machine、control plane | 统一集群生命周期观测 | 不替代 CAPI controller 的升级策略 |

对于多租户 AI 平台，UI 的最小权限、namespace scope、审计和 secret 脱敏与底层 API 一样重要。一个能够看到 GPU claim 或 Pod log 的 UI 不应默认拥有修改 Workload、Queue、Gateway 或 signer 的权限。

### 7.5 Kubernetes 对 AI 工作负载的抽象上移

把 v1.36/v1.37 Blog 串起来，可以看到一个清晰方向：

    Pod
     ├─ requests/limits, affinity, PVC
     └─ device plugin / simple scheduler
           ↓
    Workload + PodGroup
     ├─ Gang Scheduling
     ├─ workload-aware preemption
     ├─ DRA shared claims
     └─ topology placement
           ↓
    Platform
     ├─ queue/quota/fairness (Kueue/Volcano/Koordinator 等)
     ├─ inference gateway / external metrics
     ├─ identity/certificates
     ├─ sandbox/runtime isolation
     └─ UI, audit, cost and SLO

上游 Kubernetes 正在把 workload、设备和节点资源的表示能力补齐；队列、公平、模型路由、microVM、GPU virtualisation 和组织成本治理仍由生态项目组合完成。平台选型应从接口和状态机出发，而不是从某个 Blog 标题推断“上游已经替我们实现完整 AI 平台”。

---

## 第八章：KYAML、可观测性与开发者体验

### 8.1 KYAML Stable：更严格的 YAML 方言，不是新配置语言

KYAML 在 v1.37 进入 Stable。它是 YAML 的严格子集，所有 KYAML 文件仍是有效 YAML，现有 <code>kubectl</code>、Helm、Kustomize 和 YAML parser 不需要改成另一套 parser。它主要减少：

- 不必要的 YAML 类型推断；
- 模板缩进造成的结构误读；
- 同一 API manifest 的多种写法；
- review、lint 和生成工具之间的不确定性。

<code>kubectl get -o kyaml</code> 可以输出更一致的 manifest。它不会改变 API server 的 schema、defaulting、admission 或 server-side apply ownership；把现有 YAML 格式化为 KYAML 也不会自动发现业务语义错误。落地时在 Git review、生成器和 policy checker 中统一风格即可，不必把所有输入 pipeline 一次性重写。

证据：[KYAML Blog](https://kubernetes.io/blog/2026/08/11/how-to-pretty-print-kubernetes-yaml-as-kyaml)、[KEP-5295](https://kep.k8s.io/5295)。

### 8.2 <code>metrics.k8s.io/v1</code> Stable：API 版本稳定不等于监控系统升级完成

<code>metrics.k8s.io</code> API 在 v1.37 从 Beta 进入 Stable：

- <code>NodeMetrics</code> 提供节点 CPU/memory usage；
- <code>PodMetrics</code> 提供 Pod 和 per-container usage；
- <code>v1</code> 的资源类型、字段和数值含义与 <code>v1beta1</code> 相同；
- <code>kubectl top</code> 和基于 resource metrics 的 HPA 使用这类数据；
- 它不是 Prometheus 全量监控，也不是 <code>custom.metrics.k8s.io</code> 或 <code>external.metrics.k8s.io</code> 的替代。

迁移时先确认 metrics-server/adapter、RBAC、APIService、客户端 discovery 和 HPA controller 的访问路径，再逐步切换 URL：

    kubectl get --raw /apis/metrics.k8s.io/v1/nodes
    kubectl get --raw /apis/metrics.k8s.io/v1/namespaces/default/pods
    kubectl top nodes
    kubectl top pods -A

如果目标是 HPA scale-to-zero，<code>metrics.k8s.io/v1</code> 只解决 CPU/memory 的资源指标稳定访问，仍不能提供零 Pod 时所需的 queue/object/external signal。

### 8.3 Native Histograms：为高基数延迟指标降低采样成本

Kubernetes v1.37 将 <code>NativeHistograms</code> 推进到 Beta，默认开启。Kubernetes metrics 可以同时暴露 classic histogram 和 native histogram 形态，便于在 Prometheus 等支持系统中以更低的 series/cardinality 成本表达延迟分布。

采用时要注意：

- 监控后端、remote write、聚合规则和告警引擎必须支持 native histogram；
- 同一指标在迁移期间可能有 classic/native 两种消费路径，告警不要重复计算；
- 不能只用平均 latency 替代 p95/p99/goodput，尤其是 LLM token streaming；
- exporter、scrape、recording rule 和 dashboard 要做兼容性回归。

### 8.4 Custom Metrics Exporter：HPA 的外部信号供应链

RSS 的 [Building a Custom Metrics Exporter](https://kubernetes.io/blog/2026/07/14/custom-metrics-exporter-kubernetes/) 是实践型文章。它说明一个 exporter/adapter 如何把业务系统指标映射为 Kubernetes custom metrics API，供 HPA 使用。

在 AI 平台中常见的 external metric 是：

- queue depth / consumer lag；
- model request backlog；
- token rate、active sequence、GPU memory pressure；
- per-tenant concurrency；
- warm pool available capacity。

指标链路是：

    queue / gateway / model server
            │
            ▼
    Prometheus or metrics backend
            │
            ▼
    custom/external metrics adapter
            │
            ▼
    HPA controller ──► Deployment replicas

任何一环 discovery、label selector、RBAC、TLS 或 freshness 出错，HPA 都可能停在零、缩容过慢或给出错误容量。exporter Blog 是实现指南，不会把 custom metrics API 提升为 Core Stable，也不会替平台定义指标单位、租户隔离和数据保留。

### 8.5 controller-runtime Cache：低读延迟换来的内存和一致性责任

官方 controller-runtime Cache 文章特别提醒 controller 作者：

- <code>r.Get()</code>/<code>r.List()</code> 通常读本地 informer cache，不是每次直连 API server；
- list/watch cache 降低了控制面请求量，但每种 watched object 都会占用内存；
- selector、namespace、metadata-only cache 和 uncached client 的选择影响内存、网络和一致性；
- cache 可能陈旧，写入后立即从 cache 读取不能当成 read-your-write；
- hidden O(n) scan、错误的 watch 范围和重复 cache 会在规模变大后放大。

自研 AI controller 应明确：

1. 哪些对象需要全量 cache，哪些只需 metadata；
2. 哪些 get 允许 eventual consistency，哪些必须 live GET；
3. predicate、indexer 和 ownerReference 是否足以避免全量扫描；
4. cache warm-up、watch 断线、API 429 和 resync 的 backoff；
5. reconciliation metrics 是否包含 queue wait、cache age、API latency 和 write conflict。

这与 v1.37 的 watch cache/RangeStream 变化相互影响：API server 大列表读更节省内存，不代表一个 controller 可以无限制 watch 全集。

### 8.6 client-go context handling 与 contextual logging

v1.37 release notes 记录 client-go 的 context propagation 和 contextual logging 工作基本完成。对 controller/operator 的价值是把 request ID、namespace/name、cluster/tenant 等上下文带入日志和 downstream call，而不是继续使用全局 logger。

迁移时：

- 每次 API call、webhook、queue worker 和 external metric 查询都传递有界 deadline；
- 不把 secret、token、完整 prompt 或 payload 写入 contextual fields；
- 保持日志 key 稳定，避免把高基数 object UID 无限制放到 metrics label；
- 对认证插件仍可能使用 global klog 的少数调用单独评估。

---

## 第九章：Stable/Beta/Alpha 对照矩阵

下表只列本文覆盖的关键能力；不是 v1.37 67 项 enhancement 的逐条替代清单。默认状态按 v1.37.0 source/官方 Release 文章审校，组件或发行版可以额外限制。

### 9.1 Stable 与可直接纳入基线的能力

| 特性 | 版本 | API/gate | v1.37 默认 | 生产成熟度与场景 | 升级/回滚风险 |
| --- | --- | --- | --- | --- | --- |
| DRA core | v1.34 GA，v1.37 继续 | <code>resource.k8s.io/v1</code> | 开启 | GPU/FPGA/NIC 等结构化设备 | driver 版本、ResourceSlice 和 kubelet plugin 兼容 |
| DRA Extended Resource | v1.37 GA | <code>DRAExtendedResource</code> | 开启/GA | 保持 <code>example.com/gpu</code> 旧请求形态并由 DRA 分配 | DeviceClass 映射错会让旧 Pod 调度到错误设备 |
| DRA ResourceClaim device status | v1.37 GA | <code>DRAResourceClaimDeviceStatus</code> | 开启/锁定方向 | 设备状态、网络接口地址、故障排查 | status writer RBAC、driver helper API |
| DRA device taints/tolerations | v1.37 GA | <code>DRADeviceTaints</code>、<code>DRADeviceTaintRules</code> | 默认开启，部分 gate 尚待锁定 | 单设备维护、降级设备隔离 | 既有 Pod 驱逐和 claim tolerance 必须演练 |
| DRA <code>numaNode</code> | v1.37 GA | <code>resource.kubernetes.io/numaNode</code> | 无独立行为 gate | 跨 driver 比较设备 NUMA | 命名统一不等于 placement 自动完成 |
| <code>metrics.k8s.io/v1</code> | v1.37 GA | API version | 可用 | <code>kubectl top</code>、resource metrics、HPA | v1beta1 过渡、metrics-server/APIService |
| KYAML | v1.37 GA | <code>kubectl get -o kyaml</code> | 可用 | manifest review、生成和格式统一 | 不改变 schema/defaulting，工具仍需回归 |
| Storage Version Migration | v1.37 GA | <code>storagemigration.k8s.io/v1</code>、<code>StorageVersionMigrator</code> | 开启 | CRD/API storage version 和加密重写 | 迁移未完成不能删除 old served/stored version |
| Node Declared Features | v1.37 GA | <code>NodeDeclaredFeatures</code> | 开启/锁定方向 | 节点版本 skew 和能力声明 | gate 配置变化需 kubelet restart |
| resilient watch cache initialization | v1.37 完成 GA | <code>WatchCacheInitializationPostStartHook</code> | 开启/锁定 | 控制面启动/恢复保护 | controller 必须处理 429/Retry-After |
| Declarative Validation | v1.36 GA | <code>DeclarativeValidation</code> | 开启/锁定 | native API validation、生成代码 | 旧对象 update/patch 语义需回归 |
| User Namespaces | v1.36 GA | <code>UserNamespacesSupport</code>、<code>hostUsers: false</code> | GA 路径 | Pod root 隔离、idmapped mounts | Linux、runtime、CNI、CSI、GPU 兼容 |
| Fine-grained kubelet authz | v1.36 GA | <code>KubeletFineGrainedAuthz</code> | 锁定开启 | 替代广泛 <code>nodes/proxy</code> | 旧 RBAC fallback 可能掩盖过权 |
| Volume Group Snapshots | v1.36 GA | CSI group snapshot APIs | 取决于 CSI | 多 PVC crash-consistent checkpoint | driver 能力、容量和恢复一致性 |
| SELinux efficient mount/relabel | v1.37 Stable 路径 | <code>SELinuxMount</code>、<code>SELinuxChangePolicy</code> | 默认路径，driver opt-in | 大卷启动性能、标签隔离 | 同卷不同 label 可能无法共存 |

### 9.2 Beta：可以灰度，但要确认 default-on/default-off

| 特性 | 版本 | API/gate | v1.37 默认 | 适用场景 | 主要限制 |
| --- | --- | --- | --- | --- | --- |
| HPA Scale-to-Zero | v1.37 Beta | <code>HPAScaleToZero</code> | 开启 | queue worker、batch、低频 GPU worker | 需要 object/external metric；冷启动；Service 不缓存请求 |
| etcd RangeStream | v1.37 Beta | <code>EtcdRangeStream</code> | 开启 | 大列表、watch cache init | etcd 3.7+ 才命中流式；旧版本 fallback |
| concurrent watch object decode | v1.37 Beta | <code>ConcurrentWatchObjectDecode</code> | 开启 | CRD conversion 多对象初始化 | conversion webhook 并发压力上升 |
| manifest-based admission | v1.37 Beta | <code>ManifestBasedAdmissionControlConfig</code> | 开启 | bootstrap/self-protect policy | 文件分发、命名后缀和启动失败治理 |
| Generic Workload / Gang | v1.37 Beta | <code>GenericWorkload</code> | 关闭 | Workload/PodGroup、基础 Gang | gate 依赖、API 迁移、scheduler/controller 一致 |
| Workload-aware preemption | v1.37 Beta 路径 | Generic Workload 相关 scheduler path | 关闭 | 按 PodGroup 选择 preemption victims | 不等于 queue fairness 或无中断 |
| DRA Workload ResourceClaims | v1.37 Beta | <code>DRAWorkloadResourceClaims</code> | 关闭 | PodGroup/Workload 共享 ResourceClaim | 依赖 GenericWorkload/DRA，owner 生命周期复杂 |
| Memory QoS | v1.37 Beta | <code>MemoryQoS</code> | 开启 | cgroups v2 memory protection/throttling | v1/v2 差异；<code>memory.high</code> 需显式配置 |
| Pod-level Resource Managers | v1.37 Beta | <code>PodLevelResourceManagers</code> | 关闭 | Pod 总预算下 NUMA/CPU/Memory manager | 依赖 PodLevelResources；sidecar/QoS/cgroup 需实测 |
| CRI-full stats | v1.37 Beta | <code>PodAndContainerStatsFromCRI</code> | 关闭 | cAdvisor-less kubelet stats | runtime 必须支持完整 CRI stats |
| Native Histograms | v1.37 Beta | <code>NativeHistograms</code> | 开启 | latency distribution、降低 series 成本 | 后端、remote write、告警和 dashboard 兼容 |
| DRA fractional capacity | v1.37 Beta | <code>DRAFractionalCapacityRange</code> | 按最终 gate config | fractional consumable device capacity | 精度、溢出、负数和 allocator 回溯 |
| ClusterTrustBundle/Pod Certificate | v1.37 Stable/GA transition | <code>ClusterTrustBundle</code>、<code>PodCertificateRequest</code> | 默认开启/lock timing 独立 | mTLS、trust bundle、Pod identity | signer、rotation、应用 reload 仍外置 |

### 9.3 Alpha、默认关闭或生态项目

| 特性 | 版本/状态 | Gate 或接口 | 生产判断 |
| --- | --- | --- | --- |
| Server-side sharded list/watch | v1.36 Alpha | <code>ShardedListAndWatch</code> | 只在能管理 shard ownership 的 controller 试验 |
| Topology-Aware Workload Scheduling | v1.36/v1.37 Alpha | <code>TopologyAwareWorkloadScheduling</code> | 结合 PodGroup placement 做隔离压测 |
| CompositePodGroup | v1.37 Alpha | <code>CompositePodGroup</code> | 多级 gang/拓扑/抢占设计验证 |
| PodGroupPreemptionPolicy | v1.37 Alpha | <code>PodGroupPreemptionPolicy</code> | 不当作 Beta workload preemption 的默认字段 |
| WorkloadWithJob | v1.36/v1.37 Alpha | <code>WorkloadWithJob</code> | Job controller integration 需单独打开 |
| DRA ListTypeAttributes | v1.37 Alpha 2 | <code>DRAListTypeAttributes</code> | 等 driver/selector 语义稳定 |
| DRA node allocatable | v1.37 Alpha 2 | <code>DRANodeAllocatableResources</code> | CPU/memory/hugepages 计账需全链路验证 |
| DRA resource availability | v1.37 Alpha 2 | <code>DRAResourcePoolStatus</code> | 时间点查询，不是监控数据源 |
| DRA Optional Node Operations | v1.37 Alpha | <code>DRAOptionalNodeOperations</code> | 仅无 node-local side effect 的 driver |
| DRA Derived Attributes | v1.37 Alpha | <code>DRADerivedAttributes</code> | CEL 跨 driver 配对实验 |
| DRA Device Compatibility Groups | v1.37 Alpha | <code>DRADeviceCompatibilityGroups</code> | MIG/vGPU 等不可兼容 partition 预检 |
| Scheduler PreQueueingHint | v1.37 Alpha final | <code>SchedulerPreQueueingHints</code> | 不采用早期 Beta 预告，按 source gate 试验 |
| StatefulSet Recreate | v1.37 Alpha | <code>StatefulSetRecreateStrategy</code> | 会删除全部 Pod，先做停机/恢复演练 |
| localhost nftables NodePort | v1.37 Alpha | <code>KubeProxyNFTablesLocalhostNodePorts</code> | 只给明确依赖 localhost NodePort 的节点池 |
| Pod checkpoint/restore | v1.37 Alpha | CRI <code>CheckpointPod</code>/<code>RestorePod</code> | runtime 必须实现新 RPC，不能作为通用备份 |
| Agent Sandbox | ecosystem | Sandbox/SandboxClaim CRD | 不是 Kubernetes Core sandbox 或 microVM |
| AI Gateway Working Group | proposal/ecosystem | Gateway API extensions | proposal 不等于 stable API |
| Gateway API Inference Extension | ecosystem extension | InferencePool/InferenceModel/EPP | controller/conformance/版本独立审计 |
| Headlamp Kubeflow/Volcano/Knative plugins | ecosystem | UI plugins | 只改变观察和操作入口，不改变调度语义 |

---

## 第十章：AI 平台组合落地

### 10.1 参考架构：GPU worker、外部指标、Workload 和设备 claim

一个以队列为入口、以 GPU worker 为执行单元的参考组合如下：

<div class="mermaid">
flowchart LR
    Client[Client or Agent] --> Gateway[Gateway API Controller]
    Gateway --> Queue[Durable Queue]
    Queue --> Metric[External Metrics Adapter]
    Metric --> HPA[HPA minReplicas 0..N]
    HPA --> Workload[Workload / PodGroup]
    Workload --> Gang[Gang Scheduling]
    Workload --> Claim[DRA ResourceClaim or Template]
    Gang --> Scheduler[kube-scheduler]
    Claim --> Scheduler
    Scheduler --> Node[NUMA aware GPU Node]
    Node --> Runtime[GPU runtime / kubelet / Memory QoS]
    Runtime --> Worker[Inference or Training Worker]
    Worker --> Queue
    Worker --> Gateway
</div>

推荐把配置分成四个层次：

1. **流量层：** Gateway/HTTPRoute 或 inference extension 处理认证、路由、长连接和外部 egress；
2. **弹性层：** HPA 读取 queue lag、active request 或模型 backlog，控制 worker 数量；
3. **调度层：** Workload/PodGroup + Gang 保证 worker 组的最小可运行规模，DRA 描述 GPU/NIC/拓扑；
4. **节点层：** kubelet、device plugin/DRA driver、CPU/Topology/Memory manager、cgroups v2 和 runtime 兑现资源合同。

任何一层的 status 都不能代替另一层的 status。例如 HPA 已把 Deployment 调到 5，不代表 5 个 GPU 已被 DRA 分配；DRA claim Bound 也不代表 Pod 已 ready；Gateway backend 有 endpoints 也不代表模型已加载。

### 10.2 GPU 训练：DRA + Workload/PodGroup + Gang

适用情形：一个训练任务需要 leader、多个 worker、GPU/NIC/本地 NVMe，并且部分启动才有意义。

建议：

- 用 Workload/PodGroup 表示 PodSets、minCount、priority 和 disruption；
- 用 Gang Scheduling 先确保整组可放置，减少只启动半组造成的 deadlock；
- 用 DRA claim 描述 GPU、NIC、partition、health、NUMA 和共享规则；
- 若依赖 Workload claim，共同打开 <code>GenericWorkload</code> 和 <code>DRAWorkloadResourceClaims</code>，并把两个 gate 的对象/控制器版本固定；
- 有复杂拓扑时，再在隔离环境评估 <code>TopologyAwareWorkloadScheduling</code> 和 <code>CompositePodGroup</code>；
- queue/quota/fair sharing 仍由 Kueue、Volcano 或其他项目治理，不由上游 Gang 自动提供。

失败场景至少覆盖：

- GPU 数量够但 NIC/NUMA 不满足；
- 一个 Pod 的 claim 已 reserve，另一个 Pod 失败；
- PodGroup 触发 preemption 后 victim 未完全退出；
- driver status 延迟、ResourceSlice 删除、kubelet prepare 失败；
- controller 重启后 template claim 重复创建或无法回收。

### 10.3 推理 worker：HPA scale-to-zero + Gateway

适用情形：低频内部模型、批量 embedding、离线队列消费者或可接受冷启动的 GPU worker。

要点：

- 用 durable queue 或独立 object metric 作为零副本时仍存在的 signal；
- 设置 <code>minReplicas: 0</code> 前先验证 <code>external.metrics.k8s.io</code> 的 label selector 和单位；
- <code>ScaledToZero</code> 只表示 HPA 认为自己拥有 zero 状态，不表示模型 gateway 会保存请求；
- Gateway/activator/queue 必须能在 worker 为零时接收、持久化、重试和限流；
- 记录 queue age、scale decision、Pod scheduling latency、image/model load、first-token latency 和 error rate；
- 对 streaming 请求设置明确的最长等待、取消和 drain 行为。

如果是面向终端用户的同步 LLM API，常见做法是保留一个小 warm pool，把 HPA scale-to-zero 只用于后台 worker 或弹性 overflow pool，而不是让所有请求直接撞到零副本 Service。

### 10.4 NUMA/GPU 节点：Pod-level manager + 标准 NUMA 属性

适用情形：Pod 有主 GPU/CPU worker 和多个轻量 sidecar，要求主容器在同一 NUMA 节点，sidecar 又不能浪费独占 CPU。

组合条件：

1. Pod spec 使用 Pod-level resources；
2. <code>PodLevelResourceManagers</code> 显式开启并锁定 kubelet 配置；
3. Topology Manager、CPU Manager、Memory Manager 的 policy/scope 相容；
4. DRA driver 发布统一 <code>resource.kubernetes.io/numaNode</code> 或必要的 derived attribute；
5. device plugin、GPU runtime、RDMA 和 CSI 都能在目标节点兑现 allocation；
6. 观测 <code>cpuset.cpus</code>、<code>memory.numa_stat</code>、DRA status、OOM/eviction 和 GPU locality。

在没有这些验证前，用 label/taint 和传统 Pod-level requests 表达一个“尽量靠近”的意图，不要宣称已经获得跨设备原子 NUMA placement。

### 10.5 cgroups v2 Memory QoS + AI agent/模型缓存

Memory QoS 可以减轻模型加载、tokenizer、KV cache 和 sidecar 争抢内存时的节点压力，但它也可能把内存不足更早暴露为 throttling 或 OOM。建议：

- 为模型 worker、cache sidecar、日志/telemetry sidecar 设清晰 request/limit；
- 首先使用默认 <code>memoryReservationPolicy: None</code> 建立现状；
- 逐步启用 TieredReservation，比较 <code>memory.min</code>/<code>memory.low</code>、reclaim 和 tail latency；
- 只有明确理解 workload 的 memory burst 后才设置 <code>memoryThrottlingFactor</code>；
- 对 in-place resize、DRA node allocatable 和 Pod-level manager 做联合测试；
- 对 Agent Sandbox 或代码执行 Pod 额外限制临时文件、编译 cache 和外部下载。

### 10.6 RangeStream + controller cache + storage migration

大规模 AI 平台往往同时有数十万 Pod、Job、Workload、ResourceClaim 和自定义状态。推荐组合：

- etcd 3.7 + <code>EtcdRangeStream</code> 降低大列表读取峰值；
- watch cache resilient initialization 保护 API server 恢复；
- controller-runtime 使用 namespace/selector/metadata-only cache，避免无边界全集 watch；
- list/watch client 处理 429、bookmark、resourceVersion、compaction 和 reconnect；
- CRD schema 升级先创建 StorageVersionMigration，再移除 old served/stored version；
- 使用 <code>apiserver_storage_list_duration_seconds</code>、cache sync latency、controller workqueue depth、etcd backend commit/fsync latency 做容量基线。

这套组合把控制面“能不能读取”和 controller“如何消费”同时治理。只升级 etcd 或只增加 controller replicas 都不能解决另一半问题。

### 10.7 多租户安全：Admission + Pod Certificates + Kubelet authz

对共享 GPU/AI 集群，最小安全组合可以是：

- manifest-based admission 固化禁止 privileged/hostPath/危险 host namespace 的基线；
- API-based admission 承载可动态变更的团队/项目策略；
- Pod Certificates/ClusterTrustBundles 发行内部 mTLS identity 和 trust；
- RBAC 使用 namespace、Group、ServiceAccount 和短生命周期；
- kubelet fine-grained authz 让监控只能读 <code>nodes/metrics</code>/<code>nodes/stats</code>；
- audit log 和 JIT debug gateway 记录临时 <code>exec</code>/portforward；
- User Namespace、runtime sandbox、NetworkPolicy 和 egress gateway 缩小 agent 逃逸/数据外传路径。

这些 controls 之间没有“一个开启就全安全”的关系。应分别做 policy bypass、凭据泄露、节点入侵、debug overreach 和 tenant cross-read 演练。

---

## 第十一章：升级、回滚与验证清单

### 11.1 版本和对象盘点

- [ ] 记录 control plane、kubelet、etcd、CRI、CNI、CSI、device plugin/DRA driver、metrics-server、Gateway controller 的精确版本和镜像 digest。
- [ ] 固定 Kubernetes v1.37.0 source <code>f54c212e3a2f75d674b717a9b29052b20b60aefc</code>，并阅读 [CHANGELOG-1.37](https://github.com/kubernetes/kubernetes/blob/f54c212e3a2f75d674b717a9b29052b20b60aefc/CHANGELOG/CHANGELOG-1.37.md) 的 urgent upgrade notes。
- [ ] 盘点所有 <code>Workload</code>/<code>PodGroup</code> 的 API version；从 v1.36 升级前导出并清理不再 served 的 <code>scheduling.k8s.io/v1alpha2</code> 对象。
- [ ] 盘点 HPA、外部/对象指标、metrics adapter、Gateway routes、Ingress annotations、StatefulSet strategies、DRA ResourceClaim/Template 和 CRD <code>.status.storedVersions</code>。
- [ ] 记录现有 feature gate，不用“当前 API 能创建”推断“相关 controller/scheduler/kubelet 行为已启用”。

### 11.2 HPA Scale-to-Zero

- [ ] 只让队列、批处理或可接受冷启动的 workload 使用 <code>minReplicas: 0</code>。
- [ ] 确认 object/external metric 在 zero Pod 时仍存在，且 selector、单位、freshness、RBAC、TLS 都正确。
- [ ] <code>kubectl get --raw '/apis/external.metrics.k8s.io/v1beta1/...'</code> 返回有效值。
- [ ] 检查 <code>ScaledToZero=True/False</code>、<code>ScalingActive</code>、<code>ScalingLimited</code> 和 HPA events。
- [ ] 在 controller manager 和 API server 版本混跑期间，不新建依赖 zero condition 的 HPA。
- [ ] 回滚前将 HPA <code>minReplicas</code> 改为至少 1，并拉起当前 zero workload；不要先关 gate 再处理对象。

### 11.3 etcd、API server 和 controller 性能

- [ ] etcd 至少为 3.7，确认 <code>EtcdRangeStream</code> 真实命中 <code>operation="listStream"</code>；如果只看到 fallback，要按 fallback 峰值容量规划。
- [ ] 记录 <code>apiserver_storage_list_duration_seconds</code>、etcd backend commit/fsync、watch cache init、429、API Priority and Fairness 和 conversion webhook concurrency。
- [ ] 所有 controller/client 对 429、<code>Retry-After</code>、watch 断线、compaction 和 resourceVersion 失效有 backoff/重新 list 逻辑。
- [ ] 只有在能稳定分配 shard owner、处理 replica 数变化和 fallback 的 controller 上试验 <code>ShardedListAndWatch</code>。
- [ ] controller-runtime cache 做对象类型、namespace、selector、metadata-only、uncached read 的内存和延迟基线。
- [ ] 把 <code>DeclarativeValidation</code> 的 validation warning/error 和旧客户端 patch/apply 回归纳入升级测试。

### 11.4 DRA、GPU 和资源拓扑

- [ ] DRA driver 支持目标 Kubernetes 的 ResourceSlice、ResourceClaim、device status、health API 和 kubelet plugin helper。
- [ ] 如果使用 DRA ResourceHealth v1，检查 driver 是否实现新 helper interface 的 <code>WatchHealthStatus</code>，并验证 v1/v1alpha1 过渡。
- [ ] extended resource → DRA DeviceClass 映射不改变旧 workload 的设备选择和计费。
- [ ] 对 DeviceTaintRule、claim tolerance、既有 Pod 驱逐和 maintenance repair 做实测。
- [ ] 对 <code>resource.kubernetes.io/numaNode</code>、derived attribute、MIG/vGPU compatibility group 进行跨 driver 设备配对测试。
- [ ] 开启 <code>GenericWorkload</code>/<code>DRAWorkloadResourceClaims</code> 前，确认 API server、scheduler、controller、kubelet 和 driver 的 gate/版本一致。
- [ ] 对 shared claim 的 owner、reservedFor、扩缩、controller restart、失败重试和删除做 orphan 检查。
- [ ] GPU Operator、HAMi、RDMA、NVIDIA device plugin、CSI、CNI 在 rootless/kubelet user namespace 节点池上分别验证。

### 11.5 Workload、Gang 和抢占

- [ ] 用 v1beta1 schema 重建 Workload/PodGroup，不把 v1.36 的 v1alpha2 存量对象留给升级后的 apiserver。
- [ ] 明确 Basic scheduling 与 Gang scheduling 的 <code>minCount</code>、PodSet、readiness 和 completion 语义。
- [ ] 验证整个 PodGroup 的 placement、DRA claim reservation、PDB、priority、preemption victims 和失败重试。
- [ ] 不把 Workload-aware preemption 当作 Kueue/Volcano 的 queue fairness、quota 或 capacity guarantee。
- [ ] <code>TopologyAwareWorkloadScheduling</code>、<code>CompositePodGroup</code>、<code>PodGroupPreemptionPolicy</code>、<code>WorkloadWithJob</code> 逐个 gate、逐个场景验收。

### 11.6 Rootless、cgroups v2、SELinux 和存储

- [ ] <code>KubeletInUserNamespace</code> 只在预先构造好的 rootless runtime/user namespace 中启用；gate 默认开启不会自动迁移节点。
- [ ] 用 <code>runningInUserNamespace</code> 建立 node label/taint，隔离需要真实 host root 的 DaemonSet。
- [ ] 验证 CNI 修改网络、iptables/nftables、sysctl、内核模块和 kube-proxy 的能力。
- [ ] 验证 CSI mount、fsGroup、idmapped mount、volume ownership、snapshot、设备节点和卸载。
- [ ] cgroups v2 下记录 <code>memory.min</code>、<code>memory.low</code>、<code>memory.high</code>、OOM、reclaim 和 throttling；不要把 <code>memory.high</code> 的旧默认行为当成 v1.37 默认。
- [ ] SELinux 集群测试 shared volume、多 label Pod、CSI <code>seLinuxMount</code>、<code>MountOption</code> 与 <code>Recursive</code> fallback。
- [ ] StatefulSet <code>Recreate</code> 只在允许 downtime 的 workload 上启用；先演练 PVC、leader、PDB 和回滚。

### 11.7 Gateway、Ingress 和 admission

- [ ] 固定 Gateway API CRD bundle、controller image、conformance report 和 controller-specific extension 版本。
- [ ] TCPRoute/UDPRoute 从 v1alpha2 迁移到 <code>gateway.networking.k8s.io/v1</code>，同时确认 controller 已实现 Standard channel。
- [ ] 用 Ingress2Gateway 生成候选文件，逐条审查 annotation、regex、rewrite、CORS、timeout、TLS 和 session 行为。
- [ ] Ingress-NGINX retirement 迁移采用双栈/影子流量/行为对比，不把 YAML 转换成功当作流量等价。
- [ ] manifest-based admission 目录有 checksum、权限、原子发布、启动失败和紧急回滚流程；所有静态对象符合 <code>.static.k8s.io</code> 命名约束。
- [ ] 测试 etcd 不可用、API server restart、坏 policy、CEL error、policy self-protection 和人工修复。

### 11.8 回滚前置条件

回滚 Kubernetes minor 版本不能简单理解为替换二进制。至少要先回答：

| 问题 | 必须有的答案 |
| --- | --- |
| 新 API 对象能否被旧版本读取 | Workload/PodGroup、StorageVersionMigration、DRA、Pod Certificate、CTB、Gateway CRD 分别确认 |
| 新 gate 是否可关闭 | 关闭顺序、现有对象/运行中 Pod 的行为、component skew 窗口 |
| etcd 数据是否已经重写 | storage version、encryption、SVM status、backup/restore |
| workload 是否已经使用 zero/gang/shared claim | 先恢复为旧版本可理解的 replicas、Pod/claim ownership 和调度模式 |
| 节点是否已经 rootless/cgroups v2 | 回滚后的 kubelet、CRI、CNI、CSI 和 GPU 栈能否继续启动 |
| 网络 API 是否已切换 | Gateway controller/CRD、Ingress fallback、TCP/UDP v1/v1alpha2 |
| Admission 是否由静态文件保护 | 旧 API server 是否认识配置格式和静态目录，坏配置如何恢复 |

如果答案依赖“旧版本也许会 fallback”，就必须把 fallback 当成单独的容量和安全模式测试，而不是把它写成无损回滚。

---

## 结论

截至 2026-09-06，Kubernetes Blog/RSS 展示的核心趋势可以概括为：

1. **控制面更重视峰值和恢复。** RangeStream、watch cache protection、concurrent decode 和 storage migration 共同处理大规模 API server 的内存、恢复和版本生命周期。
2. **AI 调度的上游基础开始成形。** Workload/PodGroup、Gang、workload-aware preemption、DRA claim、标准 NUMA 属性和 Pod-level manager 让 Kubernetes 可以表达更多 AI/HPC 资源关系，但许多组合仍默认关闭。
3. **弹性开始允许零副本。** HPA Scale-to-Zero 对队列 worker 很有价值，不能被误读成 Kubernetes Service 或 LLM streaming 自动具备 request buffering。
4. **安全能力分层而非单点解决。** Pod User Namespaces、rootless kubelet、细粒度 kubelet authz、Pod Certificates/ClusterTrustBundles、Admission 和 JIT debug 各自缩小不同的风险面。
5. **网络和 AI 生态正在标准化，但仍有扩展边界。** Gateway API Standard、Ingress2Gateway、AI Gateway WG、Inference Extension 和 Agent Sandbox 是一条生态链，不是一组已经全部进入 Kubernetes Core 的 API。

生产平台的正确落地方式，是先把 Stable 能力纳入版本基线，再把 Beta/default-off 能力按 gate、组件、对象迁移和回滚条件逐个灰度；Alpha 与生态项目保持隔离实验和明确的非兼容标记。对 GPU 训练、LLM serving 和 AI agent，最终的系统合同必须同时覆盖请求、控制、存储、身份、设备、拓扑、隔离和运维，而不能只从一个 Blog 标题选择 feature。

---

## 附录：RSS 清单、版本和官方参考

### A.1 版本快照

| 项目 | 快照 |
| --- | --- |
| Kubernetes stable release | <code>v1.37.0</code> |
| Annotated tag object | <code>157e582fcc3ebba3c22b16721f49d6890f784c1f</code> |
| Tag 解引用后的 exact source commit | <code>f54c212e3a2f75d674b717a9b29052b20b60aefc</code> |
| v1.37 enhancement count | 67 |
| Stable / Beta / Alpha / deprecation | 16 / 23 / 27 / 1 |
| RSS feed | <https://kubernetes.io/feed.xml> |
| 审校日期 | 2026-09-06 |

<code>v1.37.0</code> 的 tag object 和 source commit 是两个不同的 Git object。本文以及仓库渲染元数据使用 source commit；tag object 仅保留在本表作为 Git ref 复核信息。Blog 中的 Beta/Alpha、Working Group proposal、生态 CRD 和主线实现均不扩大 <code>v1.37.0</code> 的 Stable 兼容承诺。

### A.2 Kubernetes v1.37 官方文章

| 主题 | 官方链接 |
| --- | --- |
| v1.37 Release / Garhwal | <https://kubernetes.io/blog/2026/08/26/kubernetes-v1-37-release/> |
| HPA Scale-to-Zero | <https://kubernetes.io/blog/2026/09/02/kubernetes-v1-37-hpa-scale-to-zero-beta/> |
| DRA Updates | <https://kubernetes.io/blog/2026/09/03/kubernetes-v1-37-dra-updates/> |
| KubeletInUserNamespace | <https://kubernetes.io/blog/2026/09/04/kubernetes-v1-37-rootless-beta/> |
| etcd RangeStream | <https://kubernetes.io/blog/2026/09/01/kubernetes-v1-37-etcd-range-stream/> |
| Storage Version Migration | <https://kubernetes.io/blog/2026/08/31/kubernetes-v1-37-storage-version-migration-ga/> |
| Pod Certificates / ClusterTrustBundles | <https://kubernetes.io/blog/2026/08/28/kubernetes-v1-37-pod-certificates-and-cluster-trust-bundles/> |
| Metrics API | <https://kubernetes.io/blog/2026/08/27/kubernetes-v1-37-metrics-api-ga/> |
| KYAML | <https://kubernetes.io/blog/2026/08/11/how-to-pretty-print-kubernetes-yaml-as-kyaml/> |
| v1.37 Sneak Peek | <https://kubernetes.io/blog/2026/07/31/kubernetes-v1-37-sneak-peek/> |

### A.3 Kubernetes v1.36 前置文章

| 主题 | 官方链接 |
| --- | --- |
| Workload-Aware Scheduling | <https://kubernetes.io/blog/2026/05/13/kubernetes-v1-36-advancing-workload-aware-scheduling/> |
| DRA v1.36 | <https://kubernetes.io/blog/2026/05/07/kubernetes-v1-36-dra-136-updates/> |
| Volume Group Snapshots | <https://kubernetes.io/blog/2026/05/08/kubernetes-v1-36-volume-group-snapshot-ga/> |
| Server-Side Sharded List and Watch | <https://kubernetes.io/blog/2026/05/06/kubernetes-v1-36-server-side-sharded-list-and-watch/> |
| Declarative Validation | <https://kubernetes.io/blog/2026/05/05/kubernetes-v1-36-declarative-validation-ga/> |
| Manifest-based Admission | <https://kubernetes.io/blog/2026/05/04/kubernetes-v1-36-manifest-based-admission-control/> |
| Pod-Level Resource Managers | <https://kubernetes.io/blog/2026/05/01/kubernetes-v1-36-feature-pod-level-resource-managers-alpha/> |
| Memory QoS | <https://kubernetes.io/blog/2026/04/29/kubernetes-v1-36-memory-qos-tiered-protection/> |
| Fine-Grained Kubelet Authorization | <https://kubernetes.io/blog/2026/04/24/kubernetes-v1-36-fine-grained-kubelet-authorization-ga/> |
| User Namespaces GA | <https://kubernetes.io/blog/2026/04/23/kubernetes-v1-36-userns-ga/> |
| SELinux volume labeling | <https://kubernetes.io/blog/2026/04/22/breaking-changes-in-selinux-volume-labeling/> |

### A.4 Gateway、Agent 和 AI 生态文章

| 主题 | 官方链接 |
| --- | --- |
| Gateway API v1.5 | <https://kubernetes.io/blog/2026/04/21/gateway-api-v1-5/> |
| Gateway API v1.6 | <https://kubernetes.io/blog/2026/08/03/gateway-api-v1-6-release/> |
| Gateway API project | <https://gateway-api.sigs.k8s.io/> |
| Ingress2Gateway 1.0 | <https://kubernetes.io/blog/2026/03/20/ingress2gateway-1-0-release/> |
| Ingress-NGINX migration behaviors | <https://kubernetes.io/blog/2026/02/27/ingress-nginx-before-you-migrate/> |
| AI Gateway Working Group | <https://kubernetes.io/blog/2026/03/09/announcing-ai-gateway-wg/> |
| Gateway API Inference Extension | <https://kubernetes.io/blog/2025/06/05/introducing-gateway-api-inference-extension/> |
| Agent Sandbox | <https://kubernetes.io/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/> |
| Headlamp Kubeflow plugin | <https://kubernetes.io/blog/2026/07/13/introducing-headlamp-plugin-for-kubeflow/> |
| Headlamp Volcano plugin | <https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/> |
| Headlamp Knative plugin | <https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/> |

### A.5 官方 KEP 与文档

| 能力 | KEP/文档 |
| --- | --- |
| HPA scale-to-zero | <https://kep.k8s.io/2021> |
| etcd RangeStream | <https://kep.k8s.io/5966> |
| Storage Version Migration | <https://kep.k8s.io/4192> |
| Server-side sharded list/watch | <https://kep.k8s.io/5866> |
| Manifest-based admission | <https://kep.k8s.io/5793> |
| Node Declared Features | <https://kep.k8s.io/5328> |
| Pod Certificates | <https://kep.k8s.io/4317> |
| ClusterTrustBundles | <https://kep.k8s.io/3257> |
| User Namespaces | <https://kep.k8s.io/127> |
| Kubelet in UserNS | <https://kep.k8s.io/2033> |
| Fine-grained kubelet authz | <https://kep.k8s.io/2862> |
| DRA extended resources | <https://kep.k8s.io/5004> |
| DRA Workload claims | <https://kep.k8s.io/5729> |
| DRA standard NUMA attribute | <https://kep.k8s.io/6072> |
| DRA derived attributes | <https://kep.k8s.io/6080> |
| DRA compatibility groups | <https://kep.k8s.io/5963> |
| Pod-level resource managers | <https://kep.k8s.io/5526> |
| Workload-aware scheduling | <https://kep.k8s.io/5732> |
| Job/Workload integration | <https://kep.k8s.io/5547> |
| PodGroup preemption policy | <https://kep.k8s.io/5710> |
| Volume group snapshots | <https://kubernetes-csi.github.io/docs/group-snapshot-restore-feature.html> |
| SELinux mount changes | <https://kep.k8s.io/1710> |
| StatefulSet Recreate | <https://kep.k8s.io/3541> |
| kube-proxy nftables | <https://kep.k8s.io/3866> |
| localhost nftables NodePort | <https://kep.k8s.io/6032> |
| Memory QoS | <https://kep.k8s.io/2570> |
| CRI-full stats | <https://kep.k8s.io/2371> |
| KYAML | <https://kep.k8s.io/5295> |
| Metrics API | <https://kep.k8s.io/5207> |

### A.6 v1.37 exact source and API references

| 主题 | v1.37.0 exact source |
| --- | --- |
| Kubernetes v1.37.0 source | <https://github.com/kubernetes/kubernetes/tree/f54c212e3a2f75d674b717a9b29052b20b60aefc> |
| Release notes | <https://github.com/kubernetes/kubernetes/blob/f54c212e3a2f75d674b717a9b29052b20b60aefc/CHANGELOG/CHANGELOG-1.37.md> |
| Feature gates and final defaults | <https://github.com/kubernetes/kubernetes/blob/f54c212e3a2f75d674b717a9b29052b20b60aefc/pkg/features/kube_features.go> |
| Workload/PodGroup v1beta1 types | <https://github.com/kubernetes/kubernetes/blob/f54c212e3a2f75d674b717a9b29052b20b60aefc/staging/src/k8s.io/api/scheduling/v1beta1/types.go> |
| DRA resource v1 types | <https://github.com/kubernetes/kubernetes/blob/f54c212e3a2f75d674b717a9b29052b20b60aefc/staging/src/k8s.io/api/resource/v1/types.go> |
| DRA scheduler plugin | <https://github.com/kubernetes/kubernetes/blob/f54c212e3a2f75d674b717a9b29052b20b60aefc/pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go> |
| Workload/PodGroup scheduling cycle | <https://github.com/kubernetes/kubernetes/blob/f54c212e3a2f75d674b717a9b29052b20b60aefc/pkg/scheduler/schedule_one_podgroup.go> |
| DRA kubelet manager | <https://github.com/kubernetes/kubernetes/blob/f54c212e3a2f75d674b717a9b29052b20b60aefc/pkg/kubelet/cm/dra/manager.go> |
| StatefulSet controller | <https://github.com/kubernetes/kubernetes/blob/f54c212e3a2f75d674b717a9b29052b20b60aefc/pkg/controller/statefulset/stateful_set_control.go> |
| kube-proxy nftables | <https://github.com/kubernetes/kubernetes/tree/f54c212e3a2f75d674b717a9b29052b20b60aefc/pkg/proxy/nftables> |
| API server storage | <https://github.com/kubernetes/kubernetes/tree/f54c212e3a2f75d674b717a9b29052b20b60aefc/staging/src/k8s.io/apiserver/pkg/storage> |

### A.7 相关仓库内文档

- [Kubernetes 原生调度器深度技术文档](Kubernetes-Native-Scheduler-Deep-Dive.html)
- [Kubernetes AI 调度器深度对比](Kubernetes-AI-Schedulers-Deep-Dive.html)
- [Volcano 升级与 Feature 兼容性](Volcano-Upgrade-Compatibility-Deep-Dive.html)
- [KServe 深度技术文档](KServe-Deep-Dive.html)
- [Kubeflow 深度技术文档](Kubeflow-Deep-Dive.html)
- [NVIDIA GPU Operator 深度技术文档](NVIDIA-GPU-Operator-Deep-Dive.html)
- [HAMi 深度技术文档](HAMi-Deep-Dive.html)
- [E2B AI Sandbox 深度技术文档](E2B-Deep-Dive.html)
- [Multica 深度技术文档](Multica-Deep-Dive.html)
