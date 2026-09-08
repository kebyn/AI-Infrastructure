# Self-hosted 基础设施访问平台对比：Teleport、The Bastion、Warpgate 及扩展参照

> **从 OpenSSH/VPN/传统堡垒机迁移时，比较身份、协议代理、授权、审计、故障域和运维成本**
>
> Teleport 仍是主要基线，但本文不把其它产品压缩成一行式竞品列表：The Bastion、Warpgate 按相同维度深入分析，Boundary、Pomerium、Guacamole 作为类别边界清晰的扩展参照。源码、版本和许可证均以固定链接为证据，不把营销页面或未发布主线当成稳定能力。
>
> **审校日期：2026-09-06。** Teleport `v18.10.0@ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d` 是主要稳定基线；其余版本和审计 commit 见第一章及附录 B。原有文件路径保持不变，方便已有链接继续指向本文。

---

## 目录

- [第一章：比较对象、版本与证据规则](#第一章比较对象-版本与证据规则)
- [第二章：平台家族与架构模型](#第二章平台家族与架构模型)
- [第三章：总体架构](#第三章总体架构)
- [第四章：身份、证书与信任链](#第四章身份-证书与信任链)
- [第五章：授权模型与最小权限](#第五章授权模型与最小权限)
- [第六章：各类资源的访问路径](#第六章各类资源的访问路径)
- [第七章：会话记录、审计与数据治理](#第七章会话记录-审计与数据治理)
- [第八章：部署、高可用与迁移](#第八章部署-高可用与迁移)
- [第九章：安全模型与威胁分析](#第九章安全模型与威胁分析)
- [第十章：运维、升级与故障排查](#第十章运维-升级与故障排查)
- [第十一章：统一能力矩阵与深入对比](#第十一章统一能力矩阵与深入对比)
- [第十二章：部署、迁移和验收对比](#第十二章部署-迁移和验收对比)
- [第十三章：场景化选型与组合架构](#第十三章场景化选型与组合架构)
- [附录 A：生产验收用例](#附录-a生产验收用例)
- [附录 B：固定版本、许可证与官方来源](#附录-b固定版本-许可证与官方来源)

---

## 第一章：比较对象、版本与证据规则

### 1.1 比较范围与问题定义

本文讨论的是 self-hosted 基础设施访问平台，而不是“所有能转发 TCP 的软件”。统一问题是：谁能在什么条件下访问哪一台主机、集群、数据库、应用或桌面；平台是否签发短期身份；协议是否在代理处被理解和记录；控制面、数据面和审计后端故障时已有会话如何处理。

| 家族 | 本文角色 | 实际解决的问题 | 不应误读为 |
| --- | --- | --- | --- |
| Teleport | 主基线、完整深度 | CA、短期证书、资源侧 Agent、多协议代理和统一审计 | 目标主机/Kubernetes/数据库的最终授权或 Sandbox |
| The Bastion | 核心深度对象 | SSH/Unix/网络设备入口、delegated group、syslog/ttyrec 和低外部依赖 | 多协议身份 CA 或数据库 query 审计平台 |
| Warpgate | 核心深度对象 | 单 Rust 二进制、内置 Web UI、浏览器终端、SSH/Kube/DB/RDP/VNC 入口 | Teleport 级别的 CA/资源发现/多租户治理 |
| Boundary | session broker 参照 | 控制器/worker 通过身份化连接和 credential injection 访问 target | 终端协议级录制和完整 PAM |
| Pomerium | HTTP/TCP 零信任参照 | OIDC 驱动的应用入口、策略和身份感知代理 | SSH、数据库、PTY 或桌面审计平台 |
| Guacamole | 浏览器协议网关参照 | 浏览器化 RDP/VNC/SSH 和连接配置 | 身份生命周期、资源级 JIT 或不可抵赖审计控制面 |

### 1.2 固定版本、tag 类型与稳定边界

| 平台 | 固定证据（审校日） | tag/发布状态 | 许可证和边界 |
| --- | --- | --- | --- |
| Teleport | `v18.10.0@ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d` | 2026-07-09 正式 Release；lightweight tag | GitHub 源码 AGPL-3.0；官方 Community binary 另受 Community Edition License 和规模条件约束；Enterprise/Cloud 不纳入稳定承诺 |
| The Bastion | `v3.24.01@30c8b522ddd9db2993e22b05b0ee19f961cadf1d` | 2026-07-08 正式 Release；lightweight tag | Apache-2.0；Perl 插件/helper 与 Unix 账号模型属于项目实现，部署仍需按目标系统加固 |
| Warpgate | `v0.28.6@525c7caf2219d5f5e3913b5732e4cbad5d15cd34` | 2026-09-01 正式 Release；lightweight tag | Apache-2.0；单二进制和 SQLite 是该版本稳定边界，主线新协议不前推 |
| Boundary | `v0.21.3@8c9715c868537616a11e0ea555b20042e212bdbc` | 2026-04-30 正式 Release；lightweight tag | Business Source License 1.1（MariaDB BSL 文本）；生产使用须复核变更日期和商业条款，不把它写成 Apache OSS |
| Pomerium | `v0.33.1@01af7466fa3b26b5e5369df49f367737d81ad18e` | 2026-08-18 正式 Release；lightweight tag | Apache-2.0；HTTP/TCP identity-aware proxy 边界，企业托管/高级策略另行核对 |
| Guacamole | server `1.6.0@1f664e08feae6e7d15d8146b78acab2e6fb470ae`；client `1.6.0@0537c89cd783681b986ff8f8c4e0b97ec6873371` | 审校日未找到 GitHub Release；官方 `1.6.0` annotated tag 可验证但按 tag-only 处理 | Apache-2.0；不把无 Release 的 tag-only 当作厂商稳定兼容承诺，部署前仍应固定并测试 server/client 实际发行包 |

正式 Release、tag-only、RC/prerelease、主线快照和商业/托管能力必须分开。本文没有把 Boundary 的主线功能、Guacamole `1.6.0` tag 后变化、Teleport Enterprise entitlement 或任何产品的 SaaS 行为算进稳定兼容性。

### 1.3 共同信任边界

```mermaid
flowchart LR
    U[用户身份面\nOIDC/MFA/SSH key/Web UI] --> P[访问控制面\nRole/Policy/Target assignment]
    P --> D[代理与连接数据面\nAgent/Worker/Proxy/Guacd]
    D --> R[目标资源原生授权\nUnix/Kubernetes/DB/App/Windows]
    D --> A[事件、录制与外部归档\nSQLite/Object store/SIEM]
```

每个平台都应回答五个问题：核心状态存在哪里；私钥、证书或 ticket 存在哪里；代理是否需要资源侧 Agent；目标故障时已有会话是否继续；审计后端不可用时是 fail-open、降级记录还是主动拒绝。网络可达性不等于授权，连接元数据也不等于协议级审计。

### 1.5 Teleport 解决什么问题

基础设施访问常被拆成多套彼此独立的系统：SSH key 管服务器，`kubeconfig` 管 Kubernetes，数据库账号和跳板机管数据层，VPN 提供网络可达性，Web SSO 只保护浏览器入口。结果是人员离职、权限变更、密钥轮换和审计检索都要跨系统完成，而且“能连到网段”常被误当成“有权访问资源”。

Teleport 把这组问题收敛为一个身份与证书控制面：

- Auth Service 维护用户 CA、主机 CA 和集群动态资源，完成登录、证书签发与授权决策；
- Proxy Service 暴露统一入口，承载 Web UI、协议路由和 Agent 反向隧道；
- 资源侧 Agent 解析 SSH、Kubernetes、数据库、应用、Desktop 与 MCP 等协议，执行资源匹配并产生审计事件；
- 人类通过 `tsh` 或 Web UI 获取短期身份，管理员使用 `tctl` 管理集群，机器身份由 `tbot` 持续获取和续期短期凭据；
- Role 把身份、标签、目标登录名、Kubernetes 用户/组、数据库用户/名和 MCP tool 等条件组合起来。

一句话概括：

> **Teleport 是身份感知访问代理、短期证书 CA、统一授权与审计系统；它缩短凭据寿命并集中访问路径，但不替代目标系统自己的授权、安全加固或终端防护。**

### 1.6 与常见接入方式的差异

| 方案 | 主要解决的问题 | 长期身份/密钥 | 资源级授权 | 协议审计 | Teleport 的差异 |
| --- | --- | --- | --- | --- | --- |
| VPN / ZTNA 网络接入 | 让终端到达网段或服务 | 常有设备证书或隧道凭据 | 通常停留在网络/应用层 | 通常是连接元数据 | Teleport 在会话建立时签发短期资源凭据并理解部分上层协议 |
| OpenSSH Bastion | SSH 跳转与集中入口 | 常见 authorized_keys 或代理转发 | 以 Unix login、SSH config 为主 | 可记录日志，完整性依赖额外组件 | Teleport 自带 SSH CA、角色/标签匹配、会话录制和资源库存 |
| 传统堡垒机/PAM | 账号托管、审批和录屏 | 可能保管目标账号密码 | 通常强，但产品与协议差异大 | 通常强 | Teleport 更强调证书、资源侧 Agent 与原生客户端协议；完整 PAM 治理不是 Community 承诺 |
| Kubernetes 原生 RBAC | 控制 Kubernetes API 对象 | kubeconfig/token/cert | 原生且最终生效 | API audit 由集群负责 | Teleport 负责入口、集群路由、身份映射和额外资源过滤，目标集群 RBAC 仍是第二道授权 |
| 数据库跳板机 | 建立数据库网络通道 | 数据库密码或云凭据 | 多依赖数据库自身账号 | 未必解析 query | Teleport 可签发数据库身份、代理原生 wire protocol 并按协议生成 query/RPC 事件 |
| Cloud IAM | 云资源权限 | 临时或长期云凭据 | 云厂商原生 | CloudTrail 等原生日志 | Teleport 可作为统一登录与本地代理入口，但最终云授权仍由 IAM 决定 |

Teleport 的价值不在于取代每个目标系统，而在于把“谁、以什么身份、从哪个入口、访问什么资源、持续多久、留下什么证据”统一起来。

### 1.7 本文中的 OSS 到底指什么

`v18.10.0` 存在三条必须分开的边界：

| 对象 | v18.10.0 官方证据 | 本文处理方式 |
| --- | --- | --- |
| GitHub 源码 | 仓库根 `LICENSE` 为 GNU AGPL-3.0 | 可以审计、构建和自托管；修改后通过网络提供服务时应评估 AGPL 第 13 条义务 |
| 官方 Community 二进制 | 同提交 Feature Matrix 标为 Teleport Community Edition License；许可文件限定为少于 100 名员工且年收入低于 1,000 万美元的组织 | 不能因为源码是 AGPL 就推断官方下载二进制也不受附加条件；部署前必须复核当期许可文本 |
| Enterprise / Cloud | 商业发行、托管控制面和额外 entitlement | 不纳入本文稳定兼容承诺，只在能力矩阵中标出边界 |

因此，本文使用“OSS”表示 **以 `v18.10.0` AGPL 源码和 Community 功能面为核心的自托管路径**，不是法律意见，也不替部署方判断官方下载包、商标、支持或再分发条件。

### 1.8 Teleport 稳定版本证据

截至 2026-09-06，GitHub `releases/latest` 返回 `v18.10.0`，其 Release 状态为 `draft=false`、`prerelease=false`。该 tag 是 lightweight tag，直接指向 source commit：

```text
v18.10.0
└── commit ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d
```

`master` 是下一个 major 的开发分支，仓库还存在多种 `v19.*-dev.*` tag；这些都不是本文的稳定能力证据。页面中的字段、默认值和兼容判断以 `ddaa46…` 为准，不把随后主线实现倒灌到 v18。

### 1.9 v18.10.0 与 OSS 直接相关的变化

| 变化 | 运维影响 |
| --- | --- |
| Windows Desktop 单次 RDP 会话可共享多个目录，并可在不中断会话时卸载 | 升级后应复测目录读写、卸载事件、磁盘占用和角色开关；AI session summary 属于 Identity Security，不是 OSS 承诺 |
| 修复 Redshift 通过 MCP 的连接问题 | 使用 MCP gateway 接数据库的环境应覆盖真实握手与查询，不应只测 `tools/list` |
| 修复 Application Access 会话过早到期以及长连接证书续期后的重复 403 | HTTP 长连接应在证书到期后收到 `Connection: close` 并重连；客户端仍需正确处理重连 |
| Kubernetes `kubernetes_resources.verbs` 中任意位置的 `*` 均应生效 | 模板展开和多 verb 角色要做回归；不要依赖旧版本的错误拒绝行为 |
| 添加 ephemeral container 要求同一 Role 同时有 `exec` 和 `patch`/`update` | 旧角色在升级后可能被拒绝，需显式核对 `pods/ephemeralcontainers` 权限 |
| 无效 Role expression、Access Request wildcard 与 session-join 字段在创建时加强校验 | 配置即代码流水线可能从“运行时失败”变成“创建时失败”，升级前应 dry-run/测试提交 |

---

## 第二章：平台家族与架构模型

### 2.1 Teleport：身份控制面与资源侧 Agent

Teleport 的 Auth Service 持有 CA、用户和动态资源状态，Proxy Service 作为统一公网入口，Agent 在资源侧主动出站建立反向隧道。`tsh`/Web UI 取得短期用户证书，`tbot` 取得机器凭据；Agent 在 SSH、Kubernetes、数据库、应用、Desktop 和 MCP 路径上执行标签/Role 匹配并产生事件。目标主机、API server 或数据库仍执行第二次原生授权。核心状态是 Auth backend 和录制对象存储，CA 私钥和 backend 备份属于最高信任资产。

### 2.2 The Bastion：SSH 入口/出口与 Unix DAC

The Bastion 以 SSH 入口和出口协议断开为中心：用户使用标准 SSH 客户端连接 bastion，bastion 再以受控 Unix 用户连接目标。realm、Unix group/DAC、delegated group、Perl 插件和 helper 组成授权扩展点；syslog、SQLite 元数据和 ttyrec 提供审计。项目强调无外部数据库依赖和可做 active/active，但共享密钥、Unix root、syslog 归档和本地文件权限是主要信任边界。它通常不在数据库/Kubernetes wire protocol 层做语义解析。

### 2.3 Warpgate：单二进制多协议网关

Warpgate 是 Rust 单二进制，直接监听 SSH、HTTPS/Web UI、Kubernetes、MySQL、PostgreSQL、RDP 和 VNC 入口；用户在 Web 管理界面把 target 分配给账号，浏览器可作为终端客户端，原生客户端可使用 ticket/配置连接。SQLite 保存用户、target、策略和录制元数据，部署快但多实例共享状态、密钥备份和高可用需额外设计。它的协议覆盖比纯 SSH bastion 广，却不等于 Teleport 的统一 CA、自动资源发现或跨集群信任模型。

### 2.4 Boundary：控制器、Worker 与 session broker

Boundary 将 controller（身份、scope、policy、target）、worker（靠近资源）和 session broker 分开。用户先通过 OIDC/LDAP 等认证，再获准为 target 建立 session；worker 可从 Vault 注入短期 credential。Boundary 关注“谁可以连接哪个 target”以及连接生命周期，目标协议通常作为 opaque stream 传递，命令、query 和 Kubernetes verb 审计应由目标系统或外围工具完成。Controller 数据库、worker credential、Vault/KMS 和 boundary token 构成恢复域。

### 2.5 Pomerium：身份感知 HTTP/TCP 代理

Pomerium 在请求到达 HTTP/HTTPS/TCP upstream 前校验 OIDC/JWT claims、device/context 和 route policy，可向应用注入身份 headers。它适合内部 Web、API、SSH-over-TCP 等零信任入口，但不会解析 SSH PTY、数据库 query、Kubernetes object 或 RDP 帧，也不负责签发目标资源证书。IdP、policy store、TLS secret、proxy 实例和 upstream 本身是故障域。

### 2.6 Guacamole：浏览器远程桌面协议网关

Guacamole 由 Web 应用、连接配置/认证扩展和 `guacd` 协议代理组成，浏览器通过 HTML5 访问 RDP/VNC/SSH/Telnet 等会话。目标凭据通常来自连接定义、LDAP/数据库或 secret extension；`guacd` 可以录制会话，但用户生命周期、审批、不可篡改归档和资源发现要由外围系统补足。它解决“无需安装客户端的桌面访问”，不是完整身份化基础设施控制面。

### 2.7 信任边界和故障域对照

| 平台 | 核心状态与秘密 | 资源侧连接方式 | 目标故障时已有会话 | 审计后端不可用的默认风险 |
| --- | --- | --- | --- | --- |
| Teleport | Auth backend、CA 私钥、录制对象 | Agent → Proxy 反向隧道 | 既有数据流可能继续；新连接需控制面/Agent | sync 可 fail-closed；async 有丢失窗口，必须告警 |
| The Bastion | Unix/realm、共享密钥、SQLite/syslog/ttyrec | Bastion → target | 依赖 SSH 进程；控制面弱故障隔离 | syslog/磁盘故障可能丢记录或阻断，需自定策略 |
| Warpgate | SQLite、ticket/加密密钥、录制文件 | 网关监听并连接 target | 进程存活时可继续；重启/SQLite 故障通常中断 | 录制写盘失败的 fail-open/close 需按版本实测 |
| Boundary | Controller DB、worker credential、Vault/KMS | Worker → target，controller 授权 | worker 存活可维持；token/credential 过期按策略处理 | 事件/log sink 失败通常不等于协议流中断 |
| Pomerium | IdP、policy、TLS secret、session cookie | Proxy → HTTP/TCP upstream | 已建立 TCP/HTTP 流通常由 proxy 进程维持 | access log/metrics 失败不必然阻断请求 |
| Guacamole | 连接库、LDAP/DB、secret、录制盘 | guacd → RDP/VNC/SSH target | guacd 存活可维持；Web/guacd 重启会中断 | 录制失败通常不阻断桌面，需外围 fail-closed |

## 第三章：总体架构

### 3.1 四个逻辑平面

```mermaid
flowchart LR
    Human["人类用户\ntsh / Web UI / Connect"] --> Proxy["Proxy Service\n统一入口 / TLS Routing / Reverse Tunnel"]
    Bot["机器与工作负载\ntbot"] --> Proxy
    Admin["管理员\ntctl"] --> Auth["Auth Service\nCA / 登录 / 动态资源 / Backend"]
    Proxy <--> Auth
    Proxy <--> Agent["Teleport Agent\nSSH / Kube / DB / App / Desktop"]
    Agent --> Resource["目标资源\nLinux / Kubernetes / DB / Web / Windows / MCP"]
    Agent --> Audit["审计事件与录制"]
    Audit --> Auth
```

可以把架构拆成四个逻辑平面：

| 平面 | 核心对象 | 关键职责 | 主要失败后果 |
| --- | --- | --- | --- |
| 身份面 | CA、用户、Agent host identity、Bot identity | 认证、签发、续期、CA 轮换、Trusted Cluster 信任 | 新登录/新连接失败，错误信任根可能扩大到全资源 |
| 控制面 | Auth Service、Backend、动态资源 | 保存 Role、User、Connector、资源库存、锁/请求等状态 | 配置变更、签发和库存更新受阻 |
| 数据面 | Proxy、Reverse Tunnel、各类 Agent | 协议路由、资源连接、部分协议解析 | 已有或新会话中断，资源不可达 |
| 审计面 | 事件 backend、session recording backend、导出器 | 事件检索、录制、回放、SIEM 导出 | “可连接但不可证明”，sync 模式还会主动终止会话 |

逻辑平面不是必须部署成四套进程。Teleport 是单一 Go 二进制，一个进程可以启用多个 Service；生产环境则应按权限、暴露面、扩缩容和故障域把角色拆开。

### 3.2 Auth Service

Auth Service 是信任根和持久状态入口，主要负责：

- 维护用户 CA、主机 CA、JWT CA、数据库/Windows 等签发所需密钥；
- 校验本地用户或 GitHub SSO 登录，生成短期用户证书；
- 保存 Role、User、Join Token、Trusted Cluster、资源定义等动态资源；
- 接收 Agent 心跳、审计事件和会话录制；
- 通过 gRPC API 为 Proxy、Agent、`tctl`、`tbot` 和集成提供控制面服务。

Auth Service 的 backend 不是普通业务缓存。拿到 backend 读写权限往往等价于能接触 CA、用户记录和授权配置；备份介质也应按最高敏感级别加密、限权和审计。

### 3.3 Proxy Service

Proxy Service 是面向客户端和 Agent 的入口：

- 接受 `tsh`、浏览器、原生 SSH、数据库客户端或本地 proxy 的连接；
- 提供 Web UI 和登录 API；
- 通过 ALPN/SNI 做 TLS Routing，常可把多协议收敛到外部 `443`；
- 接收 Agent 建立的反向 SSH 隧道，并按资源地址/集群路由到对应 Agent；
- 在需要时终止 TLS、WebSocket 或 Recording Proxy 流量。

Proxy 被称为“无状态”是指其持久业务状态位于 Auth/backend，不代表它没有高价值的瞬时数据。Web UI cookie、正在转发的明文、Recording Proxy 中的连接材料和流量元数据仍使它成为高优先级攻击面。

### 3.4 Teleport Agent 与资源服务

一个 `teleport` 进程可以启用多个服务：

| Agent Service | 上游资源 | 典型下游协议/身份 |
| --- | --- | --- |
| SSH Service（传统文档也称 Node Service） | 所在 Linux 主机或 OpenSSH 节点 | SSH host/user certificate |
| Kubernetes Service | Kubernetes API Server | HTTPS、impersonation header、ServiceAccount/kubeconfig |
| Database Service | 自托管或云数据库 | PostgreSQL/MySQL/MongoDB 等 wire protocol、mTLS、IAM |
| Application Service | HTTP、TCP、Cloud API、MCP | HTTPS/TCP、JWT/ID token、云签名、MCP transport |
| Desktop Service | Windows 主机 | Teleport Desktop Protocol 到 RDP，证书/智能卡认证 |
| Discovery Service | 云和平台 discovery API | 创建/更新动态资源，不直接等同于数据面代理 |

Agent 既是网络桥，也是授权和审计执行点。把 Agent 部署在资源附近可避免向公网开放目标端口，但 Agent 所在主机因此拥有到目标资源的网络路径和必要凭据，必须用主机权限、ServiceAccount、云 IAM 和网络策略限制其爆炸半径。

### 3.5 客户端分工

| 工具 | 身份对象 | 典型用途 | 安全注意事项 |
| --- | --- | --- | --- |
| `tsh` | 人类交互身份 | 登录、SSH、Kubernetes、数据库、App、MCP、本地 proxy | 私钥和证书保存在客户端 profile；终端失陷仍可能劫持有效会话 |
| `tctl` | 集群管理员 | 读取/写入动态资源、CA 与运维操作 | 通常需直连 Auth 或具管理员身份；不应分发给普通用户 |
| `tbot` | Bot / workload identity | 自动获取并续期 SSH、X.509、JWT、SPIFFE 等输出 | 初始 join 凭据、输出目录权限和续期进程均是信任边界 |
| Teleport Connect / Web UI | 人类交互身份 | 图形化资源访问、Desktop、录制查看 | 浏览器路径由 Proxy 终止并重编码，cookie/浏览器安全更重要 |

### 3.6 反向隧道与 NAT 后资源

默认推荐路径是 Agent 主动拨号到 Proxy，建立反向 SSH tunnel：

```text
用户 -> 公网/L4 LB -> Proxy
                     ^
                     | Agent 主动建立并维持出站 tunnel
                     |
               内网 Agent -> 目标资源
```

这带来三个结果：

1. 用户不需要直接路由到 Agent 或目标资源；
2. 防火墙通常只需允许 Agent 到 Proxy 的出站连接及 Agent 到资源的内网连接；
3. 断网、代理、TLS inspection、ALPN/SNI 过滤或空闲连接回收都可能表现为“资源离线”。

Self-hosted 仍有 direct mode，但只支持部分 Service，且需要 Proxy 直接拨 Agent。官方架构把它定位为 legacy 路径；新部署应优先反向隧道。

### 3.7 单机、拆分和 Kubernetes 拓扑

| 拓扑 | 适用范围 | 优点 | 主要风险 |
| --- | --- | --- | --- |
| 单进程同时启用 Auth/Proxy/SSH | 本地演示、PoC | 配置简单 | 单点故障；公网入口与 CA 共进程；本地 SQLite/录制容量有限 |
| 独立 Auth pool + Proxy pool | 常规生产 | 权限和暴露面分离，可独立扩缩 | 需要共享 backend、两个 L4 入口、TLS/DNS 与备份体系 |
| Kubernetes `teleport-cluster` Helm | 已有成熟 K8s 平台 | 声明式部署、滚动更新、Service/LB 集成 | 不能把 Kubernetes 高可用误当成 backend/CA 高可用；Secret 和 Pod 权限仍要治理 |
| 每个网络域部署资源 Agent | 多 VPC、IDC、边缘 | 仅需出站 tunnel，资源就近访问 | Agent 数量、版本漂移、网络策略和证书轮换复杂度上升 |

### 3.8 Backend、watch 与缓存不是同一层

Auth Service 通过 backend 持久化动态资源，并向 Proxy、Agent 和其他 Auth client 提供 watch/event stream；各 Service 使用本地 cache 减少热路径对 backend 的直接读取并维持资源视图。这里有三个容易混淆的结论：

- cache 命中能改善读延迟，不会把无持久 backend 的多 Auth 部署变成高可用；
- watch 中断后本地组件可能短暂继续使用已有视图，但新 Role、撤销、资源上下线和 CA 状态传播会延迟；
- backend 恢复、cache 重同步和 Agent tunnel 恢复是三条独立链路，健康检查必须分别覆盖。

所以“Proxy 无状态”和“Agent 有缓存”都不意味着控制面可长期离线运行。证书到期、新登录、动态策略传播、同步审计等操作仍需要 Auth/backend 可用。

---

## 第四章：身份、证书与信任链

### 4.1 人类登录链路

```mermaid
sequenceDiagram
    participant U as 用户 tsh / 浏览器
    participant P as Proxy Service
    participant I as Local Auth / GitHub SSO
    participant A as Auth Service / User CA
    participant R as Agent / Resource
    U->>P: 发起登录并提交公钥/认证上下文
    P->>I: 本地密码+MFA 或 GitHub OAuth
    I-->>P: 身份与 traits
    P->>A: 请求签发带 Role/TTL 的身份
    A-->>U: 短期 SSH/X.509 证书或 Web session
    U->>P: 使用短期身份请求资源
    P->>R: 经 tunnel 路由
    R->>R: 验证 CA、有效期、Role 与资源匹配
```

短期证书减少了长期 SSH key、静态 kubeconfig 和数据库密码的分发需求，但不等于无需撤销机制：证书在 TTL 内仍可被滥用，主动安全事件还需要缩短 TTL、终止会话或使用商业锁定能力。

### 4.2 CA 与证书类型

| 身份/用途 | 证书或签名 | 主要验证方 |
| --- | --- | --- |
| SSH 用户和主机 | OpenSSH certificate | Teleport SSH Service、兼容 OpenSSH 服务端/客户端 |
| Kubernetes、数据库、App、内部 Service | X.509 certificate | Proxy、Agent、目标资源或本地 proxy |
| Web/App/MCP 身份透传 | Teleport JWT CA 或 OIDC CA 签名的 JWT | 应用/MCP server 通过 JWKS/OIDC discovery 验证 |
| Agent 内部身份 | 含 host ID、cluster name、system role、expiry 的 host cert | Auth、Proxy 与其他集群组件 |
| Trusted Cluster | Root/Leaf CA 信任与角色映射 | Leaf Auth/Agent |

用户和 Bot 凭据通常短期并由客户端/`tbot` 续期；Teleport 内部 Service 初次加入后得到更长期的主机身份，不能把它与用户短期证书的风险模型混为一谈。内部身份失陷时通常要移除节点并进行 CA 轮换或使用额外的锁定能力。

### 4.3 Community 认证能力边界

| 能力 | v18.10.0 Community 边界 |
| --- | --- |
| 本地用户 | 支持密码与 MFA；密码、MFA 设备元数据位于 Auth backend |
| TOTP | 支持，可作为本地用户第二因素 |
| WebAuthn / FIDO2 / U2F authenticator | 支持作为本地 MFA/Passwordless authenticator；具体平台与浏览器兼容性需验证 |
| GitHub SSO | Community 唯一官方 SSO connector |
| OIDC / SAML | Enterprise；不能因源码中存在类型或文档示例就视为 Community 可用 |
| Per-session MFA | Feature Matrix 标为 Community 可用，可按集群或 Role 要求；协议支持细节不同 |
| Device Trust、IP pinning、硬件私钥强制 | Enterprise，不纳入本文承诺 |

WebAuthn authenticator 能用于 MFA，不等于 Enterprise 的“硬件私钥支持/强制硬件 key-backed client key”能力。两者都可能使用 YubiKey，但保护的密钥、执行位置和授权语义不同。

### 4.4 Agent 与 Bot 的 Join Method

加入集群是给一个尚未受信任的进程签发初始身份，选择错误会把短期证书体系重新退化成长秘密：

| Join Method | 典型环境 | 安全属性 | 生产建议 |
| --- | --- | --- | --- |
| Static token | 旧环境 | 长期可重放秘密 | 官方明确不推荐；只用于受控迁移并尽快删除 |
| Ephemeral token | 通用 | 默认短 TTL，可限制 system role | 最小化 token TTL 和角色；不要写入镜像或 Git |
| `bound_keypair` | 有持久盘的 on-prem/Bot；v18.8 起也可用于 Agent | 首次绑定公钥，后续不重复暴露 bearer secret | 适合不能使用云身份或 TPM 的环境，先核对 Agent 限制 |
| AWS IAM / EC2 | AWS | 以云实例/角色身份证明 | 优先 IAM；限制可加入的 account/role 和 token rules |
| Azure / GCP / Kubernetes / GitHub 等 delegated method | 对应平台 | 使用平台签发的工作负载身份 | 校验 issuer、audience、repository、namespace、ServiceAccount 等条件 |
| TPM | 具备 TPM 的主机/Bot | 设备绑定和硬件保护 | v18 Feature Matrix 将相关 HSM/TPM能力置于商业边界，Community 不作承诺 |

Join Token 不是普通安装参数。泄露的 token 若仍有效，攻击者可能注册具有 `node`、`app`、`db` 等 system role 的 Agent；审计中应监控 `join_token.create` 和新 host identity。

### 4.5 Machine & Workload Identity 与 `tbot`

`tbot` 代表非交互身份，循环执行“证明自身 → 获取短期身份 → 写入 destination → 到期前续期”。Community Feature Matrix 包含基础的机器/工作负载身份签发、轮换、RBAC/ABAC、审计，以及 JWT/SPIFFE/X.509 等开放格式；HSM/TPM bootstrap、外部 PKI issuer override 和 Sigstore attestation 不在 Community 承诺内。

生产落地应明确：

- Bot 是独立身份，不要让它复用人的 `tsh` profile；
- destination 目录只允许目标 workload 读取，避免同节点其他进程窃取证书；
- 输出格式和目标协议的 TTL 必须匹配，不能让下游缓存超过 Teleport 身份寿命；
- `tbot` 退出或网络隔离后，已有短期凭据可能继续有效到过期，但无法续期；
- 初始 join method 与后续凭据是两类不同秘密，必须分别轮换和监控。

### 4.6 Trusted Cluster

Self-hosted Teleport 可以让 root cluster 用户访问 leaf cluster 资源。Leaf 保留自己的 backend、用户、Role 和资源，并通过 role mapping 决定 root 身份能映射成哪些本地权限。

Trusted Cluster 不是简单的跨集群网络隧道：它建立 CA 级信任。官方架构特别提醒，leaf 的 `cluster_labels` 不能替代 role mapping 作为安全边界；持有 root CA 签发证书的用户可能绕过仅用于可见性筛选的 cluster label。应把 root CA、leaf role mapping 和反向 tunnel 一起纳入威胁建模。

---

## 第五章：授权模型与最小权限

### 5.1 Role 的求值规则

Teleport Role 同时表达平台 API 权限、目标身份和资源选择器。核心规则是：

1. 默认拒绝；
2. `deny` 先求值并优先于 `allow`；
3. 多个 Role 的 principals 通常合并，但部分 options 使用 OR、AND 或“最严格值”合并，不能一概视为 union；
4. `allow` 标签集合通常要求所有 key 匹配，`deny` 的标签匹配更贪婪；
5. wildcard、正则和 trait 模板会显著扩大匹配面，应在创建时和真实资源库存上同时测试。

常见资源字段如下：

| 字段 | 控制对象 | 还需要的目标身份/动作 |
| --- | --- | --- |
| `node_labels` | SSH nodes | `logins`、命令/端口转发等 Role option |
| `kubernetes_labels` | Kubernetes clusters | `kubernetes_users`、`kubernetes_groups`、`kubernetes_resources` |
| `db_labels` | Databases | `db_users`、`db_names`、可选数据库对象权限 |
| `app_labels` | Web/TCP/Cloud/MCP apps | MCP 还要 `mcp.tools`；云服务还受云 IAM 约束 |
| `windows_desktop_labels` | Windows desktops | `windows_desktop_logins`、clipboard/directory/recording option |
| `rules.resources` + `verbs` | Teleport 动态资源/API | 控制 list/read/create/update/delete 等管理操作 |

### 5.2 最小权限 Role 示例

下面的 Role 只允许工程师以 `ubuntu` 登录 `env=dev,team=ml` 的节点，只读访问 dev Kubernetes namespace，并调用指定 MCP tool。示例刻意不使用全局 `*:*`：

```yaml
kind: role
version: v8
metadata:
  name: ml-dev-access
spec:
  options:
    max_session_ttl: 4h
    require_session_mfa: true
    forward_agent: false
    ssh_port_forwarding:
      local:
        enabled: false
      remote:
        enabled: false
  allow:
    logins: [ubuntu]
    node_labels:
      env: dev
      team: ml
    kubernetes_labels:
      env: dev
    kubernetes_users: [ml-viewer]
    kubernetes_groups: [viewers]
    kubernetes_resources:
      - kind: pods
        namespace: ml-dev
        name: '*'
        verbs: [get, list, watch]
      - kind: deployments
        api_group: apps
        namespace: ml-dev
        name: '*'
        verbs: [get, list, watch]
    app_labels:
      env: dev
      class: mcp
    mcp:
      tools:
        - search-files
        - '^get_.*$'
  deny:
    node_labels:
      quarantine: 'true'
    mcp:
      tools:
        - delete_*
        - '*write*'
```

上线前至少验证：目标 labels 是否真实存在、无标签资源会怎样、trait 展开为空或多值时怎样、多个 Role 合并后有没有另一个 Role 重新放开端口转发，以及 v18.10 对 Role expression 的创建时校验是否会拒绝旧配置。

### 5.3 Kubernetes 的双层授权

Kubernetes 请求至少经过两层策略：

```text
Teleport Role
  ├─ kubernetes_labels：能选择哪个注册集群
  ├─ kubernetes_users/groups：允许 impersonate 成谁
  └─ kubernetes_resources：Teleport 代理允许哪些 API 对象/verb
                ↓
Kubernetes API Server
  └─ 原生 RBAC / admission / policy：最终是否接受 impersonated user/groups
```

Teleport 允许不代表 API Server 必然允许；Teleport 拒绝时，请求甚至不会到达 API Server。排障时应分别检查 Teleport audit、Role v8 语义、impersonation header 和目标集群 audit/RBAC。

v18.10.0 还有两个具体兼容点：`verbs` 中 `*` 的位置不再影响 wildcard 识别；添加 ephemeral container 需要 `exec` 与 `patch`/`update` 在同一个 Role 的 `kubernetes_resources` 中同时满足。把权限拆到两个 Role 不能假定等价。

### 5.4 Access Request、Session Join 与 Lock 的边界

| 能力 | Community v18.10.0 | Enterprise 边界 |
| --- | --- | --- |
| Access Request | `tsh` 可请求 Role；管理员需在 Auth 上用 `tctl` 审批 | 资源级请求、review rules、可搜索 UI、自动审批和完整 JIT workflow |
| Session Join / sharing | Feature Matrix 将 Session Sharing & Moderation 标为 Community 不可用，不纳入本文承诺 | Observer/Peer/Moderator、`join_sessions` 与 moderated session 工作流 |
| Session/Identity Lock | Feature Matrix 标为 Identity Governance，Community 不可用 | 对 user、role、session、host、MFA device、bot 等发 lock，并终止已有连接 |
| Dual authorization | Community 不可用 | 商业版可要求额外审查/参与者 |

Role schema 或 AGPL 源码里出现 `join_sessions`、`require_session_join`、`lock` 等类型，不代表官方 Community 二进制启用了对应产品能力。本文的 OSS 设计不能把它们当作应急阻断的唯一手段；Community 环境需要准备删除用户/Role、撤销 join token、缩短 TTL、隔离 Agent 和 CA 轮换等替代流程。

### 5.5 常见授权误配

| 误配 | 风险 | 修正方式 |
| --- | --- | --- |
| `'*': '*'` 同时覆盖 prod/dev | 新资源自动继承过宽权限 | 用明确 environment/team/owner labels，并对无标签资源默认拒绝 |
| 允许 `root` 或 `system:masters` 作为日常 principal | 绕过目标侧最小权限 | 创建专用 Unix login、Kubernetes user/group 和数据库 role |
| 只看 allow，不审计 deny 与多 Role 合并 | 实际权限与单文件阅读不同 | 用真实用户身份执行 allow/deny 正反案例 |
| 开启 SSH Agent Forwarding | 远端 root 或恶意进程可借用 agent 签名 | 默认关闭，仅对必须的兼容场景短期开启 |
| 广泛开启端口转发 | Teleport 变成通用内网跳板，协议审计被绕过 | 区分 local/remote forwarding；优先使用对应资源 Service |
| 用可变云标签直接授予高权 | 资源创建者可通过改标签提权 | 保护标签写入面，使用受控 discovery/IaC 和 deny guardrail |
| MCP tool 允许 `*` | 新增危险 tool 自动可用 | allowlist read-only tool，显式 deny 写/删类 tool，并审计参数 |

---

## 第六章：各类资源的访问路径

### 6.1 SSH Server Access

典型链路是 `tsh login` 获取短期 SSH user certificate，客户端连接 Proxy，再经 reverse tunnel 到目标 SSH Service。Agent 验证 user CA、TTL、Role、node label 和 Unix login 后创建 PTY 或执行非交互命令。

| 能力 | 访问/审计特点 | 边界 |
| --- | --- | --- |
| 交互 PTY | 录制终端输出和 resize 等事件 | 记录“用户看到的字节流”，不保证识别所有真实系统调用 |
| 单命令执行 | 产生 exec/session 事件 | 脚本内部命令可能只表现为脚本及其输出 |
| SFTP/SCP | 通过 SSH 通道传输 | 文件内容、路径和协议事件覆盖需按客户端与版本实测 |
| Local/Remote Port Forward | Role option 控制 | 代理只看到隧道，不等同于理解隧道内数据库/HTTP 操作 |
| SSH Agent Forwarding | 可按 Role 允许 | 提高被远端滥用签名能力的风险，Recording Proxy 旧路径尤其敏感 |
| Enhanced Recording | Linux BPF 事件补充进程/网络活动 | 不能阻止具高权限用户卸载探针；daemon、ptrace、内核边界仍有盲区 |

Teleport 与 OpenSSH certificate 兼容，但“兼容 OpenSSH”不等于所有 Teleport 会话控制和录制能力在 agentless OpenSSH 上都完全相同。上线必须按交互、非交互、SFTP、forwarding 和退出状态分别验证。

### 6.2 Kubernetes Access

用户运行 `tsh kube login` 后，本地 kubeconfig 指向 Teleport 并使用短期身份。Kubernetes Service 选择注册集群、校验 Teleport Role、写入允许的 impersonation user/group，再把 HTTPS 请求发往 API Server。

关键审计差异：

- 普通 API 请求产生 Kubernetes request 类事件；
- `kubectl exec` 的交互 PTY 可以录制，风险与 SSH PTY 相同；
- port-forward、attach、exec、ephemeralcontainers 都应做独立用例，不能用 `kubectl get pods` 代表全部；
- 最终 admission、Pod Security、OPA/Kyverno 和原生 Kubernetes audit 仍属于目标集群。

### 6.3 Database Access

`tsh db login/connect/proxy` 获取数据库专用短期证书或启动本地 proxy。Database Service 校验 Teleport identity 和 `db_labels`、`db_users`、`db_names`，再使用目标数据库支持的 mTLS、IAM 或服务凭据连接。

v18.10 官方文档覆盖 PostgreSQL、MySQL/MariaDB、MongoDB、CockroachDB、Redis、SQL Server、云托管数据库等多种协议；Community Feature Matrix 明确不包含 Oracle 支持，因此本文不把 Oracle 放入 OSS 稳定矩阵。

数据库审计不是“全协议录屏”：

- 所有受支持协议可输出 JSON 形式 session 事件；
- PostgreSQL session 可交互回放；
- `db.session.query` 可能包含 SQL 文本和 prepared statement 参数；
- Spanner 等 HTTP/RPC 协议使用专门 RPC 事件；
- 加密 payload、客户端扩展、存储过程内部动作或绕过 Database Service 的直连，不能假设被完整解析。

因此数据库审计仓库本身可能包含口令片段、PII 或业务数据，保留和 SIEM 导出必须做字段分类与访问控制。

### 6.4 Application、TCP 与 Cloud API Access

Application Service 可代理 HTTP、WebSocket 和 TCP 应用。Web 应用路径可把 Teleport-signed JWT 放在默认 `Teleport-Jwt-Assertion` 或管理员指定 header 中；目标应用必须从集群 JWKS 验证 signature、issuer、audience、expiry，不能只相信 header 存在。

TCP app 能把不受 Teleport 原生支持的协议接入统一入口，但会失去上层协议语义。若把数据库作为 generic TCP app，得到的是连接级审计，不应声称等价于 Database Service 的 query 审计。

Cloud API 路径通常由 `tsh proxy aws|azure|gcloud` 启动本地 listener，Application Service 使用 ambient credential、集成或 impersonation 为请求换取/签名短期云身份。Teleport Role 决定“可选择哪个云 app/role”，云 IAM 决定“该身份能对云资源做什么”，二者缺一不可。

v18.10.0 修复了长连接证书续期后反复 403 的问题：证书到期时 Proxy 用 `Connection: close` 促使客户端重建连接。这个修复不会替客户端自动重放非幂等请求，升级验证应区分 GET、stream/WebSocket 和有副作用的 POST。

### 6.5 Git Access 的保守边界

Git 流量可通过 SSH/OpenSSH、HTTPS Application Access 或 TCP app 接入，因而基础 clone/fetch/push 可以复用 Teleport 的网络入口与身份。但 v18.10.0 的专用 GitHub integration 指南同时要求 Teleport Enterprise v17.2+ 和 GitHub Enterprise Cloud；这与顶层 Feature Matrix 把 GitHub 列在 Community protected resources 的宽泛表述并不完全一致。

为避免扩大承诺，本文采用保守判定：

- Community 稳定承诺只包含用已有 SSH/App/TCP 机制保护 Git endpoint；
- 专用 GitHub 组织集成、GitHub SSH CA 自动化或细粒度 repository 映射不作为 OSS 能力；
- GitHub SSO connector 与 GitHub repository access 是两件事，前者是 Community 登录方式，后者要看具体接入实现和 GitHub 许可。

### 6.6 Windows Desktop Access

Desktop Service 把 Teleport Desktop Protocol 转为 RDP，并通过证书/智能卡路径登录 Windows。客户端使用 Web UI 或 Teleport Connect；Desktop Service 需要能访问 Windows `3389` 和相关目录/域服务。

v18.10.0 的 Community 关键边界：

- 可提供屏幕会话录制、clipboard 和 directory sharing 审计；
- local Windows user 的 passwordless access 最多 5 台 desktop；若 `static_hosts` 中 `ad:false` 超过 5 台，Community 会拒绝连接这些主机，而不是只拒绝第 6 台；
- Desktop 录制捕获屏幕变化和鼠标输入，不记录远程桌面的按键流；
- clipboard 事件只记录方向和字节数以避免内容泄漏；directory 事件会记录目录名、相对路径、offset 和长度，但不保存文件内容；
- v18.10 支持一次 RDP session 共享多个目录并单独卸载，应验证卸载后句柄、失败事件和目录 traversal 防护。

Windows 录制以屏幕变化 PNG 为主，容量明显高于终端字节流。1080p 大面积重绘可能产生约 250KB 数据，Desktop Service 本地异步录制目录和对象存储容量都要单独估算。

### 6.7 MCP Access

MCP server 在 v18 Feature Matrix 中是 Community 可用的一等资源。它复用 Application Service，并支持三类 transport：

| Transport | Agent 行为 | 版本/边界 |
| --- | --- | --- |
| stdio | Application Service 以配置的 `run_as_host_user` 启动命令并代理 stdin/stdout | v18.1+；启动命令直接获得 Agent 主机权限，必须隔离 host user/container |
| HTTP with SSE | Agent 建立 SSE 与消息通道 | MCP 2025-03-26 已弃用该 transport，优先迁移 |
| Streamable HTTP | 代理远端 HTTP MCP；`tsh proxy mcp` 可建本地 HTTP listener | v18.3+；适合现代 MCP 客户端 |

客户端先用 `tsh` 的短期身份建立 MCP session，Role 的 `app_labels` 选择 server，`mcp.tools` 对 literal、glob 或正则 tool name 做 allow/deny。未配置 allowed tools 时默认不允许任何 tool。

上游 MCP server 还可验证 Teleport 注入的两种 JWT：

- Classic JWT：由 Teleport JWT CA 签发，通过 `/.well-known/jwks.json` 验证；默认 header 为 `Teleport-Jwt-Assertion`，也可改写为 `Authorization: Bearer {{internal.jwt}}`；
- OIDC ID token：由 Teleport OIDC CA 签发，通过 `/.well-known/openid-configuration` 和 JWKS 验证，可用 `{{internal.id_token}}` 注入。

这两种是 Teleport 到上游 MCP 的 egress identity，不应与用户最初登录 Proxy 的 local/GitHub SSO 流程混淆。

MCP 产生 `mcp.session.start/end/request/notification/listen_sse_stream/invalid_http_request` 等事件。`request` 事件可包含 JSON-RPC method、id 和经过事件化处理的 params；成功的 `ping`、resources/prompts/tools list 等 discovery 调用会被跳过以减噪。因此“每个危险 tool 调用可审计”不等于“逐字记录所有 MCP frame”，也不等于审计 backend 适合存放未经脱敏的 prompt、secret 或 tool 参数。

---

## 第七章：会话记录、审计与数据治理

### 7.1 各协议到底记录什么

| 资源类型 | 结构化事件 | 会话/内容记录 | 关键盲区或敏感性 |
| --- | --- | --- | --- |
| SSH | login、session、exec、file/forwarding 等相关事件 | PTY 输出；可选 BPF enhanced events | 编码命令、脚本内部、daemon/ptrace 等可能不完整；终端可能显示 secret |
| Kubernetes | API request、session、exec 等 | `kubectl exec` PTY | 非 exec API 不是视频；最终行为还需 Kubernetes audit |
| Database | start/end/query/RPC | JSON；PostgreSQL 可交互回放 | query 与参数可能含敏感数据；协议支持粒度不同 |
| Application | `app.session.start`、按 5 分钟 chunk 聚合的 request 事件 | HTTP request stream 的结构化事件，不是页面视频 | generic TCP 只有有限语义；body/header 记录范围需实测 |
| Desktop | session、clipboard、directory read/write 等 | 屏幕变化与鼠标，不记录 keystroke | 容量大；屏幕仍可能显示 secret；clipboard 只记字节数 |
| MCP | session、JSON-RPC request/notification 等 | 协议事件，不是完整录屏 | 部分 discovery 调用减噪跳过；params 可能含 token/PII |

“支持资源”只说明可建立代理连接；“有事件”说明某些阶段可检索；“可回放”才说明存在 session artifact。这三层不能互相替代。

### 7.2 同步与异步录制

Teleport 有 `node-sync`、`node`、`proxy-sync`、`proxy` 四种集群级模式：

| 模式维度 | 语义 | 可用性与完整性取舍 |
| --- | --- | --- |
| sync | 录制组件持续把事件发往 Auth；发不出去视为 fatal | 审计失败会终止会话，适合强合规；依赖低延迟高可用 Auth/backend |
| async | 先写 Agent/Proxy 本地盘，会话后组装上传 | Auth 短暂不可用时会话可继续；本地盘可能满、被删或被篡改 |
| node | SSH 在资源侧录制，Proxy 看不到端到端 SSH 明文 | 降低 Proxy 权限，通常更安全 |
| proxy | Proxy 终止并重建 SSH 连接以录制 | Proxy 可见明文和瞬时 key material；兼容模式有更多限制 |

Windows、Database、Kubernetes 的“node/proxy”最终都由对应 Service 所在 host 录制，因为目标资源上没有 Teleport binary。所有模式可配置录制静态加密，HA Auth 实例必须访问同一 key backend，否则回放可用性会下降。

### 7.3 事件 backend 与录制 backend

三类数据不应混为一个“Teleport 数据库”：

| 数据 | 典型内容 | v18.10 OSS 可用 backend |
| --- | --- | --- |
| Core cluster state | CA、Role、User、Agent/Proxy membership、动态资源 | Local SQLite、etcd、PostgreSQL、DynamoDB、Firestore；CockroachDB 需 Enterprise |
| Audit events | 登录、RBAC 变更、session/query/tool event | Local、PostgreSQL、DynamoDB、S3/Athena、Firestore 等，按 backend 能力配置 |
| Session recordings | PTY、Desktop frame、session artifact | Local、S3/部分兼容实现、GCS、Azure Blob |

etcd 适合 core state，不适合大量时序 audit event；DynamoDB/Firestore 不保存 recording object；S3 不能作为 core state backend。高可用设计必须给三类数据分别选型和演练。

### 7.4 敏感数据治理

最少应定义以下控制：

- 谁能 `list/read` `event`、`session` 和录制对象；
- SIEM 导出是否把 SQL 参数、MCP params、URL query 或用户名扩散到更多系统；
- 对象存储版本控制、WORM/immutability、KMS key、生命周期和 legal hold 策略；
- 本地 async spool 的磁盘加密、容量告警和节点取证流程；
- 录制保留期与业务数据删除/隐私请求之间如何协调；
- NTP/时钟源、cluster name、session ID 和 event index 是否足以跨系统关联；
- 审计系统自身的配置变更、导出失败、backend throttling 和对象上传失败是否告警。

高合规环境应把“审计不可用时拒绝访问”作为显式 SLO，而不是默认认为打开 recording 就已实现 fail closed。

---

## 第八章：部署、高可用与迁移

### 8.1 单机 PoC 的正确用途

单机模式适合验证认证、Role 和资源路径，但不代表生产架构。一个最小概念配置通常同时开启 Auth、Proxy 和 SSH：

```yaml
version: v3
teleport:
  nodename: teleport-poc
  data_dir: /var/lib/teleport
  proxy_server: teleport.example.com:443
auth_service:
  enabled: true
  cluster_name: teleport.example.com
  authentication:
    type: local
    second_factors: [webauthn, otp]
proxy_service:
  enabled: true
  public_addr: teleport.example.com:443
  https_keypairs:
    - key_file: /etc/teleport/tls.key
      cert_file: /etc/teleport/tls.crt
ssh_service:
  enabled: true
  labels:
    env: poc
```

示例不包含 token、私钥或真实域名。不要把 PoC 的 `/var/lib/teleport` 目录、生成的 CA、邀请 token 或 `tsh` profile 提交到 Git。

### 8.2 生产 HA 拓扑

```mermaid
flowchart TB
    Client["tsh / Browser / Native Clients"] --> PublicLB["Public L4 LB\n443 TLS passthrough"]
    PublicLB --> P1["Proxy A"]
    PublicLB --> P2["Proxy B"]
    P1 --> PrivateLB["Private L4 LB\nAuth gRPC 3025"]
    P2 --> PrivateLB
    PrivateLB --> A1["Auth A"]
    PrivateLB --> A2["Auth B"]
    A1 --> State["Shared HA state / audit backend"]
    A2 --> State
    A1 --> Object["Session object storage"]
    A2 --> Object
    AgentA["Agent network A"] --> P1
    AgentA --> P2
    AgentB["Agent network B"] --> P1
    AgentB --> P2
```

官方 HA 架构要求两个冗余 pool：Auth 和 Proxy。Public L4 LB 面向用户/Agent，Private L4 LB 面向 Auth gRPC。LB 应透明转发 TCP 而非终止多协议 TLS；TLS Routing 开启时，多协议通过外部 443 的 ALPN 分流。

### 8.3 DNS、TLS 与网络策略

生产检查项包括：

- `teleport.example.com` 指向所有健康 Proxy；Application Access 需要每应用 DNS 或 `*.teleport.example.com` wildcard；
- TLS certificate 覆盖 cluster public address 和应用域名，并有独立续期/告警机制；
- Public LB 使用 L4/TCP、合理 idle timeout，并保留 ALPN/SNI；企业 TLS inspection 若改写握手会破坏路由；
- Proxy 到 Auth gRPC、Agent 到 Proxy reverse tunnel、Agent 到目标资源、Auth 到 backend/object store 各自有最小网络策略；
- diagnostics `--diag-addr` 只监听受控管理网；`/readyz` 不应直接暴露公网；
- 多可用区部署不够，DNS、LB、backend、object store、KMS 和 CA key backend 也要跨故障域。

### 8.4 Backend、备份与恢复

| 层 | 备份对象 | 恢复验证 |
| --- | --- | --- |
| Cluster state | backend point-in-time snapshot/逻辑备份 | Role/User/CA/Agent inventory 能恢复，新证书可签发 |
| CA key | backend 或外部 key store 中的 CA material | 受控环境验证签发与旧证书兼容，审计每次 key access |
| Audit event | 数据库/table/object 与索引 | 指定时间窗口可查询，event UID/session ID 不丢失 |
| Session recording | object、版本和 encryption key | 能按 session ID 解密回放，不只检查对象存在 |
| Static config | 所有 Auth/Proxy/Agent 的 `teleport.yaml`、Helm values | 多实例 cluster name、storage、token rules 一致且无明文 secret |

`tctl get all` 是配置导出工具，不是完整 backend/CA/recording 备份。恢复演练必须在隔离环境验证 DNS、cluster identity 和证书信任，避免把同一 CA 的测试副本意外接入生产网络。

### 8.5 从 PoC 到生产的迁移清单

1. 固定 `v18.10.0@ddaa46…` 和 Community/源码构建来源，记录 SBOM、hash 与构建参数；
2. 把 Auth、Proxy 和资源 Agent 拆分为独立 service account/OS user；
3. 从单机 SQLite/本地 recording 迁移到受支持的 HA state/audit/object backend；
4. 建立 Public/Private L4 LB、DNS、TLS 续期、NTP 与 diagnostics；
5. 先导入最小 Role 和非生产资源，跑 allow/deny/MFA/audit 用例；
6. 迁移 Agent 时使用短 TTL 或 delegated join，迁移后删除旧 token；
7. 对 SSH、Kubernetes、DB、App、Desktop、MCP 分别验证连接和审计，不以单一 SSH 成功替代；
8. 演练单 Proxy、单 Auth、backend 延迟、object store 拒绝和 Agent tunnel 重连；
9. 演练 backup restore 与 CA rotation，再开放生产用户；
10. 保留旧入口的只读观察期和明确回滚窗口，最后撤销长期 key、旧 kubeconfig 和数据库跳板账号。

迁移不是“装完 Teleport 就立即删除所有旧入口”。在审计和恢复路径尚未验证前同时切断 break-glass，可能把控制面故障放大为全公司失去基础设施访问。

---

## 第九章：安全模型与威胁分析

### 9.1 核心信任资产

| 资产 | 一旦失陷 | 保护重点 |
| --- | --- | --- |
| User/Host/JWT CA private key | 可伪造用户、Agent 或应用身份 | Auth 隔离、backend/KMS 权限、备份加密、CA rotation |
| Auth backend | 可篡改 Role/User/CA/库存和审计 | mTLS、最小 DB/IAM 权限、PITR、写入审计 |
| Proxy | 可劫持登录/路由；某些模式可见明文 | 公网加固、无 shell、及时补丁、限制 Recording Proxy |
| Agent host | 获得到目标资源的网络和服务凭据 | 独立 OS user、只读 FS、SELinux/AppArmor、最小 IAM/SA、网络分区 |
| `tsh` profile / 活跃终端 | 可在证书 TTL 内冒用用户 | 磁盘权限、短 TTL、终端 EDR、MFA、及时登出 |
| Join token / Bot bootstrap | 可注册恶意 Agent/Bot | delegated method、短 TTL、约束 rules、创建/使用审计 |
| Audit/recording storage | 可删除证据或泄漏敏感内容 | WORM、独立管理员、KMS、保留策略、完整性验证 |

### 9.2 典型威胁与缓解

| 威胁 | 形成方式 | 缓解措施 | 剩余风险 |
| --- | --- | --- | --- |
| 长期 SSH key 泄漏 | 历史 key 未撤销 | 用短期 cert 替代、清理 authorized_keys、禁直连 | 有效 Teleport cert/会话仍可在 TTL 内被用 |
| 被盗 Agent identity | Agent 主机或 data dir 失陷 | 隔离主机、重建 host identity、撤销 join path、CA rotation | Community 缺少商业 Lock 时应急粒度更粗 |
| 标签提权 | 低权用户能给资源写 `env=prod` | 将 label authority 与资源 owner 分离、deny guardrail、IaC review | 云 discovery 与业务标签可能发生漂移 |
| Wildcard 过宽 | `'*':'*'`、tool `*` 或正则错误 | 逐资源 allowlist、创建时校验、negative test | 新资源/新 tool 仍可能意外落入范围 |
| 审计绕过 | 端口转发、generic TCP、直连或禁录制 | 关闭 forwarding、网络仅允许 Agent、sync recording、目标侧 audit | 高权限主机用户仍可能干扰观测 |
| Proxy compromise | 公网漏洞、错误 TLS 或 Recording Proxy | L4 passthrough、最小服务、WAF 只放 Web 专用路径、快速补丁 | Web UI 路径仍需要在 Proxy 解密并重编码 |
| MCP prompt/tool 泄密 | 参数被事件记录或 tool 可读取 secret | tool allowlist、参数脱敏、最小上游 scope、独立 MCP host user | 模型/客户端自身仍可能泄露数据 |
| 时钟漂移 | cert 尚未生效或提前过期 | 多源 NTP、漂移告警、统一 UTC | 大范围 NTP 故障可同时影响全部 Service |

### 9.3 Teleport 不替代什么

- **主机加固/EDR。** 获准 SSH 的用户仍在真实主机执行，Teleport 不是执行 Sandbox；
- **Kubernetes API 安全。** Admission、Pod Security、ServiceAccount、etcd encryption 和 API audit 仍由集群负责；
- **数据库原生授权。** Teleport 选择数据库用户/role 后，表、行、存储过程权限仍应由数据库控制；
- **Secrets Manager。** Teleport 管访问身份，不是业务 API key、模型 token 或数据库业务 secret 的通用保管库；
- **通用零信任网络。** 它代理注册资源和部分 TCP endpoint，不是任意东西向网络分段或 SD-WAN；
- **完整 PAM/IGA。** Community 没有完整资源级 JIT、Access List review、Device Trust、Lock 和行为分析；
- **终端安全。** 客户端 malware 可劫持已认证会话，MFA 不能修复被控制的终端；
- **应用授权。** JWT 透传只证明 Teleport 身份，应用仍要验证 token 并执行自己的业务权限。

### 9.4 安全默认值建议

```text
短用户 TTL + WebAuthn/TOTP + per-session MFA（高风险 Role）
明确 labels + 专用 principals + deny guardrail
禁 SSH agent forwarding + 禁不必要 port forwarding
Agent 只出站到 Proxy + 只到指定目标端口
Auth/CA 与公网 Proxy 分池 + backend/object store 最小权限
sync recording（强合规）或加密 async spool（容错优先）
独立 audit 管理员 + SIEM 失败告警 + 定期恢复演练
```

---

## 第十章：运维、升级与故障排查

### 10.1 先按链路定位，而不是盲目重启

```text
Client
  -> DNS / TLS / ALPN / Proxy
  -> Auth login / MFA / CA signing / Role
  -> Reverse Tunnel inventory
  -> Agent authorization / protocol adapter
  -> Target native auth and authorization
  -> Audit backend / session object storage
```

每一跳都要有独立证据。常用只读检查可从以下命令开始：

```bash
teleport version
tsh version
tsh status
tsh ls
tsh kube ls
tsh db ls
tsh apps ls
tsh mcp ls
tctl status
tctl inventory ls
curl --fail --silent http://127.0.0.1:3000/readyz
```

`tctl` 命令需要管理员上下文，不应为了排障临时把管理员凭据复制到普通客户端。日志收集也应在分享前清理 token、cookie、Authorization header、数据库 query 参数和内部域名。

### 10.2 常见故障矩阵

| 现象 | 优先检查 | 常见原因 | 验证方法 |
| --- | --- | --- | --- |
| 登录后立即过期/尚未生效 | Client、Proxy、Auth 时间 | NTP 漂移、TTL/证书 clock skew | 对比 UTC、证书 `notBefore/notAfter`、Auth 日志 |
| Agent 加不进集群 | Join method、token rule、Proxy 地址 | token 到期/角色不匹配、issuer/audience 错、TLS trust 错 | 查看 `join_token.create`、Agent join error、云身份 claims |
| 列表有资源但连接超时 | Proxy tunnel 与 Agent 到目标网络 | tunnel 抖动、LB idle timeout、Agent 防火墙、目标端口关闭 | inventory 心跳、Proxy/Agent 日志、从 Agent 做目标 TCP check |
| `tls: no application protocol` | ALPN 与中间设备 | L7 LB/TLS inspection 删除 ALPN、端口映射错 | 绕过中间层、抓 ClientHello、确认 L4 passthrough |
| App 404/路由错 | SNI/public_addr/DNS | 重复 public address、wildcard DNS/证书不一致 | `tsh apps ls`、Host/SNI、v18.10 duplicate address 修复验证 |
| Kubernetes AccessDenied | 两层 RBAC | Teleport Role 拒绝、impersonation 无权、Role v8/verb 语义 | 对照 Teleport 与 kube-apiserver audit；测 get/exec/ephemeralcontainer |
| DB 能连但 query 无事件 | 协议路径与 audit backend | 走 generic TCP/直连、协议不支持、backend 写失败 | 核对 `db.session.start/query`、连接 endpoint、Event Handler |
| MCP server 可见但无 tool | `mcp.tools` 和 labels | 默认没有 tool、deny 贪婪、trait 为空 | `tsh mcp ls` warning、Role 展开结果、允许/拒绝各测一个 tool |
| Desktop 黑屏/登录失败 | Desktop Service、Windows CA/RDP | CA 未信任、域/KDC/DNS、Community 数量限制 | Desktop audit start failure、Windows event、`ad:false` host 数量 |
| 会话因 audit 中断 | sync recording path | Auth/backend 延迟、IAM 拒绝、对象/事件写失败 | Event/recording error、backend latency、模拟恢复后重试 |

### 10.3 可观测性基线

至少监控：

- Auth/Proxy/Agent `/readyz` 与进程重启；
- Agent inventory 在线率、reverse tunnel 数量和重连频率；
- 登录成功/失败、MFA 失败、证书签发延迟；
- backend request latency、throttling、watch/change-feed lag；
- audit emit error、async spool backlog/磁盘、recording upload error；
- TLS certificate 剩余天数、CA rotation phase、系统时钟偏差；
- 版本分布，尤其是 Auth、Proxy、Agent 与 `tbot` major version 差距；
- Role、User、Connector、Join Token、Trusted Cluster 等高风险资源变更。

告警必须指向可执行 runbook。例如“Agent 离线”要能区分 Proxy 故障、DNS、证书、Agent 进程和目标资源故障，而不是只通知某个主机 ping 失败。

### 10.4 升级顺序与版本兼容

Self-hosted Teleport 的官方顺序是：

```text
备份并验证恢复点
  -> 升级所有 Auth Service
  -> 健康验证
  -> 升级所有 Proxy Service
  -> 健康验证
  -> 升级 Agents / tbot
  -> 按协议回归
```

约束是 Auth 应为最新组件，Proxy 版本不得高于 Auth，Agent 版本不得高于 Proxy。跨多个 major 必须逐个 major 升级，例如 v15 → v16 → v17 → v18，不能直接 v15 → v18。

升级到 v18.10.0 前应额外完成：

- 在隔离/测试 Auth 上提交全部 Role，发现新创建时校验拒绝；
- 检查 Kubernetes wildcard verb 和 ephemeral container Role；
- 统计 Desktop async spool/object storage 容量并复测多目录共享；
- 回归 Application Access 长连接续期和重复 public address；
- 回归 MCP Redshift 路径、tool allow/deny 与审计参数；
- 确认官方 Community binary 与源码构建的 edition/license 没有混装。

### 10.5 回滚边界

Patch 回滚也应先确认 backend schema 和写入兼容。跨 major 安全降级不是简单替换二进制：官方流程要求按升级相反顺序回退非 Auth 组件，停止新 major Auth，将 backend 恢复到升级前时间点，再恢复旧 Auth exact version。

所以真正的回滚前置条件是：

- 有升级前 backend snapshot/PITR，而不只是 YAML；
- 能找回旧版 exact package/source、Helm chart 和配置；
- 录制与事件迁移没有在回滚窗口内切断旧 backend；
- DNS/LB 可以把流量逐步切回；
- break-glass 不依赖正在回滚的 Teleport 控制面；
- 已定义回滚造成的审计窗口、证书重签和 Agent 重连影响。

---

## 第十一章：统一能力矩阵与深入对比

### 11.1 六个平台能力矩阵

下表只使用第一章固定版本中的稳定证据。`原生`表示该版本在产品边界内直接提供；`外围`表示需要目标系统、Vault、IdP、syslog/SIEM 或其它组件；`部分`表示仅覆盖某协议/edition；`主线`和 `不支持` 不得写入稳定兼容承诺。

| 维度 | Teleport | The Bastion | Warpgate | Boundary | Pomerium | Guacamole |
| --- | --- | --- | --- | --- | --- | --- |
| self-hosted 形态 | Auth/Proxy/Agent 多角色 Go 服务；可拆分和 HA | Perl/SSH 入口出口，单机或 active/active；无外部 DB 依赖 | Rust 单二进制，内置 HTTPS/SSH/Kubernetes/DB/RDP/VNC/Web UI | Controller + worker + session broker；状态库和 worker 分离 | Identity-aware HTTP/TCP proxy，可自托管多组件 | guacd + Web 应用；连接配置与外围身份系统分离 |
| 主要协议 | SSH、Kubernetes、数据库、HTTP/TCP、Desktop、MCP | SSH/PTY、SFTP/SCP、网络设备；其它协议靠 helper | SSH、Kubernetes、MySQL、PostgreSQL、RDP、VNC、HTTPS | TCP session brokering；协议理解有限 | HTTP/HTTPS、TCP 应用 | RDP、VNC、SSH、Telnet 等浏览器协议 |
| 是否需要专用客户端 | `tsh` 可选；原生客户端经 proxy/local proxy | 标准 SSH 客户端和 bastion wrapper | 原生 SSH/DB 客户端或浏览器；配置 ticket | Boundary CLI/desktop 连接流程通常需要 | 浏览器、JWT/OIDC 或 TCP client | 浏览器为主；无需目标端客户端 |
| 用户认证/MFA/SSO | Local、GitHub、TOTP/WebAuthn；OIDC/SAML 等按 edition | Unix/LDAP/realm、SSH key；MFA/SSO 由插件或外围 IdP | Local、OIDC/SSO、TOTP（以 v0.28.6 配置为准） | OIDC/LDAP 等 controller auth；MFA 多由 IdP | OIDC、JWT、Pomerium policy/IdP | 可接 LDAP/OIDC/HTTP header；自身不是完整 IdP |
| 机器身份与短期凭据 | CA、短期 cert、`tbot`、JWT/SPIFFE/X.509 | SSH key/Unix account；无统一短期 CA | ticket/target credential；SQLite 保存配置，非 Teleport CA | worker credential、Vault credential injection、短期 session token | 上游 JWT/headers；不签发 SSH/DB cert | 连接凭据由配置/外部 secret 提供 |
| 资源级授权模型 | Role + labels + traits + target principals，目标再授权 | realm、Unix group/DAC、delegated group、命令策略 | user-target 一对一/显式映射、role 与 target 配置 | scope/role、target、session policy；最终凭据在目标/Vault | route policy、identity/group/claim、TCP route | connection 列表/组权限；细粒度资源发现需外围目录 |
| 临时访问/JIT/审批 | Access Request 基础流程；完整 JIT/Access Lists 为商业边界 | delegated group/临时 token 可由插件实现；无统一审批控制面 | ticket 可设过期；无多级审批工作流 | session authorization 与 credential injection；审批需外围工作流 | policy/identity 生命周期；无基础设施 JIT | 无原生 JIT/审批，依赖外围系统 |
| SSH 命令与 PTY 审计 | 原生 command/PTY/exec、session recording | ttyrec/syslog/命令审计，管理员仍可改本地文件 | 录制终端与事件；命令级深度按协议/版本验证 | 连接/会话事件，非 Teleport 级命令解析 | TCP 转发，不理解 SSH 命令 | guacd 录制/日志，命令语义需外围 |
| 数据库协议审计 | Database Service 可记录 query/RPC（支持列表以版本为准） | 不理解 DB wire protocol；仅 SSH 通道 | MySQL/PostgreSQL 代理并记录连接/查询（需按目标配置验证） | 仅 broker/credential 事件；query 审计由 DB | TCP 转发，不解析 query | 不支持原生数据库审计 |
| Kubernetes 访问控制 | Kubernetes Service、impersonation、Role 双层 RBAC | SSH 到 kube 控制节点；无 API 级授权 | Kubernetes proxy 与 user-target 映射；集群 RBAC 仍生效 | 以 target/session broker 连接 API；K8s RBAC 负责最终授权 | TCP/HTTP 入口；不提供 K8s API 资源 RBAC | SSH/RDP 进入管理节点；无 K8s API 控制面 |
| RDP/VNC/浏览器访问 | Desktop Service/RDP；Web UI；Community 数量和功能有限 | SSH 为主；RDP/VNC 需外围 | 原生 RDP/VNC、浏览器 terminal/Web UI | TCP target；桌面协议由客户端/外围处理 | HTTP 应用入口，不是桌面网关 | 原生浏览器 RDP/VNC/SSH |
| 会话录制与回放 | PTY、Desktop、DB/App 事件和对象存储录制 | ttyrec/syslog；保留与完整性由 syslog/文件治理 | 录制与 Web 回放；SQLite/文件权限是边界 | session event；录制深度和查询依赖版本/外围 | HTTP access log/事件；无终端回放 | guacd recording 可回放；不可替代身份审计 |
| SIEM/远程日志导出 | Event Handler、syslog/对象存储、审计 API | syslog 原生，集中归档需运维 | webhook/log sink/文件导出，需配置防篡改归档 | controller/worker logs、audit sink；需外围 SIEM | structured logs、Prometheus、外部 SIEM | guacd/web 日志；外部 SIEM/不可抵赖存储 |
| HA 与状态后端 | Auth backend（SQLite/etcd/PostgreSQL 等）+ Proxy/Agent LB；对象存储录制 | active/active 入口、共享 syslog；本地 SQLite/文件需复制 | SQLite 单点最简单；多实例需共享/复制和 LB 设计 | controller/worker 横向扩展，数据库和 Vault 是状态依赖 | 多实例 proxy + policy/IdP/数据存储 | guacd 可扩展；连接配置/身份库是独立 HA 责任 |
| 反向隧道/NAT 后资源 | Agent 主动出站 Proxy，强项 | bastion 主动连接目标；目标需可达 bastion | Warpgate 监听目标侧端口，NAT 需 LB/端口转发；无 Agent 模型 | worker 可放 DMZ，出站连接 target | proxy 到 upstream 的出站连接 | guacd 到目标出站；浏览器只连 Web |
| 目标系统二次授权 | Unix/K8s/DB/IAM 仍是最终授权 | Unix DAC/group 是核心最终授权 | 目标 SSH/DB/K8s 账号和 RBAC 仍生效 | target 原生账号/Vault secret 最终授权 | 应用自身 RBAC/headers 最终授权 | 目标协议账号/目录服务最终授权 |
| 单点失效与恢复 | CA/backend、Proxy、对象存储分别演练；sync audit 可 fail-closed | 本地状态、syslog、共享密钥和 active/active 一致性 | SQLite/主机磁盘、ticket key、端口配置是恢复重点 | controller DB、worker credential、Vault、KMS 是恢复重点 | IdP、policy store、proxy、证书是恢复重点 | guacd、数据库/LDAP、连接 secret、录制盘是恢复重点 |
| 许可证/商业边界 | AGPL 源码；Community 条件；Enterprise/Cloud entitlement | Apache-2.0 | Apache-2.0 | BSL 1.1，商业条件须复核 | Apache-2.0 | Apache-2.0；本文仅 tag-only 审计证据 |

### 11.2 身份、授权与凭据生命周期

Teleport 的 CA 把用户、主机和 workload 身份绑定到短期证书，Role 的 labels/traits/principals 在 Proxy/Agent 处求值，Kubernetes 和数据库再执行第二层授权。用户注销或证书过期会阻止新连接；已经建立的 SSH/DB/HTTP 会话通常不会因 IdP 注销自动回收，必须用 Lock、目标侧撤销或主动断开。

The Bastion 把 Unix 用户、组和 DAC 当作事实上的授权面：realm/delegation 可以把某些主机或命令交给组管理员，SSH 客户端无需专用协议，但 root、拥有 bastion 主机权限或能直连目标的人仍可绕开记录。它没有 Teleport 式统一 CA 和 workload identity，短期凭据、审批、离职回收依赖 Unix/LDAP、插件和运维流程。

Warpgate 通过用户到 target 的分配、ticket 和内置 Web UI 限制入口，OIDC/TOTP 解决登录强度；但 target 上的 Unix/Kubernetes/DB 账号仍是最终授权，SQLite 中的用户、target、私钥和录制文件是高价值状态。撤销分配通常影响新连接，现有连接是否立即断开应在验收中实测，不能从“ticket 有过期时间”推断全链路强制回收。

Boundary 的核心是“谁可以为哪个 target 建立 session”以及向 worker 注入何种 credential；Vault/目标系统负责秘密和最终权限。它适合把身份化 session broker 接入既有 HashiCorp 栈，不应把 controller policy 等同于 SSH 命令、DB query 或 Kubernetes verb 审计。

Pomerium 以 OIDC/JWT claims 和 route policy 做 HTTP/TCP 入口决策；Guacamole 以连接配置和目录组把浏览器用户映射到 RDP/VNC/SSH 会话。两者都不自动签发基础设施短期证书，也不保证管理员无法读取/修改连接秘密。对于六个平台，必须分别测试：注销、MFA 重置、Role/target 撤销、ticket/证书过期、目标账号禁用、代理进程重启和已有会话行为。

### 11.3 协议、审计与数据治理

“支持 TCP”只表示字节转发，不表示平台理解协议。SSH/PTY 需要区分交互输入输出、`exec`、SFTP/SCP、agent/port forwarding；Kubernetes 需要区分 API verb、`exec`、`port-forward` 与 impersonation；数据库要确认是否解析 query、参数和 TLS；HTTP 要确认只记录 method/path/status 还是也记录 body；RDP/VNC 要确认录制是否能回放而非只保存连接元数据。

录制文件和事件数据库都属于高敏感资产。Teleport 可同步写入事件/录制（后端不可用时中断会话）或异步 spool（短时容错但存在丢失窗口）；The Bastion 的 ttyrec/syslog、Warpgate 的 SQLite/文件、Guacamole 的 guacd recording、Boundary/Pomerium 的日志则需要外部 WORM、对象锁、KMS 和独立管理员来防篡改。管理员能删本地 SQLite/日志或直接登录目标主机时，产品“有审计”并不等于不可抵赖。

对非交互自动化，优先使用短期机器身份、限定 target/principal、禁止 agent forwarding，并把 CI 日志与平台事件用 request/session ID 关联。审计后端不可用的策略必须显式选择：合规环境通常 fail-closed；可用性优先环境可异步降级，但要有 spool 上限、告警和补传验收。

## 第十二章：部署、迁移和验收对比

### 12.1 拓扑和运维成本

PoC 可以把 Teleport Auth/Proxy/Agent、Warpgate 或 Bastion 放在一台受控主机，但生产至少要隔离公网 Proxy/入口、身份控制面、资源侧连接器和审计存储。Teleport 的反向 tunnel 适合 DMZ 后和 NAT 后资源；The Bastion、Warpgate、Guacamole 主要依赖代理到目标的出站可达性；Boundary worker 可放在资源侧，Pomerium 更适合应用入口而非主机跳转。

状态恢复不能只备份 YAML：Teleport 要备份 CA/backend 和录制对象；Warpgate 要备份 SQLite、ticket/加密密钥和 target 配置；The Bastion 要备份 realm/Unix 配置、共享密钥和 syslog；Boundary 要备份 controller 数据库、worker credential、Vault/KMS；Pomerium 要备份 policy/IdP 配置与证书；Guacamole 要备份连接定义、LDAP/数据库和 guacd 录制。每个平台都应做隔离环境恢复、密钥丢失演练和旧客户端兼容测试。

### 12.2 从 OpenSSH/VPN/传统堡垒机迁移

1. 盘点主机、Kubernetes、数据库、应用和桌面清单，标注现有账号、端口、NAT、管理员直连路径与合规录制要求。
2. 先以只读/影子模式建立身份映射：Teleport Role/label、Bastion realm/group、Warpgate user-target、Boundary scope/target、Pomerium route、Guacamole connection group。
3. 为每种协议建立正向、越权、绕过代理、录制失败和目标故障用例；不要以“登录成功”作为迁移完成条件。
4. 双写或镜像审计到独立 SIEM/WORM，验证时间戳、session ID、用户/目标、命令/query 元数据和回放完整性。
5. 分批切换 DNS/LB 和防火墙；先迁移低风险 SSH，再迁移 Kubernetes/DB，最后迁移桌面和自动化。保留受控 break-glass，但对其使用强制双人审批和独立审计。
6. 在确认旧 key/VPN/堡垒机路径已撤销且目标系统仍有原生 RBAC/IAM 后，才删除旧入口。证书、数据库、录制密钥和连接秘密的迁移通常不可逆，应先做恢复演练。

### 12.3 “不要只看功能清单”的决策问题

```text
是否需要短期资源凭据，而不只是一次性网络可达？
是否需要目标协议级审计（命令、query、Kubernetes verb），还是连接日志即可？
是否必须使用原生 SSH/Kubernetes/数据库客户端，能否接受 wrapper 或浏览器？
是否允许资源侧安装 Agent，还是只能由 DMZ worker/guacd 出站？
控制面故障时，已有会话是否允许继续？
审计后端故障时，系统应 fail-open、异步降级还是 fail-closed？
管理员是否可能绕过、读取或删除本地审计与连接秘密？
谁负责目标 Unix、Kubernetes、数据库和应用的最终授权？
```

## 第十三章：场景化选型与组合架构

### 13.1 按场景选择

| 场景 | 首选 | 选择理由与验收重点 |
| --- | --- | --- |
| 多协议基础设施、短期 cert、Kubernetes/DB/App/Desktop 组合 | Teleport | 统一 CA/Role/Agent；验证双层 RBAC、query/PTY 事件、反向 tunnel 和 HA 恢复 |
| 以 SSH/Unix/网络设备为主、标准客户端和低依赖 | The Bastion | Unix DAC/group delegation、syslog/ttyrec；验证 root/直连绕过、active/active 和日志归档 |
| 单二进制、快速部署、浏览器终端、SQLite | Warpgate | user-target assignment、OIDC/TOTP、RDP/VNC/DB；验证 SQLite 备份、ticket 撤销和协议审计深度 |
| 已有 Vault/HashiCorp，希望 session broker/credential injection | Boundary | controller/worker/target 与 Vault 集成；验证目标凭据、worker 故障和外围审计，不要求其替代 Teleport |
| 主要是 HTTP/TCP 应用零信任入口 | Pomerium | OIDC claims、route policy、应用 headers；验证应用自身 RBAC、WebSocket/TCP 和 IdP 故障 |
| 只需浏览器化 RDP/VNC/SSH | Guacamole | guacd + Web UI 部署简单；验证 LDAP/OIDC、连接秘密、录制 WORM 和外围审批 |

### 13.2 组合方式与边界

Pomerium 可保护内部 HTTP 管理面，Guacamole 提供浏览器桌面，Teleport 或 The Bastion 负责基础设施 SSH/数据库运维；Boundary 可在已有 Vault 体系中承担 session broker。组合时必须为每一跳生成可关联的 session ID，并明确哪一个系统是最终审批者、哪一个系统保存录制、哪一个系统能断开会话。不要把多个代理串成无法解释的审计链，也不要因 Pomerium/Guacamole 的登录成功而绕过目标 Kubernetes/数据库/Unix RBAC。

### 13.3 Teleport 的适用与限制（保留的主基线结论）

Teleport 仍是本文的主基线，因为它同时覆盖用户/机器身份、资源侧 Agent、CA、短期证书和多协议审计；下列旧有章节保留其 OSS/Enterprise 边界、与 Kubernetes/KServe/Kubeflow 的组合关系及详细验收清单，并放在跨产品决策之后，避免把 Teleport 的功能优势误写成所有平台的共同能力。

### 13.4 与相邻方案比较

| 方案 | 强项 | 相对 Teleport OSS 的不足/差异 | 更适合 |
| --- | --- | --- | --- |
| OpenSSH Bastion | 简单、成熟、组件少 | 跨协议身份、统一资源库存、数据库/MCP/Desktop 审计需自建 | 仅少量 SSH 主机、团队能严格管 CA/key |
| HashiCorp Boundary | 身份化 session broker、动态 credential 集成 | 具体协议解析、Teleport CA/客户端生态与能力模型不同 | 已有 Vault/HashiCorp 栈、偏 session broker |
| Cloud IAM + SSM/IAP | 云原生、少运维独立控制面 | 多云/on-prem 和跨协议统一性弱 | 单云且资源都能使用厂商原生接入 |
| VPN / Pritunl | 网络接入和网段可达性直接 | 通常不理解资源身份、Role、query/tool/PTY | 需要通用网络连接而非逐资源代理 |
| Kubernetes 原生 RBAC | 最终 API 授权、原生 admission/audit | 不覆盖 SSH/DB/App/Desktop，用户入口和 kubeconfig 生命周期另管 | 单纯 Kubernetes 权限控制 |
| 商业 PAM/IGA | 审批、Access Review、账号托管、合规流程成熟 | 成本、部署复杂度和自动化接口各异 | 需要完整治理、托管账号和审计工作流 |

### 13.5 适合使用 Teleport OSS 的场景

- 同时有 Linux、Kubernetes、数据库、Web/TCP、Desktop 或 MCP，需要统一短期身份入口；
- 资源位于多个私网，愿意部署只出站连接的 Agent；
- 团队能自己运营 CA、backend、对象存储、L4 LB、DNS/TLS 和升级恢复；
- GitHub SSO 或本地 MFA 足够，不依赖企业 OIDC/SAML、Device Trust 和完整 IGA；
- 能接受 Role 请求由 CLI 发起、管理员在 Auth 上用 `tctl` 审批；
- 愿意对目标系统继续维护原生 RBAC/IAM，而不是把 Teleport 当作唯一授权源。

### 13.6 不适合或需要 Enterprise/其他产品的场景

- 必须接 Okta/Entra/通用 OIDC/SAML，并自动 provisioning/deprovisioning；
- 需要资源级 JIT、审批规则、Access List review、自动审批、Dual Authorization；
- 需要 Session/Identity Lock、Device Trust、IP pinning、HSM/FIPS 或商业支持 SLA；
- 需要官方托管控制面、多区域商业 blueprint 或身份威胁分析/session AI summary；
- 需要通用零信任网络、EDR、Secrets Manager、microVM Sandbox 或完整账号密码托管；
- 组织希望使用官方 Community 预编译 binary 但不满足其当期许可条件。

### 13.7 v18.10.0 OSS 与商业边界矩阵

| 能力 | Community / AGPL 源码稳定范围 | 不纳入的商业/产品边界 |
| --- | --- | --- |
| 核心控制面 | Self-hosted Auth、Proxy、Agent、SQLite/etcd/PostgreSQL/DynamoDB/Firestore、对象录制存储 | Teleport Cloud 托管、多区域 CockroachDB backend |
| 用户身份 | Local、GitHub SSO、TOTP/WebAuthn、passwordless、per-session MFA | OIDC/SAML、SCIM、Device Trust、IP pinning、硬件私钥策略 |
| 资源访问 | SSH、Kubernetes、Database、App/TCP、Cloud API、MCP、有限 Desktop；Oracle 除外 | Oracle、专用 GitHub 集成按其 Enterprise 指南处理 |
| 机器身份 | 基础 `tbot` 签发/续期、JWT/SPIFFE/X.509、RBAC/审计 | TPM/HSM bootstrap、外部 PKI、Sigstore attestation |
| 授权 | Role/labels/traits/deny、Kubernetes resource、MCP tool | Access Lists、资源级 JIT、自动审批、完整 review rules |
| 会话控制 | 录制、回放、protocol event、SIEM export | Session Sharing/Moderation、Dual Authorization、Lock |
| 安全分析 | 原始事件和录制由运营方分析 | Access Graph、Identity Security、session summary/search、行为检测 |

### 13.8 与本仓库其他主题的组合

- Teleport 可以统一进入 Kubernetes 集群，但 [Kubernetes-Native-Scheduler-Deep-Dive.md](Kubernetes-Native-Scheduler-Deep-Dive.md) 和各 AI scheduler 仍决定工作负载如何调度；
- Teleport 可以保护 KServe/Kubeflow 管理 API 和内部 Web UI，但不替 KServe 的流量路由、模型 runtime 或 Kubeflow 多租户控制；
- Teleport MCP Access 约束 tool 身份和审计，Multica 负责 coding agent 协作编排，二者都不自动提供 Sandbox；
- Teleport 进入 E2B 管理面不等于 Teleport 提供 Firecracker 隔离，执行安全边界仍应由 E2B/Agent Sandbox 或其他 runtime 提供；
- Teleport 访问 GPU 节点不替 GPU Operator、HAMi、Kueue 或 Volcano 做设备管理和调度。

### 13.9 结论

Teleport OSS 最有价值的能力是把多协议访问统一到同一组 CA、短期证书、Role、资源标签、反向隧道和审计链路中。它减少长期 key 分发，并让基础设施访问从“先获得网络可达性”变成“先证明身份、再获取短期资源权限”。

它的生产成本也很明确：团队必须自己守住 Auth/CA、Backend、Proxy、Agent、DNS/TLS、录制和升级恢复；Community 又缺少完整身份治理与主动锁定。正确选型不是只看“能否连接”，而是逐协议验证：

```text
身份是否可信
  + Role 是否最小
  + 目标系统是否再次授权
  + 访问是否只能走受控路径
  + 审计失败时系统如何处置
  + 控制面故障后能否恢复
```

只有这六项都有可重复证据，Teleport 才从一个方便的代理入口变成可信的基础设施访问控制面。

---

## 附录 A：生产验收用例

| 类别 | 正向用例 | 负向/故障用例 | 通过条件 |
| --- | --- | --- | --- |
| 登录 | Local/GitHub + MFA 获取短期 cert | 错误 MFA、过期 cert、时钟偏差 | 正确事件、明确拒绝、TTL 与配置一致 |
| SSH | 允许 node/login 的 PTY 和 command | 错 label、root、forwarding | 允许最小路径，拒绝不留 tunnel，录制可回放 |
| Kubernetes | get/list 指定 namespace | exec、port-forward、ephemeralcontainer 越权 | Teleport 和 K8s 两层 audit 可关联 |
| Database | 指定 db/user 查询 | 错 db_name、直连、敏感参数 | Role 拒绝正确；query event/脱敏策略符合预期 |
| App | HTTP/WebSocket 与证书续期 | 重复 public addr、过期长连接 | v18.10 重连正常，无无限 403；非幂等请求不误重放 |
| Desktop | 连接、clipboard、多个目录 share/unmount | 第 6 台 local desktop、禁止 clipboard/record | Community 限制和 Role option 如预期，事件不含 clipboard 内容 |
| MCP | allowlist tool、JWT 验证 | 默认无 tool、deny tool、伪造 JWT | tool 拒绝发生在上游前；method/params 审计符合数据策略 |
| HA | 单 Proxy/Auth/Agent 故障 | backend throttling、object store deny | LB 摘除、tunnel 重连、sync/async 行为与 runbook 一致 |
| 恢复 | backend + CA + object 恢复 | 丢 encryption key、旧 DNS 接入 | 隔离环境可签发和回放，错误副本不会接入生产 |
| 升级 | Auth→Proxy→Agent 到 v18.10 | Role 校验失败、需要 major rollback | 每阶段有 gate，恢复点和旧 exact artifact 可用 |

---

## 附录 B：固定版本、许可证与官方来源

### B.1 Release 与源码

- GitHub Release：<https://github.com/gravitational/teleport/releases/tag/v18.10.0>
- Exact source：<https://github.com/gravitational/teleport/tree/ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d>
- AGPL 源码许可证：<https://github.com/gravitational/teleport/blob/ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d/LICENSE>
- Community binary license：<https://github.com/gravitational/teleport/blob/ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d/build.assets/LICENSE-community>
- v18.10.0 Feature Matrix：<https://github.com/gravitational/teleport/blob/ddaa46b8f4ee579d43480cd2d3b6a14b18e3ef7d/docs/pages/feature-matrix.mdx>

#### B.1.1 The Bastion

- Release：<https://github.com/ovh/the-bastion/releases/tag/v3.24.01>
- Exact source（lightweight tag）：<https://github.com/ovh/the-bastion/tree/30c8b522ddd9db2993e22b05b0ee19f961cadf1d>
- Apache-2.0 license：<https://github.com/ovh/the-bastion/blob/30c8b522ddd9db2993e22b05b0ee19f961cadf1d/LICENSE>
- Architecture and installation：<https://ovh.github.io/the-bastion/>
- Configuration/reference：<https://github.com/ovh/the-bastion/tree/30c8b522ddd9db2993e22b05b0ee19f961cadf1d/doc>

#### B.1.2 Warpgate

- Release：<https://github.com/warp-tech/warpgate/releases/tag/v0.28.6>
- Exact source（lightweight tag）：<https://github.com/warp-tech/warpgate/tree/525c7caf2219d5f5e3913b5732e4cbad5d15cd34>
- Apache-2.0 license：<https://github.com/warp-tech/warpgate/blob/525c7caf2219d5f5e3913b5732e4cbad5d15cd34/LICENSE>
- Documentation/configuration：<https://warpgate.null.page/>
- Protocol and web UI source：<https://github.com/warp-tech/warpgate/tree/525c7caf2219d5f5e3913b5732e4cbad5d15cd34>

#### B.1.3 Boundary

- Release：<https://github.com/hashicorp/boundary/releases/tag/v0.21.3>
- Exact source（lightweight tag）：<https://github.com/hashicorp/boundary/tree/8c9715c868537616a11e0ea555b20042e212bdbc>
- BSL 1.1 license text：<https://github.com/hashicorp/boundary/blob/8c9715c868537616a11e0ea555b20042e212bdbc/LICENSE>
- Architecture/session brokering：<https://developer.hashicorp.com/boundary/docs/concepts>
- Connect to targets and worker brokering：<https://developer.hashicorp.com/boundary/docs/getting-started/connect-to-target>

#### B.1.4 Pomerium

- Release：<https://github.com/pomerium/pomerium/releases/tag/v0.33.1>
- Exact source（lightweight tag）：<https://github.com/pomerium/pomerium/tree/01af7466fa3b26b5e5369df49f367737d81ad18e>
- Apache-2.0 license：<https://github.com/pomerium/pomerium/blob/01af7466fa3b26b5e5369df49f367737d81ad18e/LICENSE>
- Architecture and routes：<https://www.pomerium.com/docs>
- Authentication capabilities：<https://www.pomerium.com/docs/capabilities/authentication>

#### B.1.5 Guacamole

- Project release page：<https://guacamole.apache.org/releases/>
- Server `1.6.0` tag-only exact source：<https://github.com/apache/guacamole-server/tree/1f664e08feae6e7d15d8146b78acab2e6fb470ae>
- Client `1.6.0` tag-only exact source：<https://github.com/apache/guacamole-client/tree/0537c89cd783681b986ff8f8c4e0b97ec6873371>
- Apache-2.0 license（server）：<https://github.com/apache/guacamole-server/blob/1f664e08feae6e7d15d8146b78acab2e6fb470ae/LICENSE>
- Architecture and protocol support：<https://guacamole.apache.org/doc/gug/>
- Authentication extensions：<https://guacamole.apache.org/doc/gug/jdbc-auth.html>

### B.2 架构、部署与升级

- 官方架构：<https://goteleport.com/docs/reference/architecture/>
- Agent architecture：<https://goteleport.com/docs/reference/architecture/agents/>
- Authentication：<https://goteleport.com/docs/reference/architecture/authentication/>
- Authorization：<https://goteleport.com/docs/reference/architecture/authorization/>
- Session recording：<https://goteleport.com/docs/reference/architecture/session-recording/>
- Storage backends：<https://goteleport.com/docs/reference/deployment/backends/>
- High Availability：<https://goteleport.com/docs/admin-guides/deploy-a-cluster/high-availability/>
- Upgrade overview：<https://goteleport.com/docs/upgrading/overview/>

### B.3 资源与访问控制

- Role reference：<https://goteleport.com/docs/reference/access-controls/roles/>
- Kubernetes Access controls：<https://goteleport.com/docs/enroll-resources/kubernetes-access/controls/>
- Database Access：<https://goteleport.com/docs/enroll-resources/database-access/>
- Application Access：<https://goteleport.com/docs/enroll-resources/application-access/>
- Desktop Access：<https://goteleport.com/docs/enroll-resources/desktop-access/>
- MCP Access：<https://goteleport.com/docs/enroll-resources/mcp-access/>
- Community Role Access Requests：<https://goteleport.com/docs/identity-governance/access-requests/oss-role-requests/>

### B.4 证据解释规则

1. Release 页面证明正式发布状态与 release note；
2. lightweight tag 直接 commit `ddaa46…` 定义本文源码边界；
3. Feature Matrix 和具体功能页共同判定 edition，冲突时采用更保守边界；
4. 源码中存在类型、API 或 Enterprise stub，不自动证明 Community binary 可用；
5. The Bastion/Warpgate/Boundary/Pomerium 的 lightweight tag 直接 commit 是源码边界；Boundary 的 BSL 不是 Apache-2.0，不能沿用“开源”简称；
6. Guacamole 的 `1.6.0` 只有 tag-only exact source、审校日无 GitHub Release；它是可复核的源码边界而非厂商 Release 兼容承诺，正式发行包出现后必须重新核对 server/client 两个仓库和协议矩阵；
7. `master`、`v19.*-dev.*`、Teleport Cloud 行为、商业插件和其它平台的 SaaS/Enterprise 功能不扩大本文固定版本兼容承诺；
8. 许可条款、SSO/MFA 和高级审计能力可能变化，生产使用应在获取源码或二进制时重新审查对应文件，并让法务/采购复核商业条件。
