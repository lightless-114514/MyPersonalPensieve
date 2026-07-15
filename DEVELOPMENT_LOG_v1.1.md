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