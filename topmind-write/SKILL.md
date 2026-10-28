---
name: topmind-write
description: >-
  根据 topmind 工作区素材起草、续写、改稿或保存通用稿件。Use when 写成稿、润色、write、draft、revise。明确平台稿优先已安装的独立写作技能。Do NOT use for capture-only, profile-only, or external posting requests.
license: MIT
compatibility: topmind workspace. Delivery role category (often 88-交付 / 88-Delivery).
metadata:
  version: "4.15.9"
  action_category: "write"
  entrypoint: "false"
  triggers: "写作, 起草, 续写, 修订, 润色, 交付, 改写, de-AI, 出稿, 定稿, 导出, write, draft, deliver, export"
  tags: "write, draft, revise, polish, deliver"
  author: "TopMindSpace"
  homepage: "https://github.com/topmindspace/topmind-skills"
  updated: "2026-10-28"
  degradation: "../shared/capability-degradation.md"
---

# topmind Write

从材料产出可用稿件，或修订用户指定的文本。Draft / Continue / Revise / Polish / Deliver 是可选动作，不是固定流水线。

## 依据与输出

- 有专题时先读 `topic.md`（若有），再读焦点稿与必要素材；缺首页照样完成，不默认创建。
- 从用户要求和现有上下文判断受众、用途、语气；缺少实质信息才询问。不默认先 organize 再 write。
- 保留事实、不确定性与用户声音；不为“去 AI 味”编数字、经历或观点。专用改稿技能存在且适用时才加载，没有也可完成通用改稿。
- 用户要持久稿件时写专题根或 role:delivery（通常 `88-交付/`）；交付命名 `YYYY-MM-DD-描述.ext`。不创建专题内 `outputs/`；仅要求对话稿时直接给正文。
- AI 起草 `source_type: ai-derived`；仅给用户原文排版保留 user-original。

## 修订与验证

修改前读取真实文本；小范围优先唯一片段替换。多步编辑使用最新 contentHash / expectedHash 和 postEditWindow；冲突重读，不反复猜 oldText。整文改写需掌握全文，避免截断覆盖。不要编造 shell / bash 工具。

交付前检查格式、事实、来源和遗漏，移除内部标注与占位符。回复完成结果与实际路径。写入策略与 locked 首写快照见 [writeback-receipt](../shared/writeback-receipt.md)。

## 可选专用能力

写作技能保持独立仓库；Desktop 与 Obsidian 默认内置受验证版本，其他 Agent 按需安装。明确指定平台或只改排版时，优先直接使用相应独立技能：改稿 `topmind-revise`，只排版 `topmind-format`；本技能仅补工作区素材读取和落盘，不再要求用户选一次技能。宿主有 `render_article` 时用它生成平台 HTML/文本，无需猜测或执行 Python 命令。生成后按用户意图落盘，预览/复制不等于发布。

公众号 → `topmind-wechat-post`；X 长文 → `topmind-x-article`；干货短文 / 引流短帖 → `topmind-briefs` / `topmind-viral-posts`；幻灯片 → `topmind-presentation`。已安装且匹配时使用，未安装则完成通用稿并说明专用格式限制，不能伪装已生成 HTML/PPTX。消歧详见 [trigger-disambiguation](../shared/trigger-disambiguation.md)。写稿不构成外部发布授权。

用户一次授权“研究并写稿”时连续完成，不把写稿留为下一步建议。额外记忆/待办候选按 [auto-suggest](../shared/auto-suggest.md)，不因稿件内容自动更新画像。

## 保存设置

`writeback_mode: auto | confirm`：自动保存 auto 写入 + 路径回执；confirm 内容直接写入，删除/归档才进审阅入口。工具能力不足见 [capability-degradation](../shared/capability-degradation.md)。
