# 工作流 · 交付包 · 状态机

## 生命周期

```text
forward:        底稿 notes/*.md → 审校改写 → 质量三关 → 定稿 → 排版 → 发布
reverse:        选题包 → 调研/素材 → 多轮改稿 → 质量三关 → 定稿 → 排版 → 发布 →（可选）回推
站外拉取 (ext):  在线精选站/转载整合 → 创作/整合 → 质量三关 → 定稿 → 排版 → 发布 →（可选）回推
```

`direction` 写在 frontmatter：`forward | reverse`。**站外拉取也用 `reverse` + `target_file: pending`**（站外源不进 `notes/`，`forward` 会因 `source_file` 校验失败）。

## 建包

```bash
export TOPMIND_WORKSPACE=/path/to/ws
python3 scripts/new-article.py --slug <中文或英文短名> --title "中文标题" \
  --direction reverse \
  [--base <包根>] [--date YYYY-MM-DD] [--images a.png b.png] \
  [--source-file notes/xxx.md]   # forward
```

产出目录 `YYYY-MM-DD-<中文短名>/`，骨架 `公众号稿.md`。

### 站外拉取取源注意

- Next.js 站点正文常在 RSC 载荷里：优先探 `GET /api/notes/<id>` 读 `item.body`，别只 `curl` HTML。
- 图片可能在 `/api/uploads/<hash>`；下载时记录 hash → 本地名映射。
- 同图可能双 hash：`md5` 去重；截图带页面残留时按面板边框裁切。
- 与源差异、图片处理、口径边界写进包内 `README.md`；一手来源抓不到必须写明。

## 反向选题包（可选，长文建议）

```text
YYYY-MM-DD-选题策划/
├── 选题策划.md
├── T1-<题>-调研与框架.md
├── 素材总库.md
├── 图表与配图方案.md
└── 发布前待办.md
```

多轮调研**每轮回头找反证**。

## 状态机

| status | 目录名 | 含义 |
|--------|--------|------|
| 草稿 | `YYYY-MM-DD-名` | 写作中 |
| 定稿 | `…-released` | 可发 |
| 已发布 | `…-released` | 已上线（作者手动改） |

```bash
python3 scripts/sync-status.py                 # dry-run
python3 scripts/sync-status.py --apply         # 刷字数 + 纠目录名
python3 scripts/sync-status.py --set 定稿 <包> --apply
```

## 字数口径（三处别混）

| 输出 | 口径 | 用途 |
|------|------|------|
| frontmatter `word_count` | 正文**全文**的 `[\u4e00-\u9fff]` 计数 —— **frontmatter 之后的一切都算，含图注、也含图片路径里的中文** | 映射真源 |
| lint「字数」 | 视觉长度（中 1 + 英数 ×0.6，URL 不计） | 阅读时长 / 段长 |
| md2wechat「正文字数」 | 渲染后字符 | 仅展示 |

⚠️ `word_count` **只能由 `sync-status.py --apply` 回写，禁止手算**。它的口径与直觉不同：一篇 9 图稿，光 `images/NN-中文名.png` 这一串路名就贡献 40+ 字。自制口径（如「剔掉图注与路径」）会得出一个更小、更像「正文字数」的值，写进 frontmatter 后会被 `sync-mapping.py` 判为漂移 —— 实测一篇 1,027 vs 1,450，而错值同时落进 `topic.md` 总表与包内 README，**一个错值三处落盘**。

## 定稿验收命令串

```bash
python3 scripts/scan_ai_flavor.py <包>/公众号稿.md    # 总分 ≥85 且「作者姿态分」≥85
python3 scripts/lint-wechat.py --input <包>/公众号稿.md
python3 scripts/audit-provenance.py --draft <包>/公众号稿.md --source <包>/源稿-*.md
python3 scripts/sync-mapping.py --no-topstream
python3 scripts/sync-status.py
python3 scripts/md2wechat.py --input <包>/公众号稿.md --out-dir <包> \
  --slug <slug> --asset-root <素材根> --embed-images
```

第 3 行只在**有源稿**时跑（`reverse` / 站外拉取；`forward` 的底稿在 `notes/` 也一样适用）。退出码 **0 = 双向干净**、**1 = 有待判定项**、2 = 参数错。**1 不等于稿子有问题**——它只是把「本稿有源稿找不到」和「源稿有本稿落下」两类段摆出来，由人逐条判：归入已声明的修正/增补，或改回去。判定完把结论写进包内 `README.md`，这一关才算收口。

三个易踩的点：

- **阈值别乱调**：默认 `0.72`。调高会把正常的改写（换词、调序）判成新增，调低会漏掉真扩写。
- **源稿后加的块要 `--skip`**：若源稿顶部有本包后补的勘误/说明块（`> [!note] …`），它在本稿侧不存在，会恒定报一条反向待判定。用 `--skip '^>\s*\[!'` 排除，别去改稿子。
- **图注不算遗漏**：脚本反向侧额外建了一个「去掉 `▲ 图 N` 前缀」的候选池，图注编号不会被误判为漏段。

## 收尾

1. 更新专题 `topic.md` 总表（派生视图）  
2. reverse 且要回推：**务必带 `--assets`**，否则 GitHub 上 `images/` 全裂：

   ```bash
   python3 scripts/push-to-topstream.py <包> --target notes/xxx.md --assets          # dry-run
   python3 scripts/push-to-topstream.py <包> --target notes/xxx.md --assets --apply \
     --asset-names "00-封面.jpg=01-cover.jpg,…"   # 仓库约定 ASCII 图名
   ```

   仓库图路径约定：`notes/<slug>.md` 引用 `../assets/images/<slug>/NN-name.png`。  
   脚本只降级转换 + 写 notes + 搬图；**不自动改** README 索引 / `docs/公众号映射.md` / frontmatter（防索引漂移）。手工完成后再把 `target_file` 改实际路径。  
3. 提醒：外链只能进「阅读原文」；图已 base64 内嵌，占位符按清单补传  
4. 需要进交付层时：`save-output` 拷贝终稿到 `88-交付/`（`YYYY-MM-DD-描述.ext`）

## Desktop

| 步骤 | Desktop「公众号创作」 |
|------|----------------------|
| 建包/列表 | 扫工作区包根 |
| 改稿 | 写闸回执 |
| 三关 | AI 味 + lint + 事实勾选 |
| 排版 | 主题预览 + 调脚本导出 |
| 状态 | 调 `sync-status` |
