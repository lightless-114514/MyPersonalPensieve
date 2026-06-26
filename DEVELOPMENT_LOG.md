## 2026-06-25 — 思维导图修复多连通分量丢失 & 长词条截断 & 首页动态问候语

### 思维导图多连通分量丢失

根因：`buildHierarchy()` 从最连通节点（Vue3）出发做 BFS 建树。HTML→DOM模板→...→userName 链是一个独立连通分量（与 Vue3 无直连边），BFS 遍历不到，但它们又不是孤立节点（内部有边），整条链被丢弃。

修复：BFS 结束后扫描未访问的连通节点，对每个剩余分量单独建 BFS 树，作为虚拟根的独立子分支（与 Vue3 并列）。

### 长词条截断

根因：`Eduardo San Martin Morote`、`Object.defineProperty` 等长词在树上垂直间距不够，挤在一起。

修复：
- 名称超过 14 字符自动截断为 `前13字符…`
- 每个节点添加 `<title>` 元素，鼠标悬停显示完整名称
- 节点间距从 `1:1.5` 加大到 `1.2:1.8`

### 首页动态问候语

新增 `frontend/src/composables/useGreeting.ts`，按时间段随机抽取问候语：
- 早上 (6:00-12:00)：3 种
- 下午 (12:00-18:00)：3 种
- 晚上 (18:00-23:00)：3 种
- 凌晨 (23:00-6:00)：3 种

首页标题从固定"你的第二大脑"改为动态 `{{ greeting }}`。

## 2026-06-25 — 思维导图孤立节点修复（独立根节点）

### 理由

知识图谱的思维导图模式下，孤立节点（如 `橘福福`，来自"绝区零"记忆，与 Vue3 无任何关联）被错误地归入 Vue3 下方的"其他"容器，看起来像是 Vue3 的子节点。用户希望孤立节点作为**独立根节点**，与 Vue3 平级展示。

### 根因

- `buildHierarchy()` 将孤立节点统一塞进 `__isolated__`（"其他"）容器，再挂到主树根（Vue3）的 children 下
- 这样孤立节点变成 Vue3 的二级子节点，语义错误

### 前端修复

- `frontend/src/pages/GraphPage.vue`：
  - `buildHierarchy()` 不再创建"其他"容器。改为返回一个**虚拟根节点** `__virtual__`，其 children 为 `[Vue3树根, 橘福福, ...其他孤立节点]`，让孤立节点与 Vue3 平级成为独立分支
  - `renderTree()` 隐藏虚拟根节点（圆点 r=0、文字 opacity=0），并过滤掉从虚拟根出发的连线（`root.links().filter(l => l.source.data.id !== '__virtual__')`），用户只看到 Vue3 和 橘福福 两个独立树
  - 自动居中计算排除虚拟根节点，避免它影响边界框
  - 根节点圆点半径判断从 `d.depth === 0` 改为 `d.depth === 1`（因为虚拟根占了 depth 0）

### 验证

- 思维导图模式：49 个圆点（1 个 r=0 虚拟根隐藏 + 2 个 r=10 独立根 `Vue3`/`橘福福` + 46 个 r=6 子节点）
- `Vue3` 和 `橘福福` 在同一 x 坐标，确认两者深度相同、互为兄弟
- 力导向图模式不受影响，`橘福福` 仍是单独的悬浮节点

## 2026-06-23 — 接入 DeepSeek v4-flash & 精简记忆类型

### 理由

国产 API（DeepSeek）在中文场景表现更好，且 OpenAI 兼容协议使得切换成本极低。同时精简记忆类型，语音和链接目前没有实现路径，保留只会造成混淆。

### LLM 接入变更

- `config.py`：默认 provider 改为 `deepseek`，默认模型 `deepseek-v4-flash`
- `llm_service.py`：新增 `PROVIDER_DEFAULTS` 字典，根据 provider 自动选用 base_url 和模型
  - DeepSeek: `https://api.deepseek.com` + `deepseek-v4-flash`
  - 前端设置页填入 API Key 后自动持久化到 localStorage，axios 拦截器自动附加 `X-API-Key` 头
- `.env.example`：精简为仅 DeepSeek 配置示例

