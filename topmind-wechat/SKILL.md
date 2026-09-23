---
name: topmind-wechat
version: 4.13.0
description: >-
  公众号文章全生命周期子技能（write 族）：交付包、审校改写、质量三关、状态同步、微信内联排版与发布清单。
  支持 forward（底稿→公众号）、reverse（选题原创→回推）、站外拉取（在线精选站→reverse+pending）三条路径；
  内置五套主题、代码高亮、宽表卡片化、前言导读、尾部签名、外链脚注、--embed-images。
  Use when 写公众号、公众号排版、微信排版、定稿、发公众号、公众号交付包、wechat format、mp format。
  Do NOT use for 只改错别字（直接编辑）、小红书/知乎（平台约束不同）、纯网页发布、长文通用润色（走 topmind-write）。
action_category: write
triggers:
  - 公众号
  - 微信排版
  - 公众号排版
  - 公众号稿
  - 排版这篇文章
  - 定稿
  - 发公众号
  - 公众号交付
  - wechat
  - mp format
tags: [wechat, typography, formatting, publishing, markdown, write]
entrypoint: false
author: TopMindSpace
license: MIT
homepage: https://github.com/topmindspace/topmind
updated: 2026-09-23
degradation: ../shared/capability-degradation.md
compatibility: topmind workspace. Writes via UTR workspace-write / Desktop WorkspaceService. Scripts need Python 3 stdlib only.
---

# topmind-wechat · 公众号创作子技能

`topmind-write` 的**公众号专用子技能**。管一篇公众号文章从选题/底稿到发布清单的完整生命周期。

```
选题/底稿 → 创作 → 质量三关 → 定稿(状态+目录) → 排版 → 发布清单 →（可选）回推 notes
```

> **不是并列前台。** 用户说「写一篇长文」→ `topmind-write`；明确公众号/微信排版才进本技能。

## 脚本（真源）

| 脚本 | 用途 |
|------|------|
| `scripts/new-article.py` | 建交付包（骨架稿 + frontmatter + images/diagrams） |
| `scripts/sync-status.py` | 状态 ⇄ 目录名 ⇄ 字数（草稿 / 定稿 / 已发布） |
| `scripts/sync-mapping.py` | 映射一致性（frontmatter + 目录 + 可选 notes + topic 总表） |
| `scripts/push-to-topstream.py` | 可选回推：公众号稿降级为纯 Markdown notes |
| `scripts/lint-wechat.py` | 排版体检 + 自动修复（中英文间距、段长、AI 腔…） |
| `scripts/md2wechat.py` | Markdown → 全内联 HTML；**必加 `--embed-images`** |
| `scripts/scan_ai_flavor.py` | 中文去 AI 味扫描（与 `qu-aiwei-zh` 同源） |

```bash
# 路径解析：CLI --base/--workspace → env TOPMIND_WECHAT_BASE / TOPMIND_WORKSPACE / TOPSTREAM_ROOT → 惯例
export TOPMIND_WORKSPACE=/path/to/workspace   # 推荐
python3 scripts/new-article.py --slug demo --title "标题" --direction reverse
python3 scripts/lint-wechat.py --input <包>/公众号稿.md --fix
python3 scripts/scan_ai_flavor.py <包>/公众号稿.md          # 目标 ≥85
python3 scripts/md2wechat.py --input <包>/公众号稿.md --out-dir <包> --slug demo \
  --asset-root <素材根> --embed-images
python3 scripts/sync-status.py --set 定稿 <包> --apply
```

细节见 [`references/workflow.md`](references/workflow.md) · [`references/known-pits.md`](references/known-pits.md)。

## 路径默认

| 用途 | 解析 |
|------|------|
| 交付包根 | `--base` → `TOPMIND_WECHAT_BASE` → `{ws}/40-创作/2026-公众号` 或 `{ws}/20-专题/2026-公众号` |
| 工作区 | `TOPMIND_WORKSPACE` |
| 底稿/回推 | `--topstream` → `TOPSTREAM_ROOT` → 可选；不存在则跳过 notes 校验 |
| 终稿交付 | 可 `save-output` 拷贝到 role:delivery（`88-交付/`），包仍留在创作类专题 |

## 三条路径

### forward（底稿 → 公众号）

```
底稿 notes/*.md → 审校改写 → 质量三关 → 定稿 → 排版 → 发布
```

`new-article.py --direction forward --source-file notes/xxx.md`

### reverse（选题原创）

```
选题包 → 调研素材 → 多轮改稿 → 三关 → 定稿 → 排版 → 发布 →（可选）push-to-topstream
```

`new-article.py --direction reverse`（`target_file: pending`）

### 站外拉取（转载整合 / 在线精选站）

源不在本工作区、也不在 topstream `notes/` 时，**仍落 `reverse` + `target_file: pending`**。  
**不要用 `forward`**：它要求 `source_file` 以 `notes/` 开头且文件真实存在，站外源必然过不了 `sync-mapping.py`。

```bash
python3 scripts/new-article.py --slug <中文短名> --title "<标题>" --direction reverse
```

取源坑（Next.js 站点）：正文在 RSC 载荷里，优先 `GET /api/notes/<id>`；图片在 `/api/uploads/<hash>`，记 hash→本地名映射；同图双 hash 用 `md5` 去重。差异与口径写进包内 `README.md`。

