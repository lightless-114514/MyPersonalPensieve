# MyPersonalPensieve 🧠

> AI 个人记忆系统 — 记录、整理、检索你的思想与知识。

## 技术栈

### 后端 (Python) — `python-main` 分支

| 类别 | 技术 |
|------|------|
| Web 框架 | **FastAPI** |
| ORM | **SQLAlchemy** (异步模式) |
| 数据库迁移 | **Alembic** |
| 主数据库 | **MySQL 8.0** (asyncmy) |
| 向量数据库 | **Qdrant** (qdrant-client) |
| 缓存/任务队列 | **Redis** (redis-py) |
| LLM 集成 | **LangChain** + **OpenAI** |
| 环境管理 | **uv / pip** |

### Java 版本java 分支 — [Spring Boot 旧版](https://github.com/lightless-114514/MyPersonalPensieve/tree/java)

### 前端

| 类别 | 技术 |
|------|------|
| 框架 | **Vue 3** + **TypeScript** |
| UI 组件 | **shadcn-vue** |
| 样式 | **Tailwind CSS** |
| 构建工具 | **Vite** |

## 快速开始

### 前置要求

- Python 3.12+
- Docker & Docker Compose
- Node.js 18+ (前端)

### 开发环境

```bash
# 1. 启动基础设施
docker compose up -d mysql redis qdrant

# 2. 启动后端
cd backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8080

# 3. 启动前端
cd frontend
npm install
npm run dev
```

### 生产部署

```bash
docker compose up -d
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/memories` | 创建记忆 |
| GET | `/api/memories` | 分页获取记忆 |
| GET | `/api/memories/recent` | 获取最近记忆 |
| GET | `/api/memories/{id}` | 获取单条记忆 |
| DELETE | `/api/memories/{id}` | 删除记忆 |
| GET | `/api/health` | 健康检查 |

## 项目结构

```
├── backend/              # Python FastAPI 后端
│   ├── app/
│   │   ├── main.py       # FastAPI 应用入口
│   │   ├── config.py     # 配置管理
│   │   ├── models/       # SQLAlchemy 模型
│   │   ├── schemas/      # Pydantic 数据校验
│   │   ├── routes/       # API 路由
│   │   ├── services/     # 业务逻辑层
│   │   └── db/           # 数据库会话
│   ├── alembic/          # 数据库迁移
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/             # Vue 3 前端
├── docker-compose.yml
└── README.md
```

## 许可证

MIT License
