# MyPersonalPensieve - 开发日志

## 2026-07-12 — 记忆卡片大标签覆盖修复 + 知识导图树形布局⊕按钮移除

### 功能概述

修复两个UI问题：①记忆卡片大标签覆盖卡片内容 ②知识导图树形布局中不应存在的⊕展开按钮（力导向图保留）。

### Bug 1：记忆卡片大标签覆盖内容

**根因**：`MemoriesPage.vue` 中记忆卡片容器使用固定 `p-4` 内边距，而大标签使用 `absolute -top-0.5 -left-0.5` 定位在卡片左上角，顶部内边距不足导致大标签覆盖卡片标题文字。

**修复**：
| 文件 | 改动 |
|------|------|
| `pages/MemoriesPage.vue` | 卡片容器 class 从静态 `p-4` 改为动态 `:class="m.bigTag ? 'p-4 pt-10' : 'p-4'"`，有大标签时增加顶部内边距 |

### Bug 2：知识导图树形布局多余⊕按钮

**根因**：`GraphPage.vue` 的 `renderTree()` 方法从 `renderForce()` 复制了⊕展开邻居按钮的SVG元素和交互逻辑，但树形布局展示全量层级数据，不需要增量展开功能，⊕按钮反而造成误导。

**修复**：
| 文件 | 改动 |
|------|------|
| `pages/GraphPage.vue` | 移除 `renderTree()` 中⊕按钮的SVG circle/text元素、hover显示逻辑、click事件处理；图例提示条件化为 `v-if="layoutMode === 'force'"` 仅力导向图显示⊕说明 |

**差异化交互设计**：
- 力导向图：保留⊕按钮 + Shift+Click，支持增量添加邻居节点（因力导向图仅展示局部关联）
- 树形布局：移除⊕按钮，展示完整层级结构（全量数据无需增量展开）

### 文件改动

| 文件 | 改动类型 |
|------|----------|
| `frontend/src/pages/MemoriesPage.vue` | 卡片padding条件化：有大标签时pt-10，无则p-4 |
| `frontend/src/pages/GraphPage.vue` | 移除renderTree()中⊕按钮相关代码约37行；图例⊕提示条件显示 |

---

## 2026-07-10 — 自我洞察功能（周报/月报/档案）+ 隐私控制 — 自我洞察功能（周报/月报/档案）+ 隐私控制

### 功能概述

新增AI驱动的自我洞察功能，支持生成周报和月报，提供情绪曲线、关键词、高低点分析等维度；洞察档案页面管理历史报告；日记隐私控制（可分析/仅存储/锁定）确保敏感内容不被AI分析。

### 后端模型新增

| 模型/枚举 | 说明 |
|-----------|------|
| `InsightReport` | 洞察报告表：report_type(WEEKLY/MONTHLY)、日期范围、summary、emotion_curve(JSON)、keywords(JSON)、low_point(JSON)、high_point(JSON)、pattern(月报)、core_theme(月报)、memory_count、is_read |
| `InsightType` | 枚举：WEEKLY / MONTHLY |
| `PrivacyStatus` | 枚举：ANALYZE(纳入分析) / STORE(仅存储) / LOCKED(加密锁定) |
| `Memory.privacy_status` | 新增字段，默认 ANALYZE，控制日记是否参与洞察分析 |

### 后端API（8个新端点）

| 端点 | 说明 |
|------|------|
| `GET /api/insight/weekly/status?weekStart=` | 查询指定周是否已生成周报，返回exists/hasNewMemories |
| `GET /api/insight/weekly?weekStart=` | 获取指定周的周报数据 |
| `GET /api/insight/monthly?monthStart=` | 获取指定月的月报数据（最新一份） |
| `GET /api/insight/archive?page=&size=` | 洞察档案列表（分页） |
| `GET /api/insight/archive/{id}` | 档案详情（自动标记已读） |
| `POST /api/insight/generate/weekly` | 生成周报（已存在则覆盖更新） |
| `POST /api/insight/generate/monthly` | 生成月报（允许重复生成，每次新建记录） |
| `DELETE /api/insight/archive/{id}` | 删除洞察报告 |

### 周报生成逻辑

1. 获取指定周内 `privacy_status=ANALYZE` 的日记
2. 提取每篇日记的日期、标题、内容预览(200字)、情绪值
3. 调用LLM生成JSON：summary、emotion_curve(每日数据点)、keywords(TOP5)、low_point、high_point
4. 已存在周报则覆盖更新，不存在则新建

### 月报生成逻辑（两步法优化Token）

1. 获取指定月内 `privacy_status=ANALYZE` 的日记
2. **第一步**：按周分组，压缩为周代表摘要（日期范围、日记数、平均情绪、标题摘要）
3. **第二步**：调用LLM生成月报JSON：summary、emotion_curve(每周数据点)、keywords(TOP10)、low_point、high_point、pattern(显著模式)、core_theme(核心主题)
4. 每次生成创建新记录，不覆盖

### 隐私控制

| 状态 | 图标 | 含义 | 洞察行为 |
|------|------|------|----------|
| ANALYZE | Eye | 可分析 | 出现在周报/月报中 |
| STORE | Database | 仅存储 | 保存但AI不可见 |
| LOCKED | Lock | 锁定 | 加密存储，完全私密 |

- MemoryDetailPage 编辑区域新增隐私状态切换按钮
- `updateMemory` API 支持 `privacy_status` 字段更新
- 洞察生成时仅查询 `privacy_status=ANALYZE` 的日记

### 前端页面（4个新页面）

| 页面 | 路由 | 说明 |
|------|------|------|
| `InsightWeeklyPage.vue` | `/insight/weekly` | 周报页面：周选择器、生成按钮、情绪曲线图、关键词、高低点卡片 |
| `InsightMonthlyPage.vue` | `/insight/monthly` | 月报页面：月选择器、生成按钮、情绪曲线(按周)、关键词、模式/主题卡片 |
| `InsightArchivePage.vue` | `/insight/archive` | 档案列表：周报/月报卡片、分页、删除、点击查看详情 |
| `InsightDetailPage.vue` | `/insight/archive/:id` | 报告详情：完整展示单份洞察报告所有字段 |

### 侧边栏改动

- 新增"自我洞察"折叠菜单（Sparkles图标），含三个二级入口：
  - **周报**：蓝色小圆点提示（有新日记未生成周报）、已生成标记、生成中旋转动画
  - **月报**：绿色小圆点提示（每月1-7日显示）
  - **洞察档案**：红色小圆点提示（有未读报告）
- onMounted时自动检测周报状态和月报提示

### 前端状态管理

- `stores/insight.ts`：Pinia store，管理currentReport、archiveItems、weeklyStatus、生成状态、侧边栏提示状态
- API超时：周报生成120s、月报生成300s（Token消耗大）

### 数据库迁移

| 迁移文件 | 说明 |
|----------|------|
| `ef300e1cd3c9_add_privacy_status_to_memory.py` | memories表新增privacy_status列(ANALYZE/STORE/LOCKED)，默认ANALYZE |

### Bug修复

| Bug | 修复 |
|-----|------|
| 洞察API对不存在的周报/月报返回404导致前端报错 | 改为返回200 + null，前端优雅处理 |

### 文件改动

| 文件 | 改动类型 |
|------|----------|
| `backend/app/models/memory.py` | 新增InsightReport模型、InsightType枚举、PrivacyStatus枚举、Memory添加privacy_status字段 |
| `backend/app/routes/insight.py` | 新增：8个洞察API端点 |
| `backend/app/schemas/insight.py` | 新增：请求/响应Schema |
| `backend/app/services/insight_service.py` | 新增：洞察生成服务（周报/月报/档案/LLM调用/JSON解析） |
| `backend/app/main.py` | 注册insight路由 |
| `backend/app/schemas/memory.py` | 添加privacy_status字段 |
| `backend/app/services/memory_service.py` | update()支持privacy_status |
| `backend/alembic/versions/ef300e1cd3c9_...py` | 新增：privacy_status迁移 |
| `frontend/src/pages/InsightWeeklyPage.vue` | 新建：周报页面 |
| `frontend/src/pages/InsightMonthlyPage.vue` | 新建：月报页面 |
| `frontend/src/pages/InsightArchivePage.vue` | 新建：洞察档案页面 |
| `frontend/src/pages/InsightDetailPage.vue` | 新建：报告详情页面 |
| `frontend/src/stores/insight.ts` | 新建：洞察Pinia store |
| `frontend/src/api/index.ts` | 新增7个洞察API函数 |
| `frontend/src/types/index.ts` | 新增InsightReport/InsightReportListItem/WeeklyStatus/InsightArchive/EmotionCurvePoint/KeywordPoint/PrivacyStatus类型 |
| `frontend/src/router/index.ts` | 新增4条洞察路由 |
| `frontend/src/components/Sidebar.vue` | 新增自我洞察折叠菜单+提示圆点 |
| `frontend/src/pages/MemoryDetailPage.vue` | 新增隐私状态切换UI |

---

