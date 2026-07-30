# v1.1 — 生日功能（2026-07-14）

## 2026-07-14 — 生日功能全栈实现

### 功能概述

新增完整的「生日」功能模块：用户可在设置页设定生日（仅存本地 localStorage，不上传云端），生日当天触发祝福弹窗、粒子特效、经验翻倍、AI 专属祝福、记忆回顾、愿望清单等彩蛋，所有特效均有独立开关。

### 架构设计

**隐私优先**：生日数据完全存储在浏览器 localStorage，后端不接收任何生日日期信息。唯一需要后端的场景是 AI 祝福生成，且仅查询已标记为"纳入分析"的日记内容。

**前端状态管理**：Pinia Store（Composition API 风格）+ localStorage 持久化，与现有 settings/experience/insight store 保持一致模式。

### 新增文件

| 文件 | 说明 |
|------|------|
| `frontend/src/types/birthday.ts` | 生日类型定义：BirthdayData/BirthdayWish 接口、预设祝福文案池、localStorage 键名常量 |
| `frontend/src/stores/birthday.ts` | 生日 Pinia Store：本地存储读写、日期检测（isBirthdayToday/daysUntilBirthday）、功能开关、愿望列表管理、随机徽章文案 |
| `frontend/src/components/BirthdayModal.vue` | 生日祝福弹窗：渐变标题 + 气球装饰 + 4 秒自动淡出 |
| `frontend/src/components/BirthdayEffects.vue` | 全局粒子特效：emoji 粒子上升动画（requestAnimationFrame） |
| `frontend/src/components/BirthdayWishCard.vue` | AI 祝福卡：调用后端 API + 骨架屏加载态 + 回退预设文案 |
| `frontend/src/components/BirthdayMemoryReview.vue` | 记忆回顾：去年今日日记 + 最早年份回退逻辑 |
| `frontend/src/components/BirthdayWish.vue` | 愿望清单：输入框 + 今年/往年分组 + 删除功能 |
| `frontend/src/components/BirthdayReminder.vue` | 生日前提醒条：3 天内提醒 + 可关闭（每日一次） |
| `backend/app/routes/birthday.py` | 后端 API：POST /api/birthday/wish — AI 祝福生成 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `backend/app/main.py` | 注册 birthday_router 路由 |
| `frontend/src/api/index.ts` | 添加 `generateBirthdayWish()` API 函数 |
| `frontend/src/pages/SettingsPage.vue` | 添加生日设置区域：日期选择器 + 7 个功能开关 |
| `frontend/src/stores/experience.ts` | 生日双倍经验支持：addExpImmediate 检测双倍 + 金色飘字 |
| `frontend/src/components/Sidebar.vue` | 生日徽章（3 种文案随机显示：今天你最大 / 生日快乐！ / 任性一天） |
| `frontend/src/pages/HomePage.vue` | 集成 AI 祝福卡 + 记忆回顾 + 愿望清单 + 提醒条 |
| `frontend/src/App.vue` | 集成 BirthdayModal + BirthdayEffects 全局组件 |

### 核心逻辑

**日期检测**：`isBirthdayToday` 比较月日匹配（不依赖年份），支持隐藏年份模式。

**每日一次控制**：`lastGreetingShown` / `lastAiWishShown` / `lastReminderShown` 记录 YYYY-MM-DD，与当天日期比较决定是否再次显示。

**AI 祝福生成**：后端查询过去 365 天 `privacy_status=ANALYZE` 的日记（limit 50），构建 LLM prompt 要求引用成长亮点、不少于 50 字；异常时回退预设文案。

**双倍经验**：experience store 的 `addExpImmediate` 检测 `birthdayStore.isBirthdayToday && doubleExp`，双倍时显示"🎂 +X EXP 双倍!"+"🎉 生日快乐!"金色飘字。

**徽章随机文案**：3 种文案（今天你最大 / 生日快乐！ / 任性一天）在页面加载时随机选取，会话内固定。

### 后端 API

```
POST /api/birthday/wish
Headers: X-API-Key: <key>
Response: { "wish": "AI生成的祝福文案" }
```

---

## 2026-07-15 — 时间胶囊全栈实现

### 功能概述

新增「时间胶囊」功能模块：用户可选择一篇日记封存到未来指定日期，到期后首页弹出通知提醒开封；封存期间不可查看内容，强行破拆需经历30秒冷静期倒计时。后端持久化存储，支持分页列表、状态过滤和搜索。

### 架构设计

**状态机**：`SEALED`（封存）→ `OPENED`（正常开启）/ `FORCED_OPEN`（强行破拆），通过 `status` 字段区分，`is_forced` 布尔值标记破拆。

