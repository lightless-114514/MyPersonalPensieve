# MyPersonalPensieve 🧠

> 本地优先的 AI 个人记忆系统 — 存入任何内容，用自然语言查询你的过去。

## ✨ 特性

- 📝 **多模态输入** — 文字、截图、语音、链接，随心存入
- 🔍 **自然语言查询** — 用日常语言搜索你的记忆
- 🔒 **隐私安全** — 本地优先，数据自主可控
- 🧠 **AI 驱动** — LLM 自动提取实体、情感、关系
- 📊 **可视化** — 知识图谱、情感趋势一目了然

## 🏗️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Tailwind CSS + shadcn-vue |
| 后端 | Spring Boot 3.2 + Java 17 |
| 数据库 | MySQL 8.0 + Redis + Qdrant |
| AI | LangChain4j + OpenAI Whisper + Tesseract OCR |
| 部署 | Docker Compose + GitHub Actions |

## 🚀 快速开始

### 环境要求

- Java 17+
- Node.js 18+
- Maven 3.9+
- Docker & Docker Compose

### 启动基础设施

```bash
docker compose up -d
```

### 启动后端

```bash
cd backend
./mvnw spring-boot:run
```

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

## 📂 项目结构

```
MyPersonalPensieve/
├── backend/          # Spring Boot 后端
├── frontend/         # Vue 3 前端
├── docker-compose.yml
└── .github/          # CI/CD
```

## 📄 License

MIT
