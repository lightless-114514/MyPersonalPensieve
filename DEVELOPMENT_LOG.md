# 🧠 MyPersonalPensieve — 开发日志

> 2026-06-15 ~ 2026-06-16

---

## 一、前端 (Vue 3 + Vite + Tailwind CSS)

### 做了什么

| 事项 | 说明 |
|------|------|
| 启动前端 | `npm run dev` → `localhost:5173` |
| 浏览全部页面 | 首页 / 记忆 / 记忆详情 / 知识图谱 / 情感分析 / 设置 |
| 确认路由结构 | 6 个页面，左侧导航 + 暗色模式切换 |

### 遇到的问题

| 问题 | 解决 |
|------|------|
| 4 个 JSON 文件含 UTF-8 BOM 导致 Vite 启动崩溃 | PowerShell 批量清除 `\uFEFF` |

---

## 二、后端 (Spring Boot 3.3 + Java 17)

### 启动过程中的问题与修复

| # | 问题 | 根因 | 修复 |
|---|------|------|------|
| 1 | 10 个 `.java` + `application.yml` 全部含 BOM | IDE 生成文件时带了 BOM 头 | 批量清除 `\uFEFF` |
| 2 | `Entity.java` 类名遮蔽 `jakarta.persistence.@Entity` 注解 | 同包下类名与注解重名 | 重命名为 `KnowledgeEntity` |
| 3 | H2 建表生成 `engine=InnoDB` 语法报错 | 全局 `hibernate.dialect=MySQLDialect` 覆盖了 dev profile 的 H2 配置 | 移入 profile 专属配置 |
| 4 | MySQL JDBC 报 `UnsupportedEncodingException: utf8mb4` | JDBC 驱动不认识 `utf8mb4` 字符集名 | 改为 `characterEncoding=UTF-8` |
| 5 | Hibernate 6 报 `Unknown table SEQUENCES` | 连 MySQL 时未指定 dialect，自动检测失败 | 默认 profile 显式声明 `MySQLDialect` |
| 6 | 后端默认使用 `dev` profile (H2) 而非 MySQL | `spring.profiles.active` 默认值设为 `dev` | 改为 `default` |
| 7 | 后台 Java 进程被沙箱自动杀死 | Codex 沙箱限制后台进程生命周期 | 注册 approved prefix rule |

### 表结构 (最终在 MySQL 生成)

```sql
-- 记忆表
memories (
  id, title, content, type, source_url, file_path,
  sentiment, sentiment_score, processing_status,
  created_at, updated_at
)

-- 实体表
entities (
  id, name, type  -- PERSON/PLACE/ORG/EVENT/TOPIC/TECHNOLOGY/OTHER
)

-- 记忆↔实体多对多
memory_entity (
  id, memory_id(FK), entity_id(FK)
)

-- 实体关系表
relations (
  id, source_entity_id(FK), target_entity_id(FK),
  relation_type, memory_id(FK), created_at
)
```

### Redis 集成

| 功能 | 实现 |
|------|------|
| 缓存热点记忆 | Key `memories:recent`, TTL 10min |
| SSE 任务步骤 | Key `task:{taskId}`, List 结构, TTL 5min |
| 限流 | Key `rate:ask:{ip}`, 60 秒窗口上限 60 次 |

---

## 三、基础设施

### Docker Desktop

| 步骤 | 说明 |
|------|------|
| 安装 Docker Desktop 29.5.3 | WSL2 后端 |
| 虚拟磁盘从 C 盘迁移到 G 盘 | `mklink /J` 目录联接, 释放 C 盘 2.5GB |
| `docker compose up` 启动 Redis | 成功 |
| MySQL | 使用本机已有 MySQL (端口 3306), 停掉 Docker 中的 |
| Qdrant | 兼容性问题 (SIGSEGV) 暂跳过 |

### 运行状态