## 2026-07-07 — 知识图谱界面全面改造 + 后端端口迁移至8000 + 后端端口迁移至8000

### 功能概述

对知识图谱页面进行重大改造：实现节点颜色分类、丰富的交互操作、图例面板和工具栏；后端API添加nodeType字段和摘要节点；将后端端口从8080迁移至8000以避免与Steam等应用端口冲突。

### 知识图谱节点颜色分类

| 节点类型 | 颜色 | 含义 |
|----------|------|------|
| 摘要 (summary) | 蓝色 `#3b82f6` | 记忆节点，从记忆标题生成 |
| 实体 (entity) | 绿色 `#22c55e` | PERSON, PLACE, ORG, TECHNOLOGY |
| 概念 (concept) | 黄色 `#eab308` | TOPIC, EVENT |
| 其他 (other) | 灰色 `#9ca3af` | OTHER |

### 交互功能

| 操作 | 效果 |
|------|------|
| 单击节点 | 打开右侧详情面板（摘要节点加载记忆内容） |
| 双击节点 | 以该节点为中心聚焦（缩放+平移动画） |
| Shift+单击 | 叠加该节点邻居到画布 |
| 节点右上角 ⊕ 按钮 | 悬浮显示，点击展开邻居（同Shift+单击） |
| 拖拽节点 | 手动调整节点位置 |
| 拖拽空白区域 | 平移画布 |
| 滚轮 | 缩放画布 |

### UI控件

- **图例小窗口**（左下角）：颜色含义 + 操作说明，可关闭/展开
- **适应屏幕按钮**：一键缩放至全部节点可见
- **隐藏/显示箭头**：切换连线箭头显示

### 后端API改动

- `GET /api/graph` 响应中每个节点新增 `nodeType` 字段（`summary`/`entity`/`concept`/`other`）
- 新增记忆摘要节点（id格式 `memory_{id}`），与关联实体之间建立 `has_entity` 连线

### 端口迁移 8080 → 8000

Steam等应用占用8080端口导致后端无法正常响应，将全部相关配置迁移至8000。

| 文件 | 改动 |
|------|------|
| `frontend/vite.config.ts` | proxy target → localhost:8000 |
| `frontend/vite.config.js` | proxy target → localhost:8000 |
| `frontend/.env.development` | 注释更新 |
| `frontend/.env.production` | API地址 → 127.0.0.1:8000 |
| `backend/app/config.py` | 默认端口 → 8000 |
| `backend/Dockerfile` | EXPOSE + CMD → 8000 |
| `backend/run.py` | 默认端口 → 8000 |
| `backend/run_with_proxy.py` | uvicorn端口 → 8000 |
| `backend/.env` / `.env.example` | SERVER_PORT=8000 |
| `docker-compose.yml` | 端口映射 + SERVER_PORT |
| `start_servers.bat` | uvicorn启动端口 |
| `electron/main.js` | SERVER_PORT常量 |

### 文件改动

| 文件 | 改动类型 |
|------|----------|
| `frontend/src/pages/GraphPage.vue` | 全面重写：节点颜色、交互、图例、⊕按钮 |
| `frontend/src/types/index.ts` | GraphNode接口添加nodeType字段 |
| `backend/app/routes/analytics.py` | 添加nodeType映射、摘要节点、memory-entity连线 |
| `frontend/vite.config.ts` / `.js` | proxy端口8000 |
| `frontend/.env.development` / `.env.production` | 端口8000 |
| `backend/app/config.py` | 默认端口8000 |
| `backend/Dockerfile` | EXPOSE + CMD 8000 |
| `backend/run.py` / `run_with_proxy.py` | 端口8000 |
| `backend/.env` / `.env.example` | SERVER_PORT=8000 |
| `docker-compose.yml` | 端口映射8000 |
| `start_servers.bat` | uvicorn端口8000 |
| `electron/main.js` | SERVER_PORT=8000 |

---

## 2026-07-05 — 图片预览Bug修复 + 页面卡死Bug修复 + 标签下拉栏UX增强

### 功能概述

修复两个关键前端Bug：①图片上传后不显示预览 ②页面卡死无法切换路由。两者实为同一根因的级联故障。同时为标签下拉栏添加关闭按钮和失焦自动隐藏功能。

### Bug 1：图片上传后不显示预览

**根因**：`FileDropZone.vue` 模板中直接使用 `URL.createObjectURL(selectedFile)`，但 Vue 3 `<script setup>` 模板渲染上下文无法访问全局 `URL` 对象，导致 `Uncaught TypeError: Cannot read properties of undefined (reading 'createObjectURL')`，渲染崩溃。

**修复**：
| 文件 | 改动 |
|------|------|
| `components/FileDropZone.vue` | 新增 `previewUrl` computed 在 `<script setup>` 作用域内调用 `URL.createObjectURL()`；新增 `objectUrl` 变量追踪对象URL，computed重新求值时自动 `revokeObjectURL()`；新增 `onUnmounted` 钩子释放对象URL防内存泄漏；模板 `:src="URL.createObjectURL(selectedFile)"` → `:src="previewUrl"` |

### Bug 2：页面卡死无法切换路由

**根因**：FileDropZone 组件渲染崩溃破坏 Vue 虚拟DOM树完整性，级联引发 `parentNode`/`nextSibling` 为 null 的错误，导致 `<transition mode="out-in">` 路由过渡无法完成，页面卡死在当前路由。

**修复**：同Bug 1，修复 FileDropZone 根因后级联故障自动消除。

### 辅助修复（非根因，保留）

| 文件 | 改动 | 说明 |
|------|------|------|
| `backend/app/routes/files.py` | inline模式不再设置filename | 避免Content-Disposition干扰 |
| `frontend/src/api/index.ts` | getFilePreviewUrl添加时间戳防缓存 | `?t=${Date.now()}` |
| `frontend/src/pages/GraphPage.vue` | D3 simulation生命周期清理 | onUnmounted中停止simulation |
| `frontend/src/components/AppLayout.vue` | transition @before-leave保护 | 防止未完成过渡 |

### 标签下拉栏UX增强

**MemoriesPage.vue**：
- 新增 `tagBlurTimer`、`onTagBlur`、`cancelTagBlur`、`closeTagDropdown` 函数
- input 添加 `@blur="onTagBlur"` 事件，离开输入框150ms后自动隐藏下拉
- 下拉栏顶部添加"选择标签"标题 + X关闭按钮
- 建议项 `@mousedown.prevent` 改为 `cancelTagBlur(); addTag(t.tag)` 防误关
- `addTag` 函数添加 `cancelTagBlur()` + `nextTick` 回聚焦

**MemoryDetailPage.vue**：
- 新增 `editTagInputRef`、`editTagBlurTimer`、`onEditTagBlur`、`cancelEditTagBlur`、`closeEditTagDropdown`
- 新增 `getTags` 查询和 `editSuggestions` computed（原来编辑时无标签建议）
- input 添加 `@blur="onEditTagBlur"` + `ref="editTagInputRef"`
- 下拉栏添加关闭按钮头部 + 建议项列表 + 空状态提示

### 文件改动

| 文件 | 改动类型 |
|------|----------|
| `frontend/src/components/FileDropZone.vue` | 核心根因修复：previewUrl computed + onUnmounted内存释放 |
| `frontend/src/pages/MemoriesPage.vue` | 标签下拉栏UX增强：关闭按钮 + blur自动隐藏 |
| `frontend/src/pages/MemoryDetailPage.vue` | 编辑标签同样增强 + 新增标签建议 |
| `backend/app/routes/files.py` | FileResponse inline模式filename修复 |
| `frontend/src/api/index.ts` | 文件预览URL缓存破坏 |
| `frontend/src/pages/GraphPage.vue` | D3 simulation生命周期清理 |
| `frontend/src/components/AppLayout.vue` | transition过渡保护 |

---

## 2026-07-04 — 记忆对比功能 + 新建记忆按钮Bug修复 + 超时优化

### 功能概述

新增AI驱动的记忆对比功能，支持选择多组记忆进行智能对比分析；修复左下角新建记忆按钮在同页面下无法响应的Bug；修复对比接口500错误；优化前后端超时配置以支持LLM长耗时调用。

### 新建记忆按钮Bug修复

| Bug | 根因 | 修复 |
|-----|------|------|
| 左下角"新建记忆"按钮点击无反应 | MemoriesPage仅在初始化时读取`route.query.new`，同页面导航不会重新执行setup | 添加`watch(() => route.query.new)`监听路由变化，动态设置`showCreate` |

### 对比接口500错误修复

| Bug | 根因 | 修复 |
|-----|------|------|
| `/api/compare` 返回500 MissingGreenlet | SQLAlchemy async session中访问`m.tags`触发懒加载，异步上下文不支持 | `_fetch_memories()`查询添加`.options(selectinload(Memory.tags))`预加载 |

### 超时优化

