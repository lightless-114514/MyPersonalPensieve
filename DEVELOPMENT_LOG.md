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
