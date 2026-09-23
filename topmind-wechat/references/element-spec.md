# 元素渲染规范

`md2wechat.py` 把 Markdown 转成公众号内联样式 HTML 的**唯一依据**。
改渲染逻辑或新增语法时，先改本文件再改代码；`audit_inline()` 是本文件的自动校验版本。

合规分级（贯穿全篇）：

| 级别 | 含义 | 处理原则 |
|---|---|---|
| **S** 安全 | 内联纯色/边框/字号，不会静默失效 | 可以放心依赖 |
| **D** 降级 | 可能被丢弃，但丢了不破坏结构与可读性 | 可用，但**不得作为唯一区分手段** |
| **X** 禁用 | 会静默失效或整段被吞 | 一律不用；`audit_inline` 判 ERROR |

---

## 一、块级元素

| Markdown | 产物 | 级 | 说明 |
|---|---|---|---|
| `# 标题` | `<p style="20px/700/center">` | S | 不用 `<h1>`（微信按标题语义覆盖字号） |
| `## 标题` | `<h2 style="18px/700;color:text_strong">` + 自动编号 | S | 见下方「章节编号」 |
| `### 标题` | `<h3 style="16px/600">` | S | |
| `#### 标题` | `<h4 style="15px/600">` | S | |
| 段落 | `<p style="margin:0 0 {para_gap};line-height:{line_height};letter-spacing:0.5px;text-align:left;word-break:break-word">` | S | `text-align` 只允许 left/center/right |
| `---` | `<p style="center"><span style="display:inline-block;width:12%;height:2px;background:accent">` | D | 短横线依赖 `inline-block`；丢了会退化成一条不可见的行内元素 |
| `> 引用` | `<section>` + `background:surface` + `border-left:3px solid accent` | S | **不用 `<blockquote>`**：微信有原生引用样式会覆盖我们的配色 |
| `- 项` / `1. 项` | `<ul>`/`<ol>` + `<li>`，支持嵌套 | S | 圆点颜色取 accent |
| ```` ```lang ```` | `<section background:code_bg>` → 语言标签 `<section>` → 代码体 `<section style="white-space:pre-wrap;word-break:break-all">` | S | **不用 `<pre>`**；详见「代码块」 |
| 表格（≤3 列） | `<table style="width:100%">`，表头行是首个 `<tr>` | S | **不写 `table-layout:fixed`**，**不用 `thead/tbody/colgroup`** |
| 表格（≥4 列） | 自动转卡片：每行一张 `<section>`，首列作标题、其余「列名 + 值」成对 | S | 公众号列数 >4 必然横向溢出，卡片化是唯一稳的解法 |
| `![说明](src)` | `<section>` → `<p center>` → `<img style="max-width:100%;height:auto;display:block;margin:0 auto">` | S | **不用 `width:100%`**（小图被拉满变糊）；**不用 `<figure>`** |
| `*图注*`（紧随图片） | `<p style="13px;color:text_light;center">` | S | 独立 `<p>`，不嵌在图片块里 |

---

## 二、行内元素

| Markdown | 产物 | 级 | 视觉层级 |
|---|---|---|---|
| `**文字**` | `<strong style="font-weight:600;color:text_strong">` | S | **锚点层**，全文 ≤5 处 |
| `*文字*` | `<em style="font-style:normal;color:text_muted">` | S | 弱化 |
| `` `代码` `` | `<code style="background:surface;color:accent;font-family:mono">` | S | |
| `==文字==` | `<strong>` + `background:accent_soft` | S | 容器层（高亮） |
| `++文字++` 或 `<u>文字</u>` | `<span style="border-bottom:2px solid accent_light;font-weight:600;color:text_strong">` | S | **标记层**，每段 1–3 个 |
| `~~文字~~` | `<span style="background:accent_soft;font-weight:600">` | S | 半高亮 |
| `[!文字]` | `<span style="11px;color:accent;background:accent_soft;padding:1px 6px">` | S | 徽章；不用 `inline-block` |
| `[文字](url)` | 正文 `文字` + 上标 `[n]`，文末「参考链接」块 | S | 公众号正文不支持可点外链 |

### 视觉层级（三层，写稿时的标记纪律）

| 层 | 手段 | 频率 | 用错会怎样 |
|---|---|---|---|
| **锚点层** | `**加粗**` | 全文 **≤5 处** | 到处加粗 = 没有重点 |
| **标记层** | `++下划线++` | **覆盖 ≥60% 的正文段落**，每段 1–3 个 4–15 字短语 | 缺失 = 正文变成一堵灰墙，读者无处落脚 |
| **容器层** | `==高亮==`、`::: 容器`、引用块 | 按需 | 堆太多会显得花 |

标记层是**出现频率最高**的一层，也是最容易被漏掉的一层。

`lint-wechat.py` 分两层判：**标记覆盖率 ≥60%**（带标记的正文段落数 ÷ 正文段落数，低于就报「跳读时没有落点」）+ **锚点加粗 ≤5 处**（超出就报「把标记当锚点用」）。

**不用「强调占比」这个口径**——它把两层合成一个数，会同时掩盖两种病：锚点爆表（加粗 123 处）和标记归零（下划线 0 处）能算出相近的占比，但修法完全不同。占比还容易凑：35 段里只标 5 段、每段标 20 字也能到 10%，而整段划线等于没标。覆盖率对应的是「还有几段没标」这个可执行动作。

---

## 三、容器

`:::` 是自研中间标记（公众号不认 Markdown，由 `md2wechat.py` 转成内联样式 HTML）。

| 写法 | 产物 | 用在哪 |
|---|---|---|
| `::: note` | 灰边说明块 | 补充说明 |
| `::: tip` | 绿边提示块 | 实操建议 |
| `::: warn` | 琥珀边注意块 | 风险提醒 |
| `::: danger` | 红边警告块 | 严重风险 |
| `::: pull` | 上下框线 + 居中金句 | 全文点睛，1–2 处 |
| `::: stat` | 浅底卡片 + 大号 accent 数字 | 关键数据（`数值 \| 说明` 每行一条） |
| `::: dialogue` | 说话人 + 气泡 | 访谈、问答 |
| `::: toc` | 前言导读卡 | 一般不用手写，见「自动导读」 |
| `::: sign` | 尾部签名区 | 一般不用手写，见「自动签名」 |

容器名拼错会**静默降级成 note**——`lint-wechat.py` 会报未知容器。
别名（`info`/`memo`→note，`success`/`ok`→tip，`quote`/`golden`→pull，`data`/`metric`→stat，
`chat`/`talk`→dialogue）等价。

---

## 四、三段自动行为

### 章节编号

- 标题里**手写的序号会被剥离**：`## 一、官方总表` → `01 官方总表`
- 剥离规则：中文序号（`一、`/`第一、`）、阿拉伯序号（`1.`/`01 `）
- 带负向断言保护：`## 3.4× 成本` **不会**被误剥成 `4× 成本`
- 编号由 `h2_style` 决定：`number`（01 + 左竖条，默认）/ `bar`（仅左竖条）/
  `underline`（下划线）/ `center`（上下框线）/ `plain`（无装饰）