| 问题 | 根因 | 修复 |
|------|------|------|
| 前端30秒超时 `timeout of 30000ms exceeded` | LLM调用DeepSeek API耗时超过axios默认30s | axios请求添加`{ timeout: 120000 }` |
| Vite代理超时 | Vite dev server proxy默认超时较短 | proxy配置添加`timeout: 120000` |
| 后端LLM调用无超时保护 | 无 | `asyncio.wait_for(timeout=90.0)`包裹LLM调用 |

### 后端API（1个新端点）

| 端点 | 说明 |
|------|------|
| `POST /api/compare` | 接收source_ids/target_ids，AI对比分析返回对比结果 |

### 前端页面（1个新页面）

| 页面 | 说明 |
|------|------|
| `ComparePage.vue` | 记忆对比页面，左右分栏选择源/目标记忆，展示AI对比结果 |

### 文件改动

| 文件 | 改动类型 |
|------|----------|
| `frontend/src/pages/MemoriesPage.vue` | 添加route.query watcher修复按钮Bug |
| `backend/app/routes/compare.py` | 新增：对比API路由（含selectinload修复+超时保护） |
| `backend/app/schemas/compare.py` | 新增：对比请求/响应Schema |
| `backend/app/main.py` | 注册compare路由 |
| `frontend/src/pages/ComparePage.vue` | 新建：记忆对比页面 |
| `frontend/src/components/Sidebar.vue` | 添加对比入口 |
| `frontend/src/router/index.ts` | 添加对比路由 |
| `frontend/src/api/index.ts` | 新增compareMemories函数（120s超时） |
| `frontend/src/types/index.ts` | 新增对比相关类型 |
| `frontend/vite.config.ts` | proxy超时配置120s |

---

## 2026-07-03 — 首页数据统计仪表盘 + 热力图Bug修复

### 功能概述

在首页Hero区域下方嵌入数据统计仪表盘，包含GitHub风格写作热力图、高频词汇云图、4格统计卡片，提供视觉化的"成就感"反馈。

### 后端API（3个新端点）

| 端点 | 说明 |
|------|------|
| `GET /api/analytics/heatmap` | 返回全年365天每日字数/记忆数 |
| `GET /api/analytics/wordcloud` | 返回高频标签词频（支持period参数） |
| `GET /api/analytics/stats` | 返回汇总统计（总记忆/总字数/连续天数/本月新增） |

### 前端组件（3个新组件）

| 组件 | 说明 |
|------|------|
| `HeatmapChart.vue` | D3.js SVG热力图，53×7矩阵，5级绿色色阶，全年/本季度/本月切换 |
| `WordCloudChart.vue` | Canvas螺旋布局词云，本月/本年切换 |
| `StatsCards.vue` | 4格统计卡片（总记忆/总字数/连续天数/本月新增） |

### 热力图Bug修复

| Bug | 根因 | 修复 |
|-----|------|------|
| 全年模式12月/1月标签重叠 | startSunday回退到前一年12月，月份标签从12月开始渲染 | 月份标签增加displayMonthMin/Max/Year范围过滤 |
| 本月/本季度显示6个月数据 | filteredData只有startDate过滤，无endDate边界 | 添加endDate过滤（季度末日/月末） |
| 日期偏移1天 | toISOString()在UTC+8下把7月1日转为"2026-06-30" | 新增formatDate()本地时间格式化 |

### 文件改动

| 文件 | 改动类型 |
|------|----------|
| `backend/app/routes/analytics.py` | 新增3个API端点 |
| `frontend/src/types/index.ts` | 新增HeatmapDay/WordCloudItem/StatsSummary类型 |
| `frontend/src/api/index.ts` | 新增getHeatmap/getWordCloud/getStats函数 |
| `frontend/src/components/HeatmapChart.vue` | 新建：D3热力图组件 |
| `frontend/src/components/WordCloudChart.vue` | 新建：Canvas词云组件 |
| `frontend/src/components/StatsCards.vue` | 新建：统计卡片组件 |
| `frontend/src/pages/HomePage.vue` | 嵌入仪表盘三组件 |

---

## 2026-07-02 — huashu-design 美化：反AI slop系统性重构

### 设计哲学

依据 `.agents/skills/huashu-design/SKILL.md` 的反AI slop原则和品位锚点，对全站进行系统性美化重构。核心原则：一个有温度的底色 + 单个accent贯穿全场 + serif display字体 + 减法设计。

### 反slop六条禁令检查与修复

| 禁令 | 原状态 | 修复 |
|------|--------|------|
| 禁紫色渐变 | 紫色主色(HSL 262° 83% 58%) | → 暖铜色(HSL 28° 75% 48%) |
| 禁emoji作图标 | 6处emoji(📝🖼️😊😔😐⚡✓) | → lucide-vue-next组件 |
| 禁圆角卡片+左border accent | 无此模式 | ✅ 保持 |
| 禁SVG画人/物 | 无 | ✅ 保持 |
| 禁CSS剪影代产品图 | 无 | ✅ 保持 |
| 禁Inter/Roboto作display字体 | 系统默认sans-serif | → Georgia/Noto Serif SC serif |

### 色彩体系重构

全套HSL变量从紫色调转为暖铜色调：

| 变量 | 亮色模式 | 暗色模式 |
|------|----------|----------|
| --primary | 28 75% 48% | 28 70% 58% |
| --background | 40 20% 98% | 30 15% 6% |
| --accent | 28 60% 92% | 28 40% 18% |
| --border | 30 12% 88% | 30 10% 18% |
| --radius | 0.625rem | — |
| --card-shadow | 减淡(0.03透明度) | 减淡(0.2透明度) |

### 字体体系升级

- **Display字体**：Georgia, Noto Serif SC, Songti SC, serif — 用于所有h1/h2/h3
- **Body字体**：-apple-system, BlinkMacSystemFont, Segoe UI, Noto Sans SC, sans-serif
- **排版优化**：text-wrap:pretty、hanging-punctuation:first

### emoji→lucide图标替换

| 页面/组件 | 原emoji | 替换为 |
|-----------|---------|--------|
| utils.ts typeIcon | 📝🖼️ | FileText/ImageIcon/File |
| utils.ts BIG_TAG_CONFIG | 📖✏️💡⚖️ | BookOpen/PenLine/Lightbulb/Scale |
| HomePage | ✨(空状态) | 移除 |
| MemoriesPage | 📝🖼️😊😔😐 | lucide组件+文字标签 |
| MemoryDetailPage | 📖✏️💡⚖️ | component:is动态组件 |
| GraphPage | 🔀🕸️ | GitBranch/Network |
| AnalyticsPage | 📖✏️💡⚖️ | component:is动态组件 |
| SettingsPage | ✓ | Check图标 |
| Sidebar | ⚡ | Zap图标 |

### 设计签名时刻

- **HomePage hero区域**：Brain图标呼吸动画(animate-breathe) + 暖铜色accent装饰线(w-12 h-0.5 bg-primary/40)
- **所有h1**：font-display serif字体，tracking-tight
- **所有h2**(SettingsPage)：font-display serif字体

### 交互优化

- **AppLayout**：fade→page过渡动画，进入时translateY(4px)微动
- **tailwind.config.js**：动画easing改为cubic-bezier(0.22,1,0.36,1)
- **SettingsPage**：section卡片shadow-card + rounded-xl
- **AnalyticsPage**：图表卡片shadow-card + rounded-xl
- **GraphPage**：h1添加font-display

### Electron打包优化

- **main.js backgroundColor**：#0f172a(暗色硬编码) → #faf8f5(匹配亮色主题)
- **global.css**：Chromium滚动条优化(6px宽/透明轨道)
- **global.css**：electron-drag/electron-no-drag区域定义
- **global.css**：display-mode:windowed下no-select

### 文件改动

| 文件 | 改动类型 |
|------|----------|
| `frontend/src/styles/global.css` | 色彩体系+字体+排版+Electron优化 |
| `frontend/tailwind.config.js` | 字体配置+动画easing+breathe动画 |
| `frontend/src/lib/utils.ts` | emoji→lucide Component重构 |
| `frontend/src/pages/HomePage.vue` | hero签名时刻+typeIcon组件化 |
| `frontend/src/pages/MemoriesPage.vue` | emoji→lucide+font-display |
| `frontend/src/pages/MemoryDetailPage.vue` | typeIcon/opt.icon组件化+font-display |
| `frontend/src/pages/GraphPage.vue` | emoji→lucide+font-display |
| `frontend/src/pages/AnalyticsPage.vue` | opt.icon组件化+font-display+shadow-card |
| `frontend/src/pages/SettingsPage.vue` | font-display+shadow-card+rounded-xl+Check图标 |
| `frontend/src/components/Sidebar.vue` | ⚡→Zap图标 |
| `frontend/src/components/AppLayout.vue` | fade→page过渡动画 |
| `frontend/src/types/experience.ts` | 经验参数调优 |
| `electron/main.js` | backgroundColor匹配主题 |

---

## 2026-07-01 — 经验系统优化：加速升级 & UI 提示增强

### 功能概述

优化经验系统的升级节奏，缩短输入加分间隔、提高经验获取量；同时在 UI 上增加更多提示信息，让用户明确感知这是经验系统以及如何获取经验。

### 常量调整

