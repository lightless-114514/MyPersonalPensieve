# MyPersonalPensieve - 开发日志

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