| 服务 | 地址 | 状态 |
|------|------|------|
| 前端 Vue 3 | `http://localhost:5173` | ✅ |
| 后端 Spring Boot | `http://localhost:8080` | ✅ MySQL 持久化 |
| MySQL | `localhost:3306` | ✅ 本机 |
| Redis | `localhost:6379` | ✅ Docker |
| Swagger | `http://localhost:8080/swagger` | ✅ |
| H2 Console | `http://localhost:8080/h2-console` | ✅ (dev profile) |

---

## 四、当前项目结构

```
MyPersonalPensieve/
├── frontend/               # Vue 3 + Vite + Tailwind + shadcn-vue + D3.js
│   └── src/pages/          # 6 个页面: Home / Memories / MemoryDetail / Graph / Analytics / Settings
├── backend/
│   └── src/main/java/com/pensieve/
│       ├── entity/         # Memory, KnowledgeEntity, MemoryEntity, Relation
│       ├── dto/            # MemoryRequest, MemoryResponse, PagedResponse
│       ├── repository/     # MemoryRepository
│       ├── service/        # MemoryService, RedisService
│       ├── controller/     # MemoryController
│       └── config/         # CorsConfig
├── docker-compose.yml      # Redis + MySQL + Qdrant
└── application.yml         # default (MySQL) + dev (H2) profiles
```
---

## 2026-06-16 — 后端重构：Spring Boot (Java) → FastAPI (Python)

### 理由

部分功能（如 LLM 集成、向量搜索、AI 代理）在 Python 生态中更成熟，Java 的 LangChain4j 等库版本滞后、社区支持较弱。尝试 Python 技术栈，利用 FastAPI + LangChain + Qdrant 的原生 Python 客户端，降低 AI 相关功能的接入成本。

### 完成事项

| 事项 | 说明 |
|------|------|
| 创建 `python-main` 分支 | 默认分支，`java` 分支保留 Spring Boot 旧版 |
| 删除所有 Java 文件 | `backend/src/main/java/` + `pom.xml` |
| Web 框架 | Spring Boot → **FastAPI** (异步) |
| ORM | JPA/Hibernate → **SQLAlchemy** (异步模式) |
| 数据库迁移 | ddl-auto:update → **Alembic** |
| Redis | Jedis/Lettuce → **redis-py** 异步 |
| Qdrant | Java Client → **qdrant-client** (Python) |
| LLM | LangChain4j → **LangChain** (Python) + OpenAI |
| Dockerfile | Java 17 → **Python 3.12-slim** |
| docker-compose.yml | 新增 backend 构建服务 |

### API 接口（完全兼容前端）

| 方法 | 路径 | 状态 |
|------|------|------|
| POST | `/api/memories` | ✅ |
| GET | `/api/memories` | ✅ 分页 |
| GET | `/api/memories/recent` | ✅ |
| GET | `/api/memories/{id}` | ✅ |
| DELETE | `/api/memories/{id}` | ✅ |
| GET | `/api/health` | ✅ |

### 服务容错

- OpenAI 客户端：懒加载，无 API key 时不影响启动
- Qdrant 客户端：懒加载，未连接时不影响启动
- Redis 操作：try/except 包裹，未运行时优雅降级（跳过限流/缓存）

### 运行方式

```bash
# 后端
cd backend
.venv\Scripts\uvicorn.exe app.main:app --reload --port 8080

# 前端（不变）
cd frontend
npm run dev
```


---

## 2026-06-17 — 前端对接真实 API + 设置页修复 + 新增后端端点

### 前端改动

| 文件 | 改动 |
|------|------|
| pi/index.ts | createMemory 改 JSON 体；searchMemories 改为 getMemories (GET)；新增 getRecentMemories；添加 axios 拦截器自动 snake_case→camelCase |
| 	ypes/index.ts | 对齐后端 PagedResponse (	otal_elements, 	otal_pages) 和 MemoryResponse |
| HomePage.vue | 改用 getRecentMemories 取真实数据 |
| MemoriesPage.vue | 改用 getMemories + createMemory(JSON)；移除 FormData 上传 |
| SettingsPage.vue | 修复暗色模式切换按钮：	ranslate-x-[22px] 替代不在 Tailwind 间距表的 	ranslate-x-5.5；加 overflow-hidden |

### 后端新增端点

