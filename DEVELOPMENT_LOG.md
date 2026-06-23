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