**内容保护**：后端 `get_by_id` 仅对 `OPENED`/`FORCED_OPEN` 状态返回 `memory_content`，封存状态始终返回 `null`。

**通知机制**：首页通过 `checkReadyCapsules` API 每60秒轮询，返回到期但未开封的胶囊列表，`CapsuleNotification` 组件展示通知条。

### 新增文件

| 文件 | 说明 |
|------|------|
| `backend/app/models/capsule.py` | 数据库模型：TimeCapsule 表 + CapsuleStatus 枚举（SEALED/OPENED/FORCED_OPEN） |
| `backend/app/schemas/capsule.py` | Pydantic Schema：CapsuleCreateRequest/CapsuleResponse/CapsuleDetailResponse/CapsuleStatsResponse/CapsulePagedResponse |
| `backend/app/services/capsule_service.py` | 业务逻辑：create/get_stats/get_all/get_by_id/open_capsule/force_open/delete/check_ready |
| `backend/app/routes/capsule.py` | API 路由：8 个端点（POST/GET/GET stats/GET check-ready/GET detail/POST open/POST force-open/DELETE） |
| `frontend/src/pages/CapsulePage.vue` | 主页面：统计卡片（等待开封/已开启/破拆/已到期）+ 胶囊列表 + 分页 + 搜索 + 状态过滤 + 新增对话框（两步式：选日记→填信息） |
| `frontend/src/pages/CapsuleDetailPage.vue` | 详情页：状态横幅 + 日期信息 + 倒计时 + 开启/破拆操作 + 30秒冷静期（进度条+按钮禁用） + 内容展示/封存占位 |
| `frontend/src/components/CapsuleNotification.vue` | 首页通知：60秒轮询到期胶囊 + 延迟1.5秒显示 + 可关闭 + 点击跳转 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `backend/app/db/session.py` | `init_db` 中注册 TimeCapsule 模型，确保自动建表 |
| `backend/app/main.py` | 注册 capsule_router 路由 |
| `frontend/src/types/index.ts` | 添加 CapsuleStatus/TimeCapsule/TimeCapsuleDetail/CapsuleStats/CapsulePagedResult 类型 |
| `frontend/src/api/index.ts` | 添加 8 个胶囊 API 函数 |
| `frontend/src/router/index.ts` | 添加 /capsules 和 /capsules/:id 路由 |
| `frontend/src/components/Sidebar.vue` | 导入 Hourglass 图标，navItems 添加时间胶囊导航项 |
| `frontend/src/pages/HomePage.vue` | 引入 CapsuleNotification 组件 |

### 核心逻辑

**创建胶囊**：两步式对话框 — 第一步从最近日记中选择，第二步填写标题、开启日期（date picker，最早明天）和可选留言。

**正常开启**：验证 `status=SEALED` 且 `open_date <= now`，设为 `OPENED`，记录 `opened_at`。

**强行破拆**：无论是否到期均可破拆，设为 `FORCED_OPEN`，`is_forced=True`。前端需等待30秒冷静期倒计时归零后才可点击确认按钮，期间进度条动画显示剩余时间。

**到期通知**：`check_ready` 查询 `status=SEALED && open_date <= now` 的胶囊，返回 id/title/open_date/buried_date，首页组件每分钟轮询一次。

**分页列表**：默认每页5条，支持按状态过滤和标题/留言搜索，按创建时间倒序排列。

### 后端 API

```
POST   /api/capsules              创建胶囊
GET    /api/capsules              列表查询（?page=&size=&status=&search=）
GET    /api/capsules/stats        统计（waiting/opened/forced/ready）
GET    /api/capsules/check-ready  到期检查（首页通知用）
GET    /api/capsules/{id}         详情（封存不返回内容）
POST   /api/capsules/{id}/open    正常开启
POST   /api/capsules/{id}/force-open  强行破拆
DELETE /api/capsules/{id}         删除
```

### TypeScript 修复

- `CapsulePagedResponse.content` 类型从 `list` 修正为 `list[CapsuleResponse]`
- `:disabled` 绑定中 `mutation.isPending`（Ref 类型）用 `!!` 转布尔值，修复 TS2322 错误

---

## 2026-07-22 — 时间胶囊双来源增强

### 功能概述

时间胶囊新增两种创建来源：「从记忆库选取」和「新建自定义内容」。选择记忆库的胶囊关联已有日记，选择新建内容的胶囊自带 `content` 字段，内容独立于记忆库，不会存入日记。

### 架构设计

**互斥模型**：`memory_id`（可选）和 `content`（可选）互斥——创建时必须提供其中之一，不可同时提供。通过后端 service 层校验 + 前端三步式引导确保数据一致性。