| 参数 | 旧值 | 新值 | 说明 |
|------|------|------|------|
| `INPUT_DEBOUNCE_MS` | 2000 | 800 | 输入防抖从 2 秒缩短到 0.8 秒，打字加分更快触发 |
| `INPUT_REWARD_EXP` | 0.5 | 1 | 每次有效输入经验翻倍，从 0.5 提升到 1 |
| `DAILY_SUBMIT_LIMIT` | 5 | 10 | 每日提交奖励上限翻倍，从 5 次提升到 10 次 |

### UI 提示增强

**Sidebar 经验区域**（`components/Sidebar.vue`）：
- 新增标题行 `⚡ 经验系统 · 记录即成长`，让用户一眼识别这是经验系统
- 进度条加粗（h-1 → h-1.5），视觉更醒目
- 底部新增提示文字：`输入 +1 EXP · 提交 +30 EXP · 每日最多10次提交奖励`
- 飘字位置上移（bottom: 40px → 60px），避免与新增标题重叠

**MemoriesPage 提交反馈**（`pages/MemoriesPage.vue`）：
- 提交记忆成功后主动调用 `spawnFloating(30)` 显示 `+30 EXP` 飘字
- 用户现在能直观看到提交获得的经验奖励

### 文件改动

| 文件 | 改动 |
|------|------|
| `types/experience.ts` | `INPUT_DEBOUNCE_MS` 2000→800, `INPUT_REWARD_EXP` 0.5→1, `DAILY_SUBMIT_LIMIT` 5→10 |
| `components/Sidebar.vue` | 经验区域新增标题行、提示文字、进度条加粗、飘字位置调整 |
| `pages/MemoriesPage.vue` | 提交成功后调用 `spawnFloating(30)` 显示飘字反馈 |

---

## 2026-07-01 — 经验系统（模块一~五）

### 功能概述

为应用新增游戏化经验系统，用户通过输入文字和提交日记获取经验值，逐级晋升阶级，满级后可重生获得星级。支持自定义头衔、晋升特效、防抖输入计经验等机制。

### 核心约定

- 统一 `storageService` 封装 localStorage，键名 `app_exp_data`，所有模块通过此服务读写，不直接操作 localStorage
- 预留 Electron 迁移注释：替换 `get()/set()` 内部实现为 `electron-store` 或 `fs` 即可
- 存储服务写在单独文件 `services/storageService.ts`

### 模块一：侧边栏占位与存储服务初始化

**文件改动：**

| 文件 | 改动 |
|------|------|
| `types/experience.ts` | 新建：ExperienceData 接口、阶级常量（阈值/名称/颜色）、存储键名、奖励常量 |
| `services/storageService.ts` | 新建：统一存储服务，get/set/update/calcTierIndex/calcProgress 方法 |
| `stores/experience.ts` | 新建：Pinia store，响应式状态 + load/persist/addExp/onInput/claimSubmitReward/spawnFloating |
| `components/Sidebar.vue` | 底部新增 64px 经验系统占位区域 |

**默认数据：** totalExp=10, rebirthStar=0, todaySubmissions=0, lastSubmitDate=今天, customTierNames=[], effectsEnabled=true

### 模块二：输入计经验与阶级映射

**阶级体系：**

| 阈值 | 阶级 | 颜色 |
|------|------|------|
| 0 | 麻瓜 | 白（gray-400） |
| 50 | 新生 | 绿（green-400） |
| 200 | 级长 | 蓝（blue-400） |
| 500 | 魁地奇队长 | 紫（purple-400） |
| 1000 | 傲罗 | 金（yellow-400） |
| 2000 | 梅林勋章 | 红（red-400） |

**文件改动：**

| 文件 | 改动 |
|------|------|
| `stores/experience.ts` | tierIndex/tierName/tierLevel/tierColorClass/tierBarColorClass/progress/isMaxTier/displayText 计算属性 |
| `components/Sidebar.vue` | 阶级文字（动态颜色）+ 进度条（动态宽度+颜色） |
| `pages/MemoriesPage.vue` | textarea `@input="exp.onInput()"` |
| `pages/MemoryDetailPage.vue` | textarea `@input="exp.onInput()"` |

### 模块三：进度条、提交奖励与飘字特效

**文件改动：**

| 文件 | 改动 |
|------|------|
| `components/Sidebar.vue` | TransitionGroup 飘字 "+X EXP" 1.5s 上浮动画；满级进度条 animate-pulse |
| `pages/MemoriesPage.vue` | createMutation onSuccess 调用 `exp.claimSubmitReward()` |
| `pages/MemoryDetailPage.vue` | updateMutation onSuccess 调用 `exp.claimSubmitReward()` |

**规则：**
- 提交奖励：+30 EXP，每日限 5 次，跨日重置
- 飘字：CSS `floatUp` keyframes（opacity 1→0, translateY 0→-32px, 1.5s）

### 模块四：进阶特效与自定义头衔

**文件改动：**

| 文件 | 改动 |
|------|------|
| `types/experience.ts` | 新增 `effectsEnabled: boolean`、`MAX_EXP=2000`、`INPUT_DEBOUNCE_MS=2000` |
| `services/storageService.ts` | `getTierName()` 支持自定义名称参数，空则回退默认 |
| `stores/experience.ts` | 防抖 `onInput()`（2秒后结算）；`watch(tierIndex)` 晋升检测触发摇晃+闪白；`toggleEffects()`；`updateCustomTierNames()`/`resetCustomTierNames()` |
| `components/Sidebar.vue` | `.shake` CSS 动画 0.3s；全屏闪白 `<Transition name="flash">`（受 effectsEnabled 控制） |
| `pages/SettingsPage.vue` | 新增经验系统面板：特效开关 toggle + 6个头衔输入框（placeholder 为默认名）+ 保存/重置按钮 |

### 模块五：满级溢出与重生机制

**文件改动：**

| 文件 | 改动 |
|------|------|
| `services/storageService.ts` | `rebirth()` 方法：经验≥2000 时扣减 + 星级+1 |
| `stores/experience.ts` | `doRebirth()` 动作；`canRebirth`/`starText` 计算属性 |
| `components/Sidebar.vue` | 重生按钮 `<RotateCw>`（v-if="canRebirth"）；星级显示 `⭐ × N` |

**规则：**
- 满级（≥2000 EXP）经验不封顶，进度条恒 100% + 脉动
- 重生：扣减 2000 EXP + 星级 +1，阶级重新映射
- 星级 0 时不显示星级文本

### 交互细节

- **输入防抖**：每次 input 事件累积 0.5 EXP，停止输入 2 秒后统一结算并飘字
- **晋升特效**：阶级提升时侧边栏摇晃 0.3s + 全屏闪白 0.2s，受特效开关控制
- **自定义头衔**：输入框 placeholder 为默认名称，空值回退默认，保存时仅存非默认项
- **重生按钮**：仅满级时显示，点击即扣减经验+增加星级

---

## 2026-06-30 — Bug 修复：记忆列表无法加载 & 收藏筛选失效

### Bug 1：记忆列表空白，API 报错

**根因**：`memory_service.get_all()` 方法签名缺少 `favorite` 参数，但路由层调用时传了 4 个参数，方法体内部也引用了未定义的 `favorite` 变量，导致 `NameError`，`/api/memories` 接口直接 500。

**修复**：
| 文件 | 改动 |
|------|------|
| `services/memory_service.py` | `get_all()` 签名添加 `favorite: Optional[bool] = None` 参数；文件顶部添加 `from typing import Optional` |

### Bug 2：点击「已收藏」筛选按钮无反应

**根因**：`MemoriesPage.vue` 的 `useQuery` 中 `queryKey` 使用了 `page.value` 和 `showFavoritesOnly.value`，这些值在组件初始化时求值后固定，切换收藏状态时 queryKey 不变，不会触发重新请求。

**修复**：
| 文件 | 改动 |
|------|------|
| `pages/MemoriesPage.vue` | `queryKey` 从 `['memories', page.value, showFavoritesOnly.value]` 改为 `['memories', page, showFavoritesOnly]`，让 `@tanstack/vue-query` v5 自动追踪 ref 变化 |

### 其他改动
| 文件 | 改动 |
|------|------|
| `frontend/vite.config.ts` | 添加 `host: '0.0.0.0'` 支持局域网访问 |
| `start_servers.bat` | vite 启动命令加上 `--host 0.0.0.0` |

---

## 2026-06-29 — 收藏记忆功能

### 功能概述

为记忆条目新增收藏（favorite）功能，用户可以点击星星收藏记忆，并在记忆总览中筛选仅查看已收藏的记忆。

### 后端改动

| 文件 | 改动 |
|------|------|
| models/memory.py | Memory 模型新增 favorite: bool 字段，默认 False；导入 Boolean |
| schemas/memory.py | MemoryRequest / UpdateMemoryRequest / MemoryResponse 均添加 favorite 字段 |
| services/memory_service.py | create() 传递 favorite；update() 处理 favorite 更新；get_all() 新增 favorite 筛选参数；_to_response() 输出 favorite |
| routes/memories.py | GET /api/memories 新增 ?favorite=true/false 查询参数 |
| alembic/versions/dcaa1b9086ad_add_favorite_to_memory.py | 数据库迁移：添加 favorite 列（兼容 SQLite NOT NULL 约束） |