### 记忆类型精简

移除 `AUDIO`（语音）和 `LINK`（链接），仅保留 `TEXT` 和 `IMAGE`：
- `models/memory.py`：MemoryType 枚举只保留 TEXT / IMAGE
- `frontend/src/types/index.ts`：type 字段类型同步精简
- `frontend/src/lib/utils.ts`：typeIcon 只保留 TEXT / IMAGE
- `frontend/src/pages/MemoriesPage.vue`：下拉选项和 LINK 专属输入框已移除

# MyPersonalPensieve - 开发日志
## 2026-06-24 — 修复知识图谱与情感分析（接入实体提取）

### 理由

知识图谱和情感分析页面始终为空。根因是后端创建记忆时从未调用 LLM 实体提取，`KnowledgeEntity`、`Relation`、`Memory.sentiment` 始终无数据。

### 根因

- `memory_service.create()` 只做了 embedding，没有调用 `llm_service.extract_entities()`
- `llm_service` 使用 `with_structured_output()`，DeepSeek 不兼容 OpenAI parse 端点，静默失败
- LLM 调用无超时保护，网络不通时会卡住整个请求

### 后端修复

- `memory_service.py`：
  - 新增 `_process_background()`，创建记忆后自动提取实体、情感、生成 embedding
  - 实体写入 `KnowledgeEntity` 表，记忆与实体关联写入 `MemoryEntity`
  - 连续实体间创建 `Relation`（co-occurrence 关系），知识图谱有连线
  - 情感写入 `Memory.sentiment`，情感分析页面有数据
  - 使用独立 session（`async_session_factory()`）避免 greenlet 错误
- `llm_service.py`：
  - `extract_entities()` 从 `with_structured_output()` 改为 JSON 字符串解析（DeepSeek 兼容）
  - prompt 使用 jinja2 转义 `{{}}` 避免 LangChain 模板变量冲突
  - 新增 `openai_proxy` 支持 VPN 代理环境
  - `extract_entities` 和 `generate_embedding` 均加 `asyncio.wait_for` 超时保护（20s/15s）

### 测试

- 生成 8 条 Vue3 知识记忆（Composition API、响应式原理、组件通信、Vue Router、生命周期、Pinia、Teleport/Suspense、性能优化）
- 实体提取成功：59 个节点、65 条关系（Vue3、Evan You、Composition API、Pinia 等）
- 情感分析：6 条 NEUTRAL、5 条 POSITIVE，趋势图正常渲染

## 2026-06-24 — 修复标签选择器（下拉不显示 / 无法添加 / 输入卡顿）

### 理由

标签功能此前完全不可用：下拉框不显示任何标签、无法选择已有标签、输入框偶尔无法输入。根因是 vue-query 的 Ref 解包问题以及下拉框使用了未定义的 Tailwind 颜色类。

### 根因

- `suggestions` computed 中直接对 `allTags`（vue-query 返回的 **Ref 对象**）调用 `.filter()`，等于在 Ref 上调用数组方法，抛出 `TypeError` 导致建议列表永远为空
- 下拉框使用了 `bg-popover` 颜色类，但 `tailwind.config.js` 未定义 `popover` 颜色，背景透明导致看不见
- `queryKey` 使用了静态的 `tagText.value`，搜索时不会触发重新查询

### 前端修复

- `frontend/src/pages/MemoriesPage.vue`：
  - computed 改为 `allTags.value` 先解包 Ref 再 `.filter()`，标签列表正常显示
  - `queryKey` 改为静态 `['tags']`，一次性加载全部标签，搜索改为本地即时过滤（`toLowerCase().includes()`）
  - 下拉框背景从 `bg-popover` 改为 `bg-card`（已定义的颜色类）
  - 回车添加标签时用 `[...selectedTags]` 批量赋值，减少重渲染次数
  - 点击标签容器时调用 `openTagDropdownAndFocus` 确保 input 获得焦点
  - 新增 `staleTime: 30_000` 避免短时间内重复请求

### 后端修复

