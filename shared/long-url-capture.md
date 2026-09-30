# 长 URL / 网页抓取约定

> Skills（agent host）与 Desktop `workspace.fetchUrl` 对齐。抓取是加速器，**文件系统落盘**仍是真源。

## 目标

把网页变成可审阅的 Markdown 笔记（`source_type: external-capture`），不假装「已完整镜像整站」。

## 分层策略

```text
L1  静态 HTTP fetch + Readability / 启发式 / GitHub raw   ← 默认
L2  Desktop 增强渲染（隐藏 Chromium offscreen） ← SPA 空壳 / 「增强渲染」
L3  用户粘贴 / 浏览器复制                         ← 永远可用
L3+ 浏览器扩展 → Bridge 和/或 工作区直写          ← 推荐日常剪藏
```

| 层 | 入口 | 说明 |
|----|------|------|
| L1 | `fetchUrl({ url })` | `@mozilla/readability` + `html-to-markdown`；无第二窗口 |
| L1-GH | 同上，GitHub md/README | `lib/github-md.mjs`：blob/raw 直取 raw + 相对图改写；仓库根/tree 解析 README |
| L2 | `fetchUrl({ url, render: true })` | `fetch-render.mjs` + ephemeral 窗（不占 Dock） |
| L3 | 手动 | 失败回退 |
| L3+ | Extension | 页内 Readability + **预览 / 选区 / 高亮 / 模板 / 落点**；**Bridge**（高质量 MD + 图片本地化 + destinations）或 **工作区目录**（FS Access，无 Desktop）。见 ADR · `browser-extension/` · `docs/capture-clip-matrix.md` |

**复用原则**：扩展负责活 DOM 正文与高亮；Bridge 与工作区直写共用 Desktop `html-to-markdown` 与同一 frontmatter 规约。GitHub URL 语义（解析 / raw / 图片改写）单源在 Kernel `lib/github-md.mjs`，不维护第二套。Bridge 另走落点 API 与写闸；工作区直写是用户手势确认的 companion 路径。落点：Inbox / 类别 / 专题（Bridge 在线时 popup 可选）。

Agent host 无 Electron 时停在 L1/L3；扩展 **不强制** Desktop 在线（可配置工作区直写）。

## GitHub 专用路径

| 输入 | 行为 | `fetch_method` |
|------|------|----------------|
| `github.com/.../blob\|raw/<ref>/<path>.md` | 直取 `raw.githubusercontent.com` | `github-raw` |
| `raw.githubusercontent.com/.../<path>.md` | 直取并改写相对图 | `github-raw` |
| `github.com/<owner>/<repo>` · `.../tree/<ref>[/subdir]` | README 解析（API `/readme`，失败 raw 探测） | `github-readme` |
| 其他 GitHub 页（issues / pulls…） | 按普通网页提取 | `readability` / `heuristic` |

相对图片路径改写为 `raw.githubusercontent.com/...`，避免笔记内裂图。标题优先 H1，否则文件名。

## URL 类型提示（UI）

粘贴 / 输入 URL 时提示将抓取什么（不弹多选）：

- GitHub Markdown 文件 · 将抓取原文
- GitHub 仓库 · 将抓取 README
- X 动态 / X 文章 · 将按网页提取
- 网页 · 将提取正文

## 长度与截断

| 模式 | 上限 |
|------|------|
| 默认 | 40k 字符 |
| 完整抓取 | 200k 字符 |
| GitHub raw/README | 400KB 字节（与 raw 文件上限一致） |

**必须**在 UI 或 frontmatter 标明：截断、约字数、提取方法、清洗后 URL。用户不可见截断 = 产品缺陷。

## Frontmatter 建议

```yaml
source_type: external-capture
source: https://example.com/article
captured_at: 2026-07-13T12:00:00+08:00
fetch_method: readability   # readability | heuristic | render | github-raw | github-readme | selection | manual
fetch_truncated: false
word_count: 1200
```

## Desktop UX

- QuickCapture：截断 → 完整抓取；SPA → 增强渲染；保存后打开落盘路径  
- URL 类型提示（GitHub README / GitHub 原文 / X / 网页）  
- Inbox：按 `source_type` 筛选「网页/摘录」  
- AI `fetch_url` 支持 `maxLen` + `render`；Obsidian `fetch_url` 对 GitHub md 自动走 raw  
- AI `capture_url`：一键抓取并入库（带 source URL + 标题）；Desktop 与 Obsidian 对齐（`forceInbox` / `forceAtom`）  
- AI `web_search`：无需 Key 的网络搜索短列表（域名打分 + 同域去重）；命中后 `fetch_url` / `capture_url`  
- 工具失败会返回**一条**具体恢复步骤（如 edit 失败 → 先 read_file 刷 contentHash）

## 不要做的事

- 不把整页 HTML 当笔记正文  
- 不静默丢弃后半篇  
- 不把抓取失败写成「已成功 capture」  
- 不用常驻第二 BrowserWindow 占 Dock（仅 ephemeral 隐藏窗）  
- 不对 GitHub md 再走 HTML scrape（raw 更干净）  