### 前端改动

| 文件 | 改动 |
|------|------|
| types/index.ts | Memory 接口添加 favorite?: boolean |
| api/index.ts | getMemories() 支持 favorite 参数；新增 toggleFavoriteMemory() API |
| pages/MemoriesPage.vue | 每个记忆卡片右下角增加星星收藏按钮（已收藏时填充黄色）；标题栏新增「全部 / 已收藏」筛选切换按钮；点击星星通过 mutation 切换收藏状态 |
| pages/MemoryDetailPage.vue | 详情页头部新增收藏星星按钮 |

### 交互细节

- 星星按钮：灰色空心 = 未收藏，黄色实心 = 已收藏，点击切换
- 筛选按钮：点击「已收藏」仅显示 favorite=true 的记忆，点击「全部」恢复全部显示
- 列表页星星：使用 @click.prevent + @click.stop 避免触发卡片链接跳转
- 详情页星星：编辑模式下隐藏，仅在查看模式显示

## 2026-06-29 — 收藏记忆功能

### 功能概述

为记忆条目新增收藏（favorite）功能，用户可以点击星星收藏记忆，并在记忆总览中筛选仅查看已收藏的记忆。

### 后端改动

| 文件 | 改动 |
|------|------|
| `models/memory.py` | `Memory` 模型新增 `favorite: bool` 字段，默认 `False`；导入 `Boolean` |
| `schemas/memory.py` | `MemoryRequest` / `UpdateMemoryRequest` / `MemoryResponse` 均添加 `favorite` 字段 |
| `services/memory_service.py` | `create()` 传递 `favorite`；`update()` 处理 `favorite` 更新；`get_all()` 新增 `favorite` 筛选参数；`_to_response()` 输出 `favorite` |
| `routes/memories.py` | `GET /api/memories` 新增 `?favorite=true/false` 查询参数 |
| `alembic/versions/dcaa1b9086ad_add_favorite_to_memory.py` | 数据库迁移：添加 `favorite` 列（兼容 SQLite NOT NULL 约束） |

### 前端改动

| 文件 | 改动 |
|------|------|
| `types/index.ts` | `Memory` 接口添加 `favorite?: boolean` |
| `api/index.ts` | `getMemories()` 支持 `favorite` 参数；新增 `toggleFavoriteMemory()` API |
| `pages/MemoriesPage.vue` | 每个记忆卡片右下角增加星星收藏按钮（已收藏时填充黄色）；标题栏新增「全部 / 已收藏」筛选切换按钮；点击星星通过 mutation 切换收藏状态 |
| `pages/MemoryDetailPage.vue` | 详情页头部新增收藏星星按钮 |

### 交互细节

- **星星按钮**：灰色空心 = 未收藏，黄色实心 = 已收藏，点击切换
- **筛选按钮**：点击「已收藏」仅显示 `favorite=true` 的记忆，点击「全部」恢复全部显示
- **列表页星星**：使用 `@click.prevent` + `@click.stop` 避免触发卡片链接跳转
- **详情页星星**：编辑模式下隐藏，仅在查看模式显示

---

## 2026-06-29 — 收藏计忆功能

### 功能概述

为计忆条目新增收藏（favorite）功能，用户可以点击星星收藏计忆，并在计忆总览中组箚仅查看已收藏的计忆。

### 后端改功

| 文件 | 改功 |
|------|------|
| models/memory.py | Memory 模型新增 favorite: bool 字录，默认 False；导入 Boolean |
| schemas/memory.py | MemoryRequest / UpdateMemoryRequest / MemoryResponse 均添加 favorite 字彗 |
| services/memory_service.py | create() 传功 favorite；update() 处理 favorite 更新；get_all() 新增 favorite 箚功参功；_to_response() 输出 favorite |
| routes/memories.py | GET /api/memories 新增 ?favorite=true/false 查诲参功 |
| alembic/.../dcaa1b9086ad_add_favorite_to_memory.py | 数据功辿功：新增 favorite 列（兼功 SQLite NOT NULL 约功） |

### 功端改功

| 文件 | 改功 |
|------|------|
| types/index.ts | Memory 接口添加 favorite?: boolean |
| api/index.ts | getMemories() 支持 favorite 参功；新增 toggleFavoriteMemory() API |
| pages/MemoriesPage.vue | 条目右下角星星收藏按钮（已收藏时为黄色塞充）；标标条新增「全部 / 已收藏」箚功切换 |
| pages/MemoryDetailPage.vue | 辌总功处标标新增收藏星星按钮 |

### 交互细功

- 星星按钮：组色空功 = 未收藏，黄色塞充 = 已收藏，点击切换
- 箚功按钮：点击「已收藏」仅查看 favorite=true，点击「全部」功功全部
- 列表功星星：@click.prevent + @click.stop 避功角功卡片钾功链辿链辿换功
- 辌总功星星：编边功功下功理，仅查看功功显功


## 2026-06-28 鈥?鐭ヨ瘑鍥捐氨鑺傜偣鎮诞 tooltip + TypeScript 绫诲瀷淇

### 鐭ヨ瘑鍥捐氨鑺傜偣鎮诞鏄剧ず瀹屾暣璇嶆潯

鍔涘鍚戝浘鍜屾€濈淮瀵煎浘妯″紡涓嬶紝鑺傜偣鍚嶇О瓒呰繃鎴柇闀垮害鏃舵樉绀虹渷鐣ュ彿锛岄紶鏍囨偓娴樉绀哄畬鏁村悕绉般€?
**瀹炵幇缁嗚妭锛?*
- 鍔涘鍚戝浘锛氳妭鐐瑰悕绉拌秴杩?12 瀛楃鎴柇涓?`鍓?1瀛楃鈥
- 鎬濈淮瀵煎浘锛氳妭鐐瑰悕绉拌秴杩?14 瀛楃鎴柇涓?`鍓?3瀛楃鈥
- 鑷畾涔?tooltip 缁勪欢锛堟浛浠ｆ祻瑙堝櫒鍘熺敓 `<title>`锛?  - 鏄剧ず鍦ㄩ紶鏍囧彸涓婅锛坸 鍚戝彸鍋忕Щ 12px锛寉 鍚戜笂鍋忕Щ 36px锛?  - 璺熼殢榧犳爣绉诲姩
  - 杈圭晫妫€娴嬮槻姝㈣秴鍑哄彲瑙嗗尯鍩?  - 浣跨敤 shadcn-vue 鏍峰紡鍙橀噺锛坆g-popover / text-popover-foreground / border-border锛?
**鍓嶇鏀瑰姩锛?*
- `GraphPage.vue`锛?  - 鏂板 `tooltip` ref + `showTooltip / moveTooltip / hideTooltip` 鍑芥暟
  - 鍔涘鍚戝浘鑺傜偣娣诲姞 `mouseenter / mousemove / mouseleave` 浜嬩欢
  - 鎬濈淮瀵煎浘鑺傜偣娣诲姞鍚屾牱鐨勪簨浠?  - 鏂板 tooltip DOM 鍏冪礌锛堢粷瀵瑰畾浣嶏紝璺熼殢榧犳爣锛?
### TypeScript 绫诲瀷淇

淇 32 涓被鍨嬮敊璇紝`vue-tsc --noEmit` 妫€鏌ラ€氳繃銆?
**淇鍐呭锛?*
| 鏂囦欢 | 闂 | 淇 |
|------|------|------|
| `package.json` | d3 缂哄皯绫诲瀷澹版槑 | 瀹夎 `@types/d3` |
| `GraphPage.vue` | d3 鍥炶皟鍙傛暟闅愬紡 any | 娣诲姞鏄惧紡 `any` 绫诲瀷锛坉3 绫诲瀷绯荤粺澶嶆潅锛?|
| `HomePage.vue` | `m.createdAt` 鍙兘涓?undefined | `m.createdAt || ''` |
| `MemoriesPage.vue` | 鍚屼笂 | `m.createdAt || ''` |
| `MemoryDetailPage.vue` | 鍚屼笂 | `memory.createdAt || ''` |
| `stores/memory.ts` | `new Date(undefined)` 鎶ラ敊 | `new Date(b.createdAt || 0)` |

---

## 2026-06-27 鈥?鏂板褰╄壊澶ф爣绛惧垎绫?& 璁板繂缂栬緫鍔熻兘 & 鍥捐氨/鍒嗘瀽鎸夊ぇ鏍囩绛涢€?
### 澶ф爣绛惧姛鑳?
鏂板鍥涚褰╄壊澶ф爣绛惧垎绫伙紝鍖哄埆浜庢櫘閫氬皬鏍囩锛?
| 澶ф爣绛?| 棰滆壊 | 鍥炬爣 |
|--------|------|------|
| 鐭ヨ瘑鐐?(KNOWLEDGE_POINT) | 钃濊壊 | 馃摎 |
| 闅忓績璁拌堪 (FREEFORM_NOTE) | 缈犵豢 | 鉁嶏笍 |
| 鐏垫劅闂幇 (INSPIRATION_FLASH) | 鐞ョ弨 | 馃挕 |
| 鍐崇瓥绾犵粨 (DECISION_DILEMMA) | 鐜孩 | 鈿栵笍 |

