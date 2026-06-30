<div align="center">

# SpringNote

**AI 驱动的个人记忆与知识管理系统**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js&logoColor=white)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

</div>

---

## 为什么选择 SpringNote

市面上的便签软件大多只能帮你保存内容，却很难帮你利用这些内容。SpringNote 因此而生。它不仅能够记录，更能够帮助你整理、沉淀和回顾。通过 AI 自动生成日报、周报和月报，并结合回忆书功能，让过去的记录变成随时可检索、可对话的个人知识资产。

## 核心功能

### 🏠 首页工作台

独创等级、收益、活跃热力图、快速输入框和今日摘要卡片。

![SpringNote 首页](docs/images/home.png)

### 🤖 AI 智能生成

在首页快速输入想法，由 AI 自动整理为结构化内容。

### 📝 便签编辑

支持日报、周报、月报等记录类型，提供 Markdown 编辑、预览、代码块高亮和 AI 补全预测。

![SpringNote 便签](docs/images/editor.png)

### 💬 回忆书对话

以对话方式检索和整理记忆内容，支持思考过程、工具调用展示与 Markdown 渲染。

![SpringNote 回忆书](docs/images/memory-book.png)

### 📊 自动报告生成

启动时可按日期补齐缺失的周报/月报，基于已有日报或周报生成总结。

### 📈 统计面板

查看记录、活跃度、模型调用和时间范围内的数据概览。

![SpringNote 统计面板](docs/images/analytics.png)

### ⏰ 牛马时钟

支持自定义日薪和工作时长，自动计算时薪并作为组件展示在页面上。

![SpringNote 组件](docs/images/clock-widget.png)

### 🖥️ 桌面端极致体验

支持自定义 Windows 标题栏、托盘、开机自启动、全局快捷键、桌面状态组件和系统字体切换。

---

## 快速开始

### 下载安装

通过 GitHub 下载，请前往 [Release 页](https://github.com/lightless-114514/MyPersonalPensieve/releases) 下载 SpringNote。

### 供应商配置

以 DeepSeek 为例进行配置说明：

**① 添加供应商 BaseURL**

请填写 `https://api.deepseek.com/beta`

![第一步](docs/images/step1.png)

**② 添加模型 `deepseek-v4-flash`**

![第二步](docs/images/step2.png)

**③ 编辑模型**

![第三步](docs/images/step3.png)

**④ 选择默认模型**

![第四步](docs/images/step4.png)

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
.venv\Scripts\uvicorn.exe app.main:app --port 8080

# 前端
cd frontend
npm install
npm run dev
```

---

## 🌍 社区

QQ 群组：**1 群：463423961**

---

## ❤️ Special Thanks

特别感谢所有 Contributors 和社区成员对 SpringNote 的支持 ❤️

---

## ⭐ Star History

> 如果本项目对您的生活 / 工作产生了帮助，或者您关注本项目的未来发展，请给项目 Star，这是我们维护这个开源项目的动力 <3

[![Star History Chart](https://api.star-history.com/svg?repos=lightless-114514/MyPersonalPensieve&type=Date)](https://star-history.com/#lightless-114514/MyPersonalPensieve&Date)

---

## 许可证

[MIT License](LICENSE)