- `backend/app/services/memory_service.py`：
  - 标签创建改为 `memory.tags.append(mt)` 直接挂到关系列表，确保 `commit` 后 `_to_response` 能取到标签
  - 移除无效的 `db.refresh(memory, attribute_names=["tags"])`（`attribute_names` 不支持 relationship 字段）

### 附带修复

- `frontend/src/lib/utils.ts`：修复 emoji 和中文相对时间显示乱码（`??` → `📝`、`刚刚`、`分钟前` 等）
- `frontend/src/pages/HomePage.vue`：首页按钮文案根据有无记忆动态切换
- `frontend/src/types/index.ts`、`frontend/src/api/index.ts`：新增 `TagItem` 类型和 `getTags()` API


## 2026-06-23 — 重构为 Electron 桌面应用（SQLite + ChromaDB）

### 理由

Docker 微服务架构对终端用户部署门槛太高（需要装 Docker、启动 3 个容器）。改为 Electron 单体桌面应用，用户双击即可运行，数据本地存储，零配置。

### 架构变更

| 组件 | 之前 | 之后 |
|------|------|------|
| 数据库 | MySQL 8.0 (Docker) | SQLite (aiosqlite，嵌入式) |
| 向量存储 | Qdrant (Docker) | ChromaDB (本地持久化) |
| 缓存 | Redis (Docker) | 内存缓存 (同接口，无外部依赖) |
| 部署方式 | docker compose | Electron + PyInstaller 单体打包 |
| 前端 | Vite dev server | 支持 dev (proxy) + desktop (完整 URL) 两种模式 |

### 新增文件

| 文件 | 说明 |
|------|------|
| electron/main.js | Electron 主进程：启动后端子进程 + 创建窗口 |
| electron/preload.js | 预加载脚本，暴露 window.pensieve 环境信息 |
| electron/package.json | electron-builder 配置（NSIS 安装包 + portable） |
| electron/scripts/build.js | 一键构建脚本（前端 + 后端 + 打包） |
| backend/run.py | PyInstaller 打包入口，输出 PENSIEVE_STARTING 信号 |
| backend/pensieve_backend.spec | PyInstaller spec（含 ChromaDB 隐式依赖收集） |
| frontend/.env.development | 开发模式 API base 配置 |

### 后端改动

- config.py：新增 _default_data_dir() 自动解析数据目录（开发模式 backend/data，打包后可执行文件同级 data）
- db/session.py：SQLite 连接参数 check_same_thread=False；新增 init_db() 首次启动自动建表（替代 alembic migrate）
- main.py：lifespan 中调用 init_db() + ensure_collection()
- qdrant_service.py：整文件改为 ChromaDB 实现，保持方法签名不变
- redis_service.py：整文件改为内存缓存实现（_MemoryStore），保持方法签名不变
- pyproject.toml：依赖从 asyncmy/pymysql/redis/qdrant-client 换为 aiosqlite/chromadb，dev 加 pyinstaller

### 前端改动

- api/index.ts：baseURL 改为 import.meta.env.VITE_API_BASE || '/api'，支持桌面端完整 URL
- env.d.ts：声明 ImportMetaEnv 和 window.pensieve 类型
- package.json：build 去掉 vue-tsc -b（加快构建），新增 build:strict

### .gitignore 更新

排除 build 产物：frontend/dist/、*.tsbuildinfo、vite.config.js/d.ts、backend/build/、backend/dist/、electron/release/

### 数据流（桌面端）

Electron main.js 启动后 spawn pensieve_backend.exe (PyInstaller 打包的后端)，通过 uvicorn 运行 FastAPI 服务读写 SQLite + ChromaDB。前端由 BrowserWindow 加载静态文件，axios 请求发往 127.0.0.1:8080/api。

### 当前状态

- 桌面端架构搭建完成
- 后端服务接口不变，业务层零改动
- 打包流程就绪（electron/scripts/build.js）
- 待后续：实际打包测试 + 桌面端 UI 适配

---

## 2026-06-17 — 前端对接真实 API + 设置页修复 + 新增后端端点

### 前端改动