**来源标识**：`source_type` 虚拟字段（`"memory"` / `"custom"`），由 service 层根据 `memory_id` 是否存在动态计算，不存入数据库。

**级联保护**：外键 `ondelete` 从 `CASCADE` 改为 `SET NULL`——删除关联记忆时胶囊不被级联删除，仅断开关联。

### 修改文件

| 文件 | 改动 |
|------|------|
| `backend/app/models/capsule.py` | `memory_id` 改为 `nullable=True` + `ondelete="SET NULL"`；新增 `content` 字段（Text, nullable） |
| `backend/app/schemas/capsule.py` | `CapsuleCreateRequest` 的 `memory_id`/`content` 改为 `Optional` 且互斥校验；`CapsuleResponse` 新增 `content`/`source_type` 字段 |
| `backend/app/services/capsule_service.py` | `create` 方法分支：memory 模式查记忆、custom 模式直接存 content；`get_all`/`get_by_id` 返回 `source_type`；详情内容根据来源取值 |
| `backend/alembic/env.py` | 添加 `TimeCapsule` 模型 import，确保 autogenerate 识别 |
| `backend/alembic/versions/a635703a6b55_...py` | 迁移脚本：add content 列 + batch 重建表（memory_id 可空 + FK SET NULL） |
| `frontend/src/types/index.ts` | `TimeCapsule` 接口 `memoryId` 改为 `string | null`；新增 `content`/`sourceType` 字段 |
| `frontend/src/api/index.ts` | `createCapsule` payload `memoryId`/`content` 改为可选 |
| `frontend/src/pages/CapsulePage.vue` | 创建弹窗重构为三步式：Step1 选来源（BookOpen/PenLine 图标卡片）→ Step2a 记忆列表选取 / Step2b 标题+内容输入 → Step3 开启日期+留言+封存 |
| `frontend/src/pages/CapsuleDetailPage.vue` | 内容卡片标题根据 `sourceType` 动态显示（"记忆内容" / "胶囊内容"） |

### 核心逻辑

**创建流程**：
1. Step1：用户选择来源（记忆库 / 新建内容）
2. Step2a（记忆库）：展示最近日记列表，选中后进入 Step3
3. Step2b（新建内容）：用户直接输入标题和内容，进入 Step3
4. Step3：选择开启日期（最早明天）+ 可选留言 → 封存

**后端校验**：
- `memory_id` 和 `content` 均为空 → 400 "必须选择一篇记忆或输入胶囊内容"
- `memory_id` 和 `content` 同时存在 → 400 "不能同时选择记忆和输入内容"

**详情展示**：`source_type=memory` 时从关联记忆取内容，`source_type=custom` 时从胶囊自身 `content` 取内容。

### 数据库迁移

SQLite 不支持 `ALTER COLUMN` 和命名外键约束，迁移脚本使用原始 SQL 重建表方式：
1. 备份原表 → 删除原表 → 创建新表（memory_id 可空 + FK SET NULL + content 列）→ 复制数据 → 删除备份
2. 幂等处理：检查 `content` 列是否已存在（部分迁移状态兼容）

### 后端 API 变更

```
POST /api/capsules
  Request Body（变更）:
    memory_id: string | null  （原：必填）
    content: string | null    （原：无）
    title: string             （不变）
    open_date: datetime       （不变）
    message: string | null    （不变）
  Response Body（新增字段）:
    content: string | null
    source_type: "memory" | "custom"
```

---

## 2026-07-25 — 时间胶囊选择记忆新增大小标签筛选

### 功能概述

时间胶囊创建流程中「从记忆库选取」步骤新增标签筛选能力：大标签（BigTagCategory）一键过滤 + 小标签搜索/多选 + 分页浏览，帮助用户快速定位目标记忆。

### 修改文件

| 文件 | 改动 |
|------|------|
| `frontend/src/pages/CapsulePage.vue` | 新增 `memoryBigTagFilter`/`memorySmallTagFilter`/`tagSearch`/`tagPage`/`tagPageSize` 响应式变量；新增 `useQuery` 查询标签列表（`getTags`）；记忆列表 `useQuery` 的 `queryKey`/`queryFn` 加入大标签和小标签过滤参数；新增 `toggleSmallTag`/`prevTagPage`/`nextTagPage` 交互函数；`watch(tagSearch)` 重置分页；模板中大标签按钮组 + 小标签搜索框 + 分页控件 + 已选标签展示 |
| `frontend/src/api/index.ts` | `getRecentMemories` 新增 `bigTag`/`tags` 可选参数，传递 `big_tag`/`tags` query params |