- **末章若为收束类用 `∞` 而不是顺延数字**：标题匹配
  总结/结语/小结/尾声/后记/写在最后/写在后面/收尾/结尾/余论 时，编号取 `∞`
  （`number` 样式下生效）。理由：数字编号暗示"还有下一节"，与收束章的定位打架。
  实测 `## 六、总结` → `∞ 总结`，其余仍为 `01`…`05`。
- **写稿时不要手写序号**：手写后序号变成不可编程的字符串，
  换编号样式、加引用、做导航都得手改一遍

### 前言导读

- 触发条件（满足任一，且 `toc` 未被 `--no-toc` 关闭）：
  - 章节数 ≥ `toc_min_h2`（默认 4）
  - 章节数 ≥ 3 且正文 ≥ `toc_min_chars`（默认 2000 中文字）
- 位置：**首个正文段落之后**（不是标题与封面图之间）
- 内容：最多 `toc_max`（默认 5）条，超出时附注「……共 N 节」
  ——**不假装全文只有这几节**
- **导读的标记必须与正文标题一致**：
  - 标题带编号（`number`）→ 导读也编号，末章收束类同为 `∞`
  - 标题不带编号（`center`/`underline`/`plain`）→ 导读用中性圆点 `·`，
    **不能凭空造出 01/02**（否则读者在正文里找不到对应的编号）
- 显式 `::: toc` 优先于自动插入

### 尾部签名

`--signature` 三态：

| 值 | 行为 |
|---|---|
| `auto`（默认） | 稿件末尾**已自带**签名/CTA 则不再追加，避免出现两处签名区 |
| `on` | 无条件追加 |
| `off` | 只在显式写了 `::: sign` 时渲染 |

- 署名用占位 `{{作者名}}`，**不替用户编造人名**；`--author` / `--author-bio` 可填
- 判定「已自带」的口径：正文末尾 8 个非空段落内出现
  `点赞 / 在看 / 三连 / 点个关注 / 欢迎关注 / 关注「 / 扫码 / 分享给 / 我是…，`

---

## 五、代码块

- **不用 `<pre>`**：公众号端不自动换行，窄屏横向溢出，且格式检测会标风险项
- 用 `<section>` + `white-space:pre-wrap` + `word-break:break-all`
- 缩进与换行由代码自身提供：**HTML 源码里不在 pre-wrap 容器内插入任何格式化换行**
  （插了就会渲染出伪空行和大左缩进）
- **色板跟随主题**（`code_scheme`）：
  - `mono`（默认）：只用「主色 + 明暗层级」。注释最暗、字符串次之、
    关键字取主色的提亮版、其余用 `code_text`
  - `palenight`：Material Palenight 的 16 色，**已不推荐**——
    天蓝/翠绿/橙红与砖红、琥珀等主色毫无关系，一篇文章里会出现两套色彩语言
- 语言标签显示在代码体上方，字号 11px，颜色取 accent

---

## 六、`audit_inline()` 检查清单

每次生成 HTML 后自动跑，`ERROR` 必须清零。检查项已按本文件分级：

**ERROR**：`<div>` `<figure>` `<figcaption>` `<pre>` `<thead>` `<tbody>` `<colgroup>`
`<h1>` `<iframe>` `<video>` `<script>` `<style>`；`text-align` 非标准值；
px 固定宽度；`white-space:pre/nowrap`；`position/float/transform/opacity`；
`display:flex/grid`；`-webkit-*`；`linear-gradient`；`box-shadow`；`rgba()/hsla()`；
`var(--)`；`@media/@keyframes`；`class` 属性；Markdown 标记残留（`==`、`**`）

**WARN**：`table-layout:fixed`（列宽均分）、`display:inline-block`（非常规 display 值）、
`border-radius`（可能被丢，属优雅降级）、图片 `width:100%`、`id` 属性、
`<img width="...">` 属性

WARN 不是「可以忽略」，而是「已知风险，需确认是否可接受」。