| 文件 | 改动 |
|------|------|
| api/index.ts | createMemory 改 JSON 体；searchMemories 改为 getMemories (GET)；新增 getRecentMemories；添加 axios 拦截器自动 snake_case→camelCase |
| types/index.ts | 对齐后端 PagedResponse (total_elements, total_pages) 和 MemoryResponse |
| HomePage.vue | 改用 getRecentMemories 取真实数据 |
| MemoriesPage.vue | 改用 getMemories + createMemory(JSON)；移除 FormData 上传 |
| SettingsPage.vue | 修复暗色模式切换按钮：translate-x-[22px] 替代不在 Tailwind 间距表的 translate-x-5.5；加 overflow-hidden |

### 后端新增端点

| 端点 | 说明 |
|------|------|
| GET /api/graph | 返回实体 + 关系的知识图谱数据 (D3.js 可视化) |
| GET /api/analytics/sentiment | 按日期聚合情感趋势（支持 ?days=7/30/90） |

### 数据流

Vue 3 页面通过 Vue Query → axios → Vite proxy (/api → :8080) → FastAPI → SQLAlchemy → MySQL

### 当前状态

- 前端 6 个页面全部对接真实后端 API
- 暗色模式切换按钮动画修复
- 记忆 CRUD（创建/列表/详情/删除）全部走 MySQL
- 图谱和情感分析端点就绪，等待 AI 实体提取数据填充

---

## 2026-06-16 — 后端重构：Spring Boot (Java) → FastAPI (Python)

### 理由

部分功能（如 LLM 集成、向量搜索、AI 代理）在 Python 生态中更成熟，Java 的 LangChain4j 等库版本滞后、社区支持较弱。尝试 Python 技术栈，利用 FastAPI + LangChain + Qdrant 的原生 Python 客户端，降低 AI 相关功能的接入成本。

### 完成事项

| 事项 | 说明 |
|------|------|
| 创建 python-main 分支 | 默认分支，java 分支保留 Spring Boot 旧版 |
| 删除所有 Java 文件 | backend/src/main/java/ + pom.xml |
| Web 框架 | Spring Boot → FastAPI (异步) |
| ORM | JPA/Hibernate → SQLAlchemy (异步模式) |
| 数据库迁移 | ddl-auto:update → Alembic |
| Redis | Jedis/Lettuce → redis-py 异步 |
| Qdrant | Java Client → qdrant-client (Python) |
| LLM | LangChain4j → LangChain (Python) + OpenAI |
| Dockerfile | Java 17 → Python 3.12-slim |
| docker-compose.yml | 新增 backend 构建服务 |

### API 接口（完全兼容前端）

| 方法 | 路径 | 状态 |
|------|------|------|
| POST | /api/memories | OK |
| GET | /api/memories | OK 分页 |
| GET | /api/memories/recent | OK |
| GET | /api/memories/{id} | OK |
| DELETE | /api/memories/{id} | OK |
| GET | /api/health | OK |

### 服务容错

- OpenAI 客户端：懒加载，无 API key 时不影响启动
- Qdrant 客户端：懒加载，未连接时不影响启动
- Redis 操作：try/except 包裹，未运行时优雅降级（跳过限流/缓存）

---

## 2026-06-15 — 前端 Vue 3 搭建 + 后端 Spring Boot 初版 + 基础设施

### 前端

| 事项 | 说明 |
|------|------|
| 启动前端 | npm run dev → localhost:5173 |
| 浏览全部页面 | 首页 / 记忆 / 记忆详情 / 知识图谱 / 情感分析 / 设置 |
| 确认路由结构 | 6 个页面，左侧导航 + 暗色模式切换 |

### 后端

启动并修复 7 个问题（BOM 编码、Entity 类名冲突、H2/MySQL 方言、JDBC 字符集等），最终在 MySQL 生成表结构：

- memories（记忆主表）
- entities（知识实体）
- memory_entity（多对多关联）
- relations（实体关系）

集成 Redis 缓存/限流/任务步骤功能。

### 基础设施

| 服务 | 地址 | 状态 |
|------|------|------|
| 前端 Vue 3 | localhost:5173 | OK |
| 后端 Spring Boot | localhost:8080 | OK MySQL 持久化 |
| MySQL | localhost:3306 | OK 本机 |
| Redis | localhost:6379 | OK Docker |
| Swagger | localhost:8080/swagger | OK |
