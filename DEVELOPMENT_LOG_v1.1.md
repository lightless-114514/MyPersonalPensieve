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