**鍚庣鏀瑰姩锛?*
- `models/memory.py`锛氭柊澧?`BigTag` 鏋氫妇锛宍Memory` 琛ㄦ柊澧?`big_tag` 鍙€夊垪
- `schemas/memory.py`锛歚MemoryRequest` / `MemoryResponse` 鏂板 `big_tag` 瀛楁
- `services/memory_service.py`锛氬垱寤?鏇存柊璁板繂鏃惰В鏋愬苟淇濆瓨 `big_tag`
- `routes/analytics.py`锛歚/api/graph` 鍜?`/api/analytics/sentiment` 鏂板 `?big_tag=` 鏌ヨ鍙傛暟
- `alembic/versions/66137253b388_add_big_tag_to_memory.py`锛氳縼绉绘枃浠?
**鍓嶇鏀瑰姩锛?*
- `types/index.ts`锛氭柊澧?`BigTagCategory` 绫诲瀷锛宍Memory` 鎺ュ彛娣诲姞 `bigTag`
- `lib/utils.ts`锛氭柊澧?`BIG_TAG_CONFIG`銆乣bigTagClass()`銆乣bigTagLabel()` 宸ュ叿鍑芥暟
- `pages/MemoriesPage.vue`锛氬垱寤鸿〃鍗曟柊澧炲僵鑹插ぇ鏍囩閫夋嫨鍣紱璁板繂鍗＄墖宸︿笂瑙掓樉绀哄ぇ鏍囩瑙掓爣
- `pages/MemoryDetailPage.vue`锛氳鎯呴〉澶撮儴鏄剧ず澶ф爣绛惧窘绔?- `pages/HomePage.vue`锛氶椤佃蹇嗗崱鐗囧乏涓婅鏄剧ず澶ф爣绛捐鏍?- `pages/GraphPage.vue`锛氭柊澧炲ぇ鏍囩绛涢€夋寜閽锛屽彲鍒囨崲鏌ョ湅鍏ㄩ儴/鐗瑰畾澶ф爣绛剧殑鐭ヨ瘑鍥捐氨
- `pages/AnalyticsPage.vue`锛氭柊澧炲ぇ鏍囩绛涢€夋寜閽锛屾儏鎰熻秼鍔垮彲鎸夊ぇ鏍囩杩囨护

### 璁板繂缂栬緫鍔熻兘

鐢ㄦ埛鐜板湪鍙互淇敼宸叉湁璁板繂鐨勬墍鏈夊睘鎬э細

**鍚庣鏀瑰姩锛?*
- `schemas/memory.py`锛氭柊澧?`UpdateMemoryRequest`锛堟墍鏈夊瓧娈靛彲閫夛級
- `routes/memories.py`锛氭柊澧?`PUT /api/memories/{id}` 绔偣
- `services/memory_service.py`锛氭柊澧?`update()` 鏂规硶锛屾敮鎸佷慨鏀规爣棰?鍐呭/澶ф爣绛?灏忔爣绛?鏉ユ簮URL

**鍓嶇鏀瑰姩锛?*
- `api/index.ts`锛氭柊澧?`updateMemory()` API 璋冪敤
- `pages/MemoryDetailPage.vue`锛氭柊澧炵紪杈戞寜閽紙绗斿浘鏍囷級锛岀偣鍑诲睍寮€缂栬緫琛ㄥ崟锛屽彲淇敼锛氭爣棰樸€佸ぇ鏍囩銆佹潵婧怳RL銆佸唴瀹广€佸皬鏍囩

### 淇

- `GraphPage.vue` / `AnalyticsPage.vue`锛氫慨澶嶅ぇ鏍囩绛涢€?`queryKey` 涓嶅搷搴斿紡鐨勯棶棰橈紝鏀圭敤 `computed(() => [...])`
- `MemoriesPage.vue` / `HomePage.vue`锛氬ぇ鏍囩瑙掓爣浠庡彸涓婅绉诲埌宸︿笂瑙掞紝閬垮厤涓庢棩鏈熼噸鍙?
---

## 2026-06-25 鈥?鎬濈淮瀵煎浘淇澶氳繛閫氬垎閲忎涪澶?& 闀胯瘝鏉℃埅鏂?& 棣栭〉鍔ㄦ€侀棶鍊欒

### 鎬濈淮瀵煎浘澶氳繛閫氬垎閲忎涪澶?
鏍瑰洜锛歚buildHierarchy()` 浠庢渶杩為€氳妭鐐癸紙Vue3锛夊嚭鍙戝仛 BFS 寤烘爲銆侶TML鈫扗OM妯℃澘鈫?..鈫抲serName 閾炬槸涓€涓嫭绔嬭繛閫氬垎閲忥紙涓?Vue3 鏃犵洿杩炶竟锛夛紝BFS 閬嶅巻涓嶅埌锛屼絾瀹冧滑鍙堜笉鏄绔嬭妭鐐癸紙鍐呴儴鏈夎竟锛夛紝鏁存潯閾捐涓㈠純銆?
淇锛欱FS 缁撴潫鍚庢壂鎻忔湭璁块棶鐨勮繛閫氳妭鐐癸紝瀵规瘡涓墿浣欏垎閲忓崟鐙缓 BFS 鏍戯紝浣滀负铏氭嫙鏍圭殑鐙珛瀛愬垎鏀紙涓?Vue3 骞跺垪锛夈€?
### 闀胯瘝鏉℃埅鏂?
鏍瑰洜锛歚Eduardo San Martin Morote`銆乣Object.defineProperty` 绛夐暱璇嶅湪鏍戜笂鍨傜洿闂磋窛涓嶅锛屾尋鍦ㄤ竴璧枫€?
淇锛?- 鍚嶇О瓒呰繃 14 瀛楃鑷姩鎴柇涓?`鍓?3瀛楃鈥
- 姣忎釜鑺傜偣娣诲姞 `<title>` 鍏冪礌锛岄紶鏍囨偓鍋滄樉绀哄畬鏁村悕绉?- 鑺傜偣闂磋窛浠?`1:1.5` 鍔犲ぇ鍒?`1.2:1.8`

### 棣栭〉鍔ㄦ€侀棶鍊欒

鏂板 `frontend/src/composables/useGreeting.ts`锛屾寜鏃堕棿娈甸殢鏈烘娊鍙栭棶鍊欒锛?- 鏃╀笂 (6:00-12:00)锛? 绉?- 涓嬪崍 (12:00-18:00)锛? 绉?- 鏅氫笂 (18:00-23:00)锛? 绉?- 鍑屾櫒 (23:00-6:00)锛? 绉?
棣栭〉鏍囬浠庡浐瀹?浣犵殑绗簩澶ц剳"鏀逛负鍔ㄦ€?`{{ greeting }}`銆?
## 2026-06-25 鈥?鎬濈淮瀵煎浘瀛ょ珛鑺傜偣淇锛堢嫭绔嬫牴鑺傜偣锛?
### 鐞嗙敱

