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

问候语、最近记忆列表、快速记录入口。

### 📝 记忆管理

支持文字记录的创建、编辑、删除，可添加自定义标签和大标签分类（工作、生活、学习等），支持收藏功能快速标记重要记忆。

### ⚡ 经验系统

游戏化激励机制，记录即成长。输入文字获取经验，提交记忆获得额外奖励，逐级晋升阶级（麻瓜 → 新生 → 级长 → 魁地奇队长 → 傲罗 → 梅林勋章）。满级后可重生获得星级，支持自定义头衔和晋升特效。

### 🤖 AI 智能处理

接入 OpenAI API，自动从记忆内容中提取知识实体与关系、分析情感倾向，支持自然语言查询记忆。

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

### ⚙️ 设置

暗色模式切换、OpenAI API 密钥配置、中英文语言切换。

### ⏳ 时间胶囊

将日记封存到未来指定日期，到期后首页弹出通知提醒开封。封存期间不可查看内容，强行破拆需经历 30 秒冷静期倒计时。支持分页列表、状态过滤和搜索，后端持久化存储。

### 🖥️ 桌面端

基于 Electron 封装，支持独立窗口运行。

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
| 图表 | **D3.js** |

### 桌面端

| 类别 | 技术 |
|------|------|
| 桌面框架 | **Electron** |
| 后端打包 | **PyInstaller** |

---

## 开发环境

```bash
# 后端
cd backend
python -m venv .venv
.venv\Scripts\pip install -e .
.venv\Scripts\uvicorn.exe app.main:app --port 8000

# 前端
cd frontend
npm install
npm run dev
```

---

## ⭐ Star History

> 如果本项目对您的生活 / 工作产生了帮助，或者您关注本项目的未来发展，请给项目 Star，这是我们维护这个开源项目的动力 <3

[![Star History Chart](https://api.star-history.com/svg?repos=lightless-114514/MyPersonalPensieve&type=Date)](https://star-history.com/#lightless-114514/MyPersonalPensieve&Date)

---

## 许可证

[MIT License](LICENSE)