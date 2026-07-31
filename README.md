<div align="center">

# MyPersonalPensieve

**AI 驱动的个人记忆与知识管理系统**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js&logoColor=white)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

</div>

---

## 为什么选择 MyPersonalPensieve

传统的笔记工具只负责记录，却很难帮你从记录中提取价值。MyPersonalPensieve 不仅存储你的文字、链接和想法，更通过 AI 自动提取实体与关系、分析情感倾向、构建知识图谱，让散落的记忆变成可检索、可可视化的个人知识网络。

## 核心功能

### 🏠 首页工作台

问候语、最近记忆列表、快速记录入口、时间胶囊到期提醒。

### 📝 记忆管理

支持文字记录的创建、编辑、删除，可添加自定义标签和大标签分类（工作、生活、学习等），支持收藏功能快速标记重要记忆。支持文件附件上传。

### ⚡ 经验系统

游戏化激励机制，记录即成长。输入文字获取经验，提交记忆获得额外奖励，逐级晋升阶级（麻瓜 → 新生 → 级长 → 魁地奇队长 → 傲罗 → 梅林勋章）。满级后可重生获得星级，支持自定义头衔和晋升特效。

### 🤖 AI 智能处理

接入 OpenAI 兼容 API（DeepSeek / OpenAI 等），自动从记忆内容中提取知识实体与关系、分析情感倾向，支持自然语言查询记忆。

### 🕸️ 知识图谱

基于 D3.js 力导向图和树形布局，可视化展示记忆中的实体与关系网络。节点按类型颜色分类：

| 颜色 | 类型 | 说明 |
|------|------|------|
| 🔵 蓝色 | 摘要 | 记忆节点，展示记忆标题 |
| 🟢 绿色 | 实体 | 人物、地点、组织、技术 |
| 🟡 黄色 | 概念 | 话题、事件 |
| ⚪ 灰色 | 其他 | 未分类实体 |

**交互操作：**
- **单击** → 打开节点详情面板
- **双击** → 以该节点为中心聚焦
- **Shift+单击** → 展开邻居节点到画布
- **⊕ 按钮** → 悬浮显示在节点右上角，点击展开邻居
- **拖拽节点** → 手动调整位置
- **拖拽空白** → 平移画布
- **滚轮** → 缩放画布

支持按大标签筛选、适应屏幕、隐藏箭头、图例说明面板。

### 📊 情感分析

情感趋势图表，按时间范围和大标签查看情感变化，直观了解情绪走向。

### 📈 洞察报告

AI 自动生成周报和月报，总结记忆中的关键主题、情感趋势和重要事件。支持历史报告归档查看和详情阅读。

### ⚖️ 对比分析

选择两个时间段进行记忆对比，AI 分析两个时期的情感变化、主题差异和成长轨迹。

### 🎂 生日提醒

记录联系人的生日，到期自动提醒，支持本地存储管理。

### ⏳ 时间胶囊

将日记封存到未来指定日期，到期后首页弹出通知提醒开封。封存期间不可查看内容，强行破拆需经历 30 秒冷静期倒计时。支持分页列表、状态过滤和搜索，后端持久化存储。

### 📤 数据导出

支持将记忆数据导出为 PDF 文件，方便备份和分享。

### ⚙️ 设置

暗色模式切换、LLM 供应商配置（API 密钥、Base URL、模型选择）、中英文语言切换。

### 🖥️ 桌面端

基于 Electron 封装，支持独立窗口运行，后端通过 PyInstaller 打包为单文件。

---

## 快速开始

### 下载安装

通过 GitHub 下载，请前往 [Release 页](https://github.com/lightless-114514/MyPersonalPensieve/releases) 下载最新版本。

### 供应商配置

以 DeepSeek 为例进行配置说明：

**① 添加供应商 BaseURL**

请填写 `https://api.deepseek.com/beta`

**② 添加模型 `deepseek-v4-flash`**

**③ 编辑模型参数**

**④ 在设置中选择默认模型**

---

## 技术栈

### 后端 (Python)

| 类别 | 技术 |
|------|------|
| Web 框架 | **FastAPI** |
| ORM | **SQLAlchemy** (异步模式) |
| 数据库迁移 | **Alembic** |
| 主数据库 | **SQLite** (aiosqlite) |
| 向量数据库 | **ChromaDB** |
| 缓存 | **内存缓存** |
| LLM 集成 | **LangChain** + **OpenAI** |

### 前端

| 类别 | 技术 |
|------|------|
| 框架 | **Vue 3** + **TypeScript** |
| UI 组件 | **shadcn-vue** |
| 样式 | **Tailwind CSS** |
| 构建工具 | **Vite** |
| 数据请求 | **TanStack Query** |
| 状态管理 | **Pinia** |
| 图表 | **D3.js** |

### 桌面端

| 类别 | 技术 |
|------|------|
| 桌面框架 | **Electron** |
| 后端打包 | **PyInstaller** |

---

## 开发环境

### 环境要求

- Python 3.12+
- Node.js 18+

### 后端（端口 8000）

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\pip install -e .
.venv\Scripts\uvicorn.exe app.main:app --port 8000
# macOS/Linux
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --port 8000
```

### 前端（端口 5173）

```bash
cd frontend
npm install
npm run dev
```

前端已配置代理，`/api` 请求自动转发到后端 `http://localhost:8000`。

### 配置

后端配置项见 `backend/.env.example`，复制为 `.env` 后按需修改：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| SERVER_HOST | 127.0.0.1 | 后端监听地址 |
| SERVER_PORT | 8000 | 后端端口 |
| LLM_API_KEY | 空 | LLM API Key |
| LLM_BASE_URL | 空 | LLM API Base URL |
| LLM_MODEL | deepseek-v4-flash | 默认模型名称 |
| LLM_PROVIDER | deepseek | LLM 供应商 |
| PENSIEVE_DATA_DIR | backend/data | 数据目录 |

---

## 项目结构

```
MyPersonalPensieve/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py         # 应用入口
│   │   ├── config.py       # 配置管理
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   ├── routes/         # API 路由
│   │   ├── services/       # 业务逻辑层
│   │   └── schemas/        # Pydantic 请求/响应模型
│   ├── alembic/            # 数据库迁移
│   └── data/               # SQLite + ChromaDB 数据存储
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── api/            # API 客户端
│   │   └── types/          # TypeScript 类型定义
│   └── ...
├── electron/               # Electron 桌面端
│   ├── main.js             # 主进程
│   ├── preload.js          # 预加载脚本
│   └── scripts/            # 打包脚本
└── docker-compose.yml      # Docker 部署配置（旧版，仅供参考）
```

---

## ⭐ Star History

> 如果本项目对您的生活 / 工作产生了帮助，或者您关注本项目的未来发展，请给项目 Star，这是我们维护这个开源项目的动力 <3

[![Star History Chart](https://api.star-history.com/svg?repos=lightless-114514/MyPersonalPensieve&type=Date)](https://star-history.com/#lightless-114514/MyPersonalPensieve&Date)

---

## 许可证

[MIT License](LICENSE)