### 后端 API 变更

```
GET /api/memories/recent
  新增 Query Params:
    big_tag: string (可选) — 按大标签过滤
    tags:    string (可选) — 按小标签过滤，逗号分隔

GET /api/memories/tags（已有，复用）
  支持搜索(q) + 分页(page/size)，返回 {content, page, size, total_elements, total_pages}
```

### 交互设计

- **大标签筛选**：横向按钮组，点击切换，仅显示对应分类下的记忆
- **小标签筛选**：搜索框实时过滤标签 + 分页浏览 + 点击多选/取消
- **已选标签**：底部展示已选小标签 pill，支持单个移除和一键清空
- **联动**：大标签/小标签变更后，记忆列表自动重新查询

---

## 2026-07-26 — 时间胶囊页面白屏修复

### 问题描述

时间胶囊页面（`/capsules`）白屏崩溃，其他页面正常。浏览器控制台报 `ReferenceError: Cannot access 'memoryBigTagFilter' before initialization`。

### 根因分析

`CapsulePage.vue` 中 `memoryBigTagFilter` 和 `memorySmallTagFilter` 的 `ref` 声明位于 `useQuery` 调用之后（原第116-117行），但 `useQuery` 的 `queryKey` 中 `computed` 会在 setup 阶段立即被 `watchEffect` 追踪，此时变量尚未声明，触发 TDZ（暂时性死区）错误，导致组件崩溃白屏。

此问题由 commit `68b1281`（"feat: 时间胶囊选择记忆新增小标签筛选功能"）引入——该提交在 `useQuery` 之后追加了筛选变量声明，未注意声明顺序。

### 修复内容

将以下5个变量声明从 `useQuery` 之后移至 `useQuery` 之前：

| 变量 | 类型 | 用途 |
|------|------|------|
| `memoryBigTagFilter` | `Ref<BigTagCategory \| ''>` | 大标签筛选 |
| `memorySmallTagFilter` | `Ref<string[]>` | 小标签筛选 |
| `tagSearch` | `Ref<string>` | 标签搜索 |
| `tagPage` | `Ref<number>` | 标签分页页码 |
| `tagPageSize` | `number` | 标签每页条数 |

### 附带修复

- `vite.config.ts` / `vite.config.js`：proxy target 从 `http://localhost:8000` 改为 `http://127.0.0.1:8000`，解决 Node.js IPv6 优先导致 ECONNREFUSED 的问题

### 修改文件

| 文件 | 改动 |
|------|------|
| `frontend/src/pages/CapsulePage.vue` | 变量声明顺序调整：5个筛选变量移至 `useQuery` 之前 |
| `frontend/vite.config.ts` | proxy target 改为 `127.0.0.1:8000` |
| `frontend/vite.config.js` | 同步修改编译输出文件 |

---

## 2026-07-28 — 侧边栏整合 & 大标签筛选修复

### 侧边栏整合

将侧边栏从8项平铺导航整合为5项（3独立 + 2下拉分组），减少视觉噪音，核心功能保持一键直达。

| 顶层 | 类型 | 子项 |
|------|------|------|
| 首页 | 独立链接 | — |
| 记忆 | 独立链接 | — |
| 时间胶囊 | 独立链接 | — |
| 分析与洞察 | 折叠下拉 | 图谱、分析、对比、周报、月报、洞察档案 |
| 设置与工具 | 折叠下拉 | 导出、设置 |

**改动要点**：
- 原"自我洞察"模块合并进"分析与洞察"下拉，用分隔线区分分析工具与洞察报告
- 新增路由监听：`watch(route.path)` 自动展开当前路由所属分组
- 分组按钮在子项激活时高亮（`isInGroup` 判断）
- 新增 `Wrench` 图标用于"设置与工具"分组

### 时间胶囊大标签筛选修复

**问题**：胶囊列表页点击大标签筛选按钮无效果，列表不变化。

**根因**：`getCapsules` API 函数前端传参 `bigTag`（camelCase），但后端参数名为 `big_tag`（snake_case）。axios 的 `params` 对象不会自动转换键名，后端收不到 `big_tag` 参数导致筛选无效。

**修复**：在 `getCapsules` 中将 `bigTag` 解构后转为 `big_tag` 传给后端。

### 修改文件

| 文件 | 改动 |
|------|------|
| `frontend/src/components/Sidebar.vue` | 侧边栏重构：8平铺→3独立+2下拉；合并自我洞察模块；新增路由监听自动展开 |
| `frontend/src/api/index.ts` | `getCapsules` 参数 `bigTag`→`big_tag` 转换修复 |