鐭ヨ瘑鍥捐氨鐨勬€濈淮瀵煎浘妯″紡涓嬶紝瀛ょ珛鑺傜偣锛堝 `姗樼绂廯锛屾潵鑷?缁濆尯闆?璁板繂锛屼笌 Vue3 鏃犱换浣曞叧鑱旓級琚敊璇湴褰掑叆 Vue3 涓嬫柟鐨?鍏朵粬"瀹瑰櫒锛岀湅璧锋潵鍍忔槸 Vue3 鐨勫瓙鑺傜偣銆傜敤鎴峰笇鏈涘绔嬭妭鐐逛綔涓?*鐙珛鏍硅妭鐐?*锛屼笌 Vue3 骞崇骇灞曠ず銆?
### 鏍瑰洜

- `buildHierarchy()` 灏嗗绔嬭妭鐐圭粺涓€濉炶繘 `__isolated__`锛?鍏朵粬"锛夊鍣紝鍐嶆寕鍒颁富鏍戞牴锛圴ue3锛夌殑 children 涓?- 杩欐牱瀛ょ珛鑺傜偣鍙樻垚 Vue3 鐨勪簩绾у瓙鑺傜偣锛岃涔夐敊璇?
### 鍓嶇淇

- `frontend/src/pages/GraphPage.vue`锛?  - `buildHierarchy()` 涓嶅啀鍒涘缓"鍏朵粬"瀹瑰櫒銆傛敼涓鸿繑鍥炰竴涓?*铏氭嫙鏍硅妭鐐?* `__virtual__`锛屽叾 children 涓?`[Vue3鏍戞牴, 姗樼绂? ...鍏朵粬瀛ょ珛鑺傜偣]`锛岃瀛ょ珛鑺傜偣涓?Vue3 骞崇骇鎴愪负鐙珛鍒嗘敮
  - `renderTree()` 闅愯棌铏氭嫙鏍硅妭鐐癸紙鍦嗙偣 r=0銆佹枃瀛?opacity=0锛夛紝骞惰繃婊ゆ帀浠庤櫄鎷熸牴鍑哄彂鐨勮繛绾匡紙`root.links().filter(l => l.source.data.id !== '__virtual__')`锛夛紝鐢ㄦ埛鍙湅鍒?Vue3 鍜?姗樼绂?涓や釜鐙珛鏍?  - 鑷姩灞呬腑璁＄畻鎺掗櫎铏氭嫙鏍硅妭鐐癸紝閬垮厤瀹冨奖鍝嶈竟鐣屾
  - 鏍硅妭鐐瑰渾鐐瑰崐寰勫垽鏂粠 `d.depth === 0` 鏀逛负 `d.depth === 1`锛堝洜涓鸿櫄鎷熸牴鍗犱簡 depth 0锛?
### 楠岃瘉

- 鎬濈淮瀵煎浘妯″紡锛?9 涓渾鐐癸紙1 涓?r=0 铏氭嫙鏍归殣钘?+ 2 涓?r=10 鐙珛鏍?`Vue3`/`姗樼绂廯 + 46 涓?r=6 瀛愯妭鐐癸級
- `Vue3` 鍜?`姗樼绂廯 鍦ㄥ悓涓€ x 鍧愭爣锛岀‘璁や袱鑰呮繁搴︾浉鍚屻€佷簰涓哄厔寮?- 鍔涘鍚戝浘妯″紡涓嶅彈褰卞搷锛宍姗樼绂廯 浠嶆槸鍗曠嫭鐨勬偓娴妭鐐?
## 2026-06-24 鈥?淇鐭ヨ瘑鍥捐氨涓庢儏鎰熷垎鏋愶紙鎺ュ叆瀹炰綋鎻愬彇锛?
### 鐞嗙敱

鐭ヨ瘑鍥捐氨鍜屾儏鎰熷垎鏋愰〉闈㈠缁堜负绌恒€傛牴鍥犳槸鍚庣鍒涘缓璁板繂鏃朵粠鏈皟鐢?LLM 瀹炰綋鎻愬彇锛宍KnowledgeEntity`銆乣Relation`銆乣Memory.sentiment` 濮嬬粓鏃犳暟鎹€?
### 鏍瑰洜

- `memory_service.create()` 鍙仛浜?embedding锛屾病鏈夎皟鐢?`llm_service.extract_entities()`
- `llm_service` 浣跨敤 `with_structured_output()`锛孌eepSeek 涓嶅吋瀹?OpenAI parse 绔偣锛岄潤榛樺け璐?- LLM 璋冪敤鏃犺秴鏃朵繚鎶わ紝缃戠粶涓嶉€氭椂浼氬崱浣忔暣涓姹?
### 鍚庣淇

- `memory_service.py`锛?  - 鏂板 `_process_background()`锛屽垱寤鸿蹇嗗悗鑷姩鎻愬彇瀹炰綋銆佹儏鎰熴€佺敓鎴?embedding
  - 瀹炰綋鍐欏叆 `KnowledgeEntity` 琛紝璁板繂涓庡疄浣撳叧鑱斿啓鍏?`MemoryEntity`
  - 杩炵画瀹炰綋闂村垱寤?`Relation`锛坈o-occurrence 鍏崇郴锛夛紝鐭ヨ瘑鍥捐氨鏈夎繛绾?  - 鎯呮劅鍐欏叆 `Memory.sentiment`锛屾儏鎰熷垎鏋愰〉闈㈡湁鏁版嵁
  - 浣跨敤鐙珛 session锛坄async_session_factory()`锛夐伩鍏?greenlet 閿欒
- `llm_service.py`锛?  - `extract_entities()` 浠?`with_structured_output()` 鏀逛负鏅€?chat + JSON 鎵嬪姩瑙ｆ瀽锛屽吋瀹?DeepSeek
  - 鎵€鏈?LLM HTTP 璋冪敤鍔犱笂 `httpx.Timeout(60.0)` 瓒呮椂
  - `generate_embedding()` 浠?ChromaDB 鐨?embedding function 鏀逛负璋冪敤 DeepSeek/OpenAI embeddings API

### 楠岃瘉

- 鐭ヨ瘑鍥捐氨椤甸潰鏈?59 涓妭鐐瑰拰杩炵嚎
- 鎯呮劅鍒嗘瀽椤甸潰鏈夎秼鍔挎姌绾垮浘
- 璁板繂璇︽儏椤垫樉绀烘儏鎰熸爣绛?
## 2026-06-23 鈥?鎺ュ叆 DeepSeek v4-flash & 绮剧畝璁板繂绫诲瀷

### 鐞嗙敱

鍥戒骇 API锛圖eepSeek锛夊湪涓枃鍦烘櫙琛ㄧ幇鏇村ソ锛屼笖 OpenAI 鍏煎鍗忚浣垮緱鍒囨崲鎴愭湰鏋佷綆銆傚悓鏃剁簿绠€璁板繂绫诲瀷锛岃闊冲拰閾炬帴鐩墠娌℃湁瀹炵幇璺緞锛屼繚鐣欏彧浼氶€犳垚娣锋穯銆?
### LLM 鎺ュ叆鍙樻洿

- `config.py`锛氶粯璁?provider 鏀逛负 `deepseek`锛岄粯璁ゆā鍨?`deepseek-v4-flash`
- `llm_service.py`锛氭柊澧?`PROVIDER_DEFAULTS` 瀛楀吀锛屾牴鎹?provider 鑷姩閫夌敤 base_url 鍜屾ā鍨?  - DeepSeek: `https://api.deepseek.com` + `deepseek-v4-flash`
  - 鍓嶇璁剧疆椤靛～鍏?API Key 鍚庤嚜鍔ㄦ寔涔呭寲鍒?localStorage锛宎xios 鎷︽埅鍣ㄨ嚜鍔ㄩ檮鍔?`X-API-Key` 澶?- `.env.example`锛氱簿绠€涓轰粎 DeepSeek 閰嶇疆绀轰緥

### 璁板繂绫诲瀷绮剧畝

绉婚櫎 `AUDIO`锛堣闊筹級鍜?`LINK`锛堥摼鎺ワ級锛屼粎淇濈暀 `TEXT` 鍜?`IMAGE`锛?- `models/memory.py`锛歁emoryType 鏋氫妇鍙繚鐣?TEXT / IMAGE
- `frontend/src/types/index.ts`锛歵ype 瀛楁绫诲瀷鍚屾绮剧畝
- `frontend/src/lib/utils.ts`锛歵ypeIcon 鍙繚鐣?TEXT / IMAGE
- `frontend/src/pages/MemoriesPage.vue`锛氫笅鎷夐€夐」鍜?LINK 涓撳睘杈撳叆妗嗗凡绉婚櫎

---

## 2026-06-18 鈥?鏈湴鍖栭噸鏋勶細MySQL/Redis/Qdrant 鈫?SQLite + ChromaDB + 鍐呭瓨缂撳瓨

### 鐞嗙敱

Docker 渚濊禆澶噸锛圡ySQL + Redis + Qdrant 涓変釜瀹瑰櫒锛夛紝鏈湴寮€鍙戝惎鍔ㄩ摼璺暱銆傜洰鏍囷細闆朵緷璧栫洿鎺ヨ繍琛岋紝鍚屾椂淇濈暀 Docker 妯″紡浣滀负鍙€夋柟妗堛€?
### 鏁版嵁搴撴浛鎹?
| 鍘?| 鏂?| 璇存槑 |
|------|------|------|
| MySQL + asyncmy | SQLite + aiosqlite | 闆堕厤缃紝鍗曟枃浠舵暟鎹簱 |
| Redis | 鍐呭瓨缂撳瓨 | 闄愭祦/缂撳瓨鐢?Python dict 鏇夸唬 |
| Qdrant | ChromaDB | 鍚戦噺瀛樺偍宓屽叆杩涚▼鍐?|

### 鏍稿績鏀瑰姩

