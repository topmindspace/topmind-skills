# topmind-wechat · 技能侧设计摘要

> 技能边界以本文件、`SKILL.md` 和 `references/` 为准。不要另做一份用浏览器本地存储的公众号编辑器。

## 定位

- write 族**子技能**（`action_category: write` · `entrypoint: false` · pack `optional: true`）
- 不是日常前台：由 `topmind` / `topmind-write` 在「公众号 / 微信排版」意图下路由
- 能力真源：`scripts/*.py`（stdlib）+ `references/*` + `assets/themes/*`（5 套，含 `amber-review`）

## 路径解析

`--base` → `TOPMIND_WECHAT_BASE` → `{TOPMIND_WORKSPACE}/40-创作|20-专题/{year}-公众号`；topstream 可选（`TOPSTREAM_ROOT`）。
**禁止**把 `/Users/...` 写进脚本默认值（`~/TopWorkSpace/...` 惯例兜底允许）。

## 三条路径

- **forward**：`notes/*.md` → 公众号稿（`source_file`）
- **reverse**：选题原创 → 公众号稿 → 可选回推（`target_file: pending`；回推**必须** `--assets`）
- **站外拉取**：在线精选站/转载整合 → 仍用 `reverse` + `pending`（站外源不进 notes）

## 质量三关 + 排版关

事实 / 逻辑 / 文字（scan_ai_flavor ≥85 + 报告腔四症状）→ lint 0 error → md2wechat `--embed-images`。

Desktop / 移动伴面只实现**约束子集**；完整语义以本目录 Python 为准。

## references 索引

| 文件 | 管什么 |
|------|--------|
| `workflow.md` | 流程/状态机/路径/站外拉取 |
| `known-pits.md` | 实操坑 |
| `element-spec.md` | 元素 → HTML 渲染规格 |
| `theme-map.md` | 主题键 ↔ 题材映射 |
| `wechat-constraints.md` | 平台硬约束（转换产物） |
| `typography-rules.md` | 阅读节奏/段长 |
| `writing-quality.md` | 质量三关 |

## 已知分叉与对拍要求

| 项 | 真源 | Desktop 子集 | 要求 |
|----|------|--------------|------|
| max-item | lint-wechat.py **70** | `WECHAT_MAX_ITEM` | 必须同值 |
| AI 结构扣分 | scan_ai_flavor.structural | `structuralDeduction()` | 同规则 |
| stat 管道行 | md2wechat 非 `\|` 丢弃 | wechat-format 同 | 同语义 |
| embed-images | `--embed-images` | `WechatService.exportViaScript` **优先**；否则 `embedLocalImagesWithChecklist` | 同效果 + 上传清单 |
| 导出真源 | `md2wechat.py` | 有 Python + 脚本时走 `wechat.exportViaScript` | 内置为回退 |

改动任一侧规则时，**同一次改动**更新另一侧并跑 `tests/plugin-wechat-ui.test.mjs` 对拍断言。