**回推纪律**：notes 保持纯 Markdown。`::: 容器` / 徽章 / `==高亮==` 只进公众号稿。回推**务必带 `--assets`**（否则 GitHub 上 `images/` 死链）：

```bash
python3 scripts/push-to-topstream.py <包> --target notes/xxx.md --assets          # dry-run
python3 scripts/push-to-topstream.py <包> --target notes/xxx.md --assets --apply \
  --asset-names "00-封面.jpg=01-cover.jpg,…"
```

## 交付包与状态

```text
YYYY-MM-DD-<中文短名>            # 草稿
YYYY-MM-DD-<中文短名>-released   # 定稿 / 已发布
├── 公众号稿.md                  # 唯一改稿入口
├── <slug>-公众号版.html         # 浏览器打开 → 复制正文 → 粘贴后台
├── 图片上传清单.md
├── images/  diagrams/
└── README.md                    # 包说明（可选）
```

**frontmatter（映射真源）**

```yaml
status: 草稿            # 草稿 | 定稿 | 已发布
direction: reverse      # forward | reverse
source_file: ""         # forward 填 notes/xxx.md
target_file: pending    # reverse：pending | notes/xxx.md
word_count: 0           # 纯中文字数，sync-status 维护
```

状态与目录名**不要手改**：

```bash
python3 scripts/sync-status.py --set 定稿 <包> --apply
```

## 质量三关（定稿前必过）

### 关 1 · 事实

- 承重数字回**一手来源**；厂商口径 / 据报道 分开写  
- 查不到一手来源的传闻**删**  
- 改稿续写：正文已有数字**回源重核**（上一轮文本最不可信）  
- 多口径（主轮/复跑）显式拆开；表格从数据源生成，禁止手抄  
- 外部工具改过的稿：**先核数字再动文字**；「比值对但绝对值错」= 全段重核  

### 关 2 · 逻辑

- 单边结论旁配反方证据  
- 结构前后一致；同一事实多处同值  

### 关 3 · 文字（去 AI 味）

```bash
python3 scripts/scan_ai_flavor.py <包>/公众号稿.md   # ≥85（人话）
```

- 删套话/黑话/工程圈行话；降调段末加粗金句  
- **满分 ≠ 有人味**：再查「段末金句癖 / 节奏过分整齐 / 没有场景与我 / 报告体标注」  
- **口语化 ≠ 有人味**：删社交垫词（元叙述、空转过渡、姿态句）  
- 判据：**这句话删掉之后，读者少知道了什么？**  

详见 [`references/writing-quality.md`](references/writing-quality.md)。

## 排版要点（写稿时）

- 开头 150 字内钩子；单段 ≤110 字；列表项 ≤70 字  
- 二级标题序号化；容器：`::: stat|pull|note|tip|warn|danger|dialogue`  
- **`::: stat` 内必须是 `数值 | 说明` 管道行**，否则静默丢弃  
- 评测稿：**图承担数据，正文只解读**；健康密度 **300–450 字/图**  
- 个股用词红线：禁用 买入/推荐/目标价…；文末投资声明  

更多：[`references/typography-rules.md`](references/typography-rules.md) · [`references/wechat-constraints.md`](references/wechat-constraints.md)。

## 排版与导出（必读）

```bash
python3 scripts/md2wechat.py \
  --input <包>/公众号稿.md --out-dir <包> --slug <slug> \
  --asset-root <素材根> --embed-images \
  [--theme assets/themes/minimal-ink.json]
```

1. **永远 `--embed-images`**，否则粘贴丢图（相对路径被序列化成 file://）  
2. **图片 basename 铁律**：正文引用名 = `images/` 目标名；禁止两套同名图共处  
3. 合规自检出现 `✗` 改生成器，不要手改 HTML  

坑清单：[`references/known-pits.md`](references/known-pits.md)。

## 主题

| 文件 | 风格 | 适用 |
|------|------|------|
| `assets/themes/minimal-ink.json`（默认） | 黑白灰 + 砖红 | 深度研析 / 观点 / 随笔 |
| `assets/themes/tech-blue.json` | 科技蓝 | AI/技术 |
| `assets/themes/newsprint.json` | 报纸衬线 | 人文评论 |
| `assets/themes/graphite.json` | 石墨克制 | 严肃报告 |
| `assets/themes/amber-review.json` | 琥珀评测 | 产品评测 |

`md2wechat.py --list-themes` 看全部；`--theme genre:评测` 可按题材自动选。  
渲染规格见 [`references/element-spec.md`](references/element-spec.md) · 主题映射见 [`references/theme-map.md`](references/theme-map.md)。

**平台红线速查**（详见 [`references/wechat-constraints.md`](references/wechat-constraints.md)）：禁 `div`/`pre`/`h1`/`figure`/`thead`/flex/float/gradient/shadow；表格 `table-layout` 不写 fixed；列数 ≥4 转卡片。

## 与 Desktop「公众号创作」

Desktop mini-app（`topmind-wechat` 插件）是本技能的**可视化工作流伴面**：包列表 → 改稿 → 三关 → 预览 → 导出。写回仍走 WorkspaceService；脚本语义以本技能为准。

## When NOT to use

- 只想改几个句子 → 直接编辑  
- 小红书 / 知乎 / 掘金 → 平台约束不同  
- 通用长文交付 → `topmind-write`  
- 只去 AI 味不排版 → `scan_ai_flavor.py` 或 humanizer 类技能  