- `config.py`锛氭柊澧?Settings 绫?(pydantic-settings)锛屾敮鎸?.env 鍜岀幆澧冨彉閲忥紱is_docker 鑷姩妫€娴?- `db/session.py`锛氭暟鎹簱 URL 鏍规嵁 is_docker 鑷姩鍒囨崲 (mysql+asyncmy:// vs sqlite+aiosqlite://)
- `redis_service.py`锛氭暣鏂囦欢鏀逛负鍐呭瓨缂撳瓨瀹炵幇锛坃MemoryStore锛夛紝淇濇寔鏂规硶绛惧悕涓嶅彉
- `pyproject.toml`锛氫緷璧栦粠 asyncmy/pymysql/redis/qdrant-client 鎹负 aiosqlite/chromadb锛宒ev 鍔?pyinstaller

### 鍓嶇鏀瑰姩

- `api/index.ts`锛歜aseURL 鏀逛负 `import.meta.env.VITE_API_BASE || '/api'`锛屾敮鎸佹闈㈢瀹屾暣 URL
- `env.d.ts`锛氬０鏄?ImportMetaEnv 鍜?window.pensieve 绫诲瀷
- `package.json`锛歜uild 鍘绘帀 vue-tsc -b锛堝姞蹇瀯寤猴級锛屾柊澧?build:strict

### .gitignore 鏇存柊

鎺掗櫎 build 浜х墿锛歠rontend/dist/銆?.tsbuildinfo銆乿ite.config.js/d.ts銆乥ackend/build/銆乥ackend/dist/銆乪lectron/release/

### 鏁版嵁娴侊紙妗岄潰绔級

Electron main.js 鍚姩鍚?spawn pensieve_backend.exe (PyInstaller 鎵撳寘鐨勫悗绔?锛岄€氳繃 uvicorn 杩愯 FastAPI 鏈嶅姟璇诲啓 SQLite + ChromaDB銆傚墠绔敱 BrowserWindow 鍔犺浇闈欐€佹枃浠讹紝axios 璇锋眰鍙戝線 127.0.0.1:8080/api銆?
### 褰撳墠鐘舵€?
- 妗岄潰绔灦鏋勬惌寤哄畬鎴?- 鍚庣鏈嶅姟鎺ュ彛涓嶅彉锛屼笟鍔″眰闆舵敼鍔?- 鎵撳寘娴佺▼灏辩华锛坋lectron/scripts/build.js锛?- 寰呭悗缁細瀹為檯鎵撳寘娴嬭瘯 + 妗岄潰绔?UI 閫傞厤

---

## 2026-06-17 鈥?鍓嶇瀵规帴鐪熷疄 API + 璁剧疆椤典慨澶?+ 鏂板鍚庣绔偣

### 鍓嶇鏀瑰姩

| 鏂囦欢 | 鏀瑰姩 |
|------|------|
| api/index.ts | createMemory 鏀?JSON 浣擄紱searchMemories 鏀逛负 getMemories (GET)锛涙柊澧?getRecentMemories锛涙坊鍔?axios 鎷︽埅鍣ㄨ嚜鍔?snake_case鈫抍amelCase |
| types/index.ts | 瀵归綈鍚庣 PagedResponse (total_elements, total_pages) 鍜?MemoryResponse |
| HomePage.vue | 鏀圭敤 getRecentMemories 鍙栫湡瀹炴暟鎹?|
| MemoriesPage.vue | 鏀圭敤 getMemories + createMemory(JSON)锛涚Щ闄?FormData 涓婁紶 |
| SettingsPage.vue | 淇鏆楄壊妯″紡鍒囨崲鎸夐挳锛歵ranslate-x-[22px] 鏇夸唬涓嶅湪 Tailwind 闂磋窛琛ㄧ殑 translate-x-5.5锛涘姞 overflow-hidden |

### 鍚庣鏂板绔偣

| 绔偣 | 璇存槑 |
|------|------|
| GET /api/graph | 杩斿洖瀹炰綋 + 鍏崇郴鐨勭煡璇嗗浘璋辨暟鎹?(D3.js 鍙鍖? |
| GET /api/analytics/sentiment | 鎸夋棩鏈熻仛鍚堟儏鎰熻秼鍔匡紙鏀寔 ?days=7/30/90锛?|

### 鏁版嵁娴?
Vue 3 椤甸潰閫氳繃 Vue Query 鈫?axios 鈫?Vite proxy (/api 鈫?:8080) 鈫?FastAPI 鈫?SQLAlchemy 鈫?MySQL

### 褰撳墠鐘舵€?
- 鍓嶇 6 涓〉闈㈠叏閮ㄥ鎺ョ湡瀹炲悗绔?API
- 鏆楄壊妯″紡鍒囨崲鎸夐挳鍔ㄧ敾淇
- 璁板繂 CRUD锛堝垱寤?鍒楄〃/璇︽儏/鍒犻櫎锛夊叏閮ㄨ蛋 MySQL
- 鍥捐氨鍜屾儏鎰熷垎鏋愮鐐瑰氨缁紝绛夊緟 AI 瀹炰綋鎻愬彇鏁版嵁濉厖

---

## 2026-06-16 鈥?鍚庣閲嶆瀯锛歋pring Boot (Java) 鈫?FastAPI (Python)

### 鐞嗙敱

閮ㄥ垎鍔熻兘锛堝 LLM 闆嗘垚銆佸悜閲忔悳绱€丄I 浠ｇ悊锛夊湪 Python 鐢熸€佷腑鏇存垚鐔燂紝Java 鐨?LangChain4j 绛夊簱鐗堟湰婊炲悗銆佺ぞ鍖烘敮鎸佽緝寮便€傚皾璇?Python 鎶€鏈爤锛屽埄鐢?FastAPI + LangChain + Qdrant 鐨勫師鐢?Python 瀹㈡埛绔紝闄嶄綆 AI 鐩稿叧鍔熻兘鐨勬帴鍏ユ垚鏈€?
### 瀹屾垚浜嬮」

| 浜嬮」 | 璇存槑 |
|------|------|
| 鍒涘缓 python-main 鍒嗘敮 | 榛樿鍒嗘敮锛宩ava 鍒嗘敮淇濈暀 Spring Boot 鏃х増 |
| 鍒犻櫎鎵€鏈?Java 鏂囦欢 | backend/src/main/java/ + pom.xml |
| Web 妗嗘灦 | Spring Boot 鈫?FastAPI (寮傛) |
| ORM | JPA/Hibernate 鈫?SQLAlchemy (寮傛妯″紡) |
| 鏁版嵁搴撹縼绉?| ddl-auto:update 鈫?Alembic |
| Redis | Jedis/Lettuce 鈫?redis-py 寮傛 |
| Qdrant | Java Client 鈫?qdrant-client (Python) |
| LLM | LangChain4j 鈫?LangChain (Python) + OpenAI |
| Dockerfile | Java 17 鈫?Python 3.12-slim |
| docker-compose.yml | 鏂板 backend 鏋勫缓鏈嶅姟 |

### API 鎺ュ彛锛堝畬鍏ㄥ吋瀹瑰墠绔級

| 鏂规硶 | 璺緞 | 鐘舵€?|
|------|------|------|
| POST | /api/memories | OK |
| GET | /api/memories | OK 鍒嗛〉 |
| GET | /api/memories/recent | OK |
| GET | /api/memories/{id} | OK |
| DELETE | /api/memories/{id} | OK |
| GET | /api/health | OK |

### 鏈嶅姟瀹归敊

- OpenAI 瀹㈡埛绔細鎳掑姞杞斤紝鏃?API key 鏃朵笉褰卞搷鍚姩
- Qdrant 瀹㈡埛绔細鎳掑姞杞斤紝鏈繛鎺ユ椂涓嶅奖鍝嶅惎鍔?- Redis 鎿嶄綔锛歵ry/except 鍖呰９锛屾湭杩愯鏃朵紭闆呴檷绾э紙璺宠繃闄愭祦/缂撳瓨锛?
---

## 2026-06-15 鈥?鍓嶇 Vue 3 鎼缓 + 鍚庣 Spring Boot 鍒濈増 + 鍩虹璁炬柦

### 鍓嶇

| 浜嬮」 | 璇存槑 |
|------|------|
| 鍚姩鍓嶇 | npm run dev 鈫?localhost:5173 |
| 娴忚鍏ㄩ儴椤甸潰 | 棣栭〉 / 璁板繂 / 璁板繂璇︽儏 / 鐭ヨ瘑鍥捐氨 / 鎯呮劅鍒嗘瀽 / 璁剧疆 |
| 纭璺敱缁撴瀯 | 6 涓〉闈紝宸︿晶瀵艰埅 + 鏆楄壊妯″紡鍒囨崲 |

### 鍚庣

鍚姩骞朵慨澶?7 涓棶棰橈紙BOM 缂栫爜銆丒ntity 绫诲悕鍐茬獊銆丠2/MySQL 鏂硅█銆丣DBC 瀛楃闆嗙瓑锛夛紝鏈€缁堝湪 MySQL 鐢熸垚琛ㄧ粨鏋勶細

- memories锛堣蹇嗕富琛級
- entities锛堢煡璇嗗疄浣擄級
- memory_entity锛堝瀵瑰鍏宠仈锛?- relations锛堝疄浣撳叧绯伙級

闆嗘垚 Redis 缂撳瓨/闄愭祦/浠诲姟姝ラ鍔熻兘銆?
### 鍩虹璁炬柦

| 鏈嶅姟 | 鍦板潃 | 鐘舵€?|
|------|------|------|
| 鍓嶇 Vue 3 | localhost:5173 | OK |
| 鍚庣 Spring Boot | localhost:8080 | OK MySQL 鎸佷箙鍖?|
| MySQL | localhost:3306 | OK 鏈満 |
| Redis | localhost:6379 | OK Docker |
| Swagger | localhost:8080/swagger | OK |

