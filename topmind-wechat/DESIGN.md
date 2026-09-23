# topmind-wechat · 技能侧设计摘要

> 全案见 [`docs/wechat-studio-DESIGN.md`](../../../docs/wechat-studio-DESIGN.md)。本文只记技能包边界。

## 定位

- write 族**子技能**（`action_category: write` · `entrypoint: false` · pack `optional: true`）
- 不是日常前台：由 `topmind` / `topmind-write` 在「公众号 / 微信排版」意图下路由
- 能力真源：`scripts/*.py`（stdlib）+ `references/*` + `assets/themes/*`

## 路径解析

`--base` → `TOPMIND_WECHAT_BASE` → `{TOPMIND_WORKSPACE}/40-创作|20-专题/{year}-公众号`；topstream 可选（`TOPSTREAM_ROOT`）。

## 质量三关 + 排版关

事实 / 逻辑 / 文字（scan_ai_flavor ≥85 + 报告腔四症状）→ lint 0 error → md2wechat `--embed-images`。

Desktop / 移动伴面只实现**约束子集**；完整语义以本目录 Python 为准。

## 已知分叉与对拍要求

| 项 | 真源 | Desktop 子集 | 要求 |
|----|------|--------------|------|
| max-item | lint-wechat.py **70** | `WECHAT_MAX_ITEM` | 必须同值 |
| AI 结构扣分 | scan_ai_flavor.structural | `structuralDeduction()` | 同规则 |
| stat 管道行 | md2wechat 非 `\|` 丢弃 | wechat-format 同 | 同语义 |
| embed-images | `--embed-images` | `WechatService.exportViaScript` **优先**；否则 `embedLocalImagesWithChecklist` | 同效果 + 上传清单 |
| 导出真源 | `md2wechat.py` | 有 Python + 脚本时走 `wechat.exportViaScript` | 内置为回退 |

改动任一侧规则时，**同一次改动**更新另一侧并跑 `tests/plugin-wechat-ui.test.mjs` 对拍断言。