| 端点 | 说明 |
|------|------|
| GET /api/graph | 返回实体 + 关系的知识图谱数据 (D3.js 可视化) |
| GET /api/analytics/sentiment | 按日期聚合情感趋势（支持 ?days=7/30/90） |

### 数据流

`
Vue 3 页面 → Vue Query → axios → Vite proxy (/api → :8080)
                                        ↓
                              FastAPI → SQLAlchemy → MySQL
`

### 当前状态

- 前端 6 个页面全部对接真实后端 API ✅
- 暗色模式切换按钮动画修复 ✅
- 记忆 CRUD（创建/列表/详情/删除）全部走 MySQL ✅
- 图谱和情感分析端点就绪，等待 AI 实体提取数据填充 ✅
- 开发环境运行方式不变



---

## 2026-06-23 — 重构为 Electron 桌面应用（SQLite + ChromaDB）

### 理由

Docker 微服务架构对终端用户部署门槛太高（需要装 Docker、启动 3 个容器）。改为 Electron 单体桌面应用，用户双击即可运行，数据本地存储，零配置。

### 架构变更

| 组件 | 之前 | 之后 |
|------|------|------|
| 数据库 | MySQL 8.0 (Docker) | **SQLite** (aiosqlite，嵌入式) |
| 向量存储 | Qdrant (Docker) | **ChromaDB** (本地持久化) |
| 缓存 | Redis (Docker) | **内存缓存** (同接口，无外部依赖) |
| 部署方式 | docker compose | **Electron + PyInstaller** 单体打包 |
| 前端 | Vite dev server | 支持 dev (proxy) + desktop (完整 URL) 两种模式 |

### 新增文件

| 文件 | 说明 |
|------|------|
| electron/main.js | Electron 主进程：启动后端子进程 + 创建窗口 |
| electron/preload.js | 预加载脚本，暴露 window.pensieve 环境信息 |
| electron/package.json | electron-builder 配置（NSIS 安装包 + portable） |
| electron/scripts/build.js | 一键构建脚本（前端 + 后端 + 打包） |
| ackend/run.py | PyInstaller 打包入口，输出 PENSIEVE_STARTING 信号 |
| ackend/pensieve_backend.spec | PyInstaller spec（含 ChromaDB 隐式依赖收集） |
| rontend/.env.development | 开发模式 API base 配置 |

### 后端改动

- config.py：新增 _default_data_dir() 自动解析数据目录（开发模式 ackend/data，打包后可执行文件同级 data）
- db/session.py：SQLite 连接参数 check_same_thread=False；新增 init_db() 首次启动自动建表（替代 alembic migrate）
- main.py：lifespan 中调用 init_db() + ensure_collection()
- qdrant_service.py：整文件改为 ChromaDB 实现，保持方法签名不变
- 
edis_service.py：整文件改为内存缓存实现（_MemoryStore），保持方法签名不变
- pyproject.toml：依赖从 syncmy/pymysql/redis/qdrant-client 换为 iosqlite/chromadb，dev 加 pyinstaller

### 前端改动

- pi/index.ts：aseURL 改为 import.meta.env.VITE_API_BASE || '/api'，支持桌面端完整 URL
- env.d.ts：声明 ImportMetaEnv 和 window.pensieve 类型
- package.json：uild 去掉 ue-tsc -b（加快构建），新增 uild:strict

### .gitignore 更新

排除 build 产物：rontend/dist/、*.tsbuildinfo、ite.config.js/d.ts、ackend/build/、ackend/dist/、electron/release/

### 数据流（桌面端）

`
Electron main.js
  ├─ spawn pensieve_backend.exe (PyInstaller)
  │    └─ uvicorn → FastAPI → SQLite + ChromaDB
  └─ BrowserWindow 加载 frontend/dist (静态文件)
       └─ axios → http://127.0.0.1:8080/api
`

### 当前状态

- 桌面端架构搭建完成 ✅
- 后端服务接口不变，业务层零改动 ✅
- 打包流程就绪（electron/scripts/build.js）✅
- 待后续：实际打包测试 + 桌面端 UI 适配

