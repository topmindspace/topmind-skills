#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit-provenance.py — 双向逐段溯源审计（改稿保真度的机械化检查）。

## 它解决什么问题

把一篇成稿改成另一种形态（X 长文 → 公众号、底稿 → 交付稿）时，最容易出的不是错别字，
而是**悄悄扩写**和**悄悄漏掉**。人眼逐段比对一篇几千字的稿子既慢又不可靠。

本脚本做**两个方向**的机械化检查：

- **正向（本稿 → 源稿）**：`--draft` 的每一段，能否在 `--source` 里找到？找不到的即
  「疑似新增」—— 扩写就藏在这里
- **反向（源稿 → 本稿）**：`--source` 的每一段，有没有在本稿里落下？找不到的即「疑似遗漏」

## 为什么不用 diff

形态转换必然改变排版：断段、标题层级、`++` 标记层、图注加 `▲ 图 N` 编号。
逐行 diff 会被这些噪声淹没，真正的问题（多出/少掉的事实句）反而看不见。

所以这里**先归一化到「纯文字内容」再比对**，并显式放过几类合法差异：

| 分类 | 含义 |
|------|------|
| `identical` | 归一化后完全相同 |
| `rewritten` | 同段但有文字改动（图注编号、标点、已声明的事实修正都落这里） |
| `merged` | 本稿把源稿的**几段并成了一段** |
| `split` | 源稿的一段被本稿**拆成了几段** |
| `caption` | 仅图注加了 `▲ 图 N：` 前缀，正文一字未改 |
| `tail` | 结尾 CTA / 签名 / 「首发于公众号」类附加句 |
| `unexplained` | **其余全部**，需要人工判定 —— 这是唯一会被报警的一类 |

⚠️ **`merged` / `split` 两类是必须的**：源稿常把「正文末句 + 图注」挤在同一段，本稿拆开是
正常排版。没有这两类，几乎每张图都会报一次假阳性；而只做段落级匹配则会把所有拆段都误报。
所以候选池同时建两级窗口：**段窗口**（1~3 段合并）与**句窗口**（1~3 句合并，长度下限 12 字）。

## 已知陷阱（踩过）

不要用 `^---.*?^---` 配 `re.S` 剥 frontmatter —— 正文里常有 `---` 分隔线，
那个正则会连带把中间正文吃掉，导致源稿被误判成「只剩几段」。
本脚本只剥**文件头**的 frontmatter：`^---\\n.*?\\n---\\n` + `count=1`。

源稿里后加的块（勘误、HTML 注释）默认会进待判定，用 `--skip` 排除：

    --skip '^>\\s*\\[!'

## 用法

    python3 scripts/audit-provenance.py --draft <包>/公众号稿.md --source <包>/源稿-X长文.md
    python3 scripts/audit-provenance.py --draft a.md --source b.md --skip '^>\\s*\\[!' --json
    python3 scripts/audit-provenance.py --draft a.md --source b.md --threshold 0.8 --verbose

退出码：0 = 无待判定项；1 = 有 `unexplained`（需人工看）；2 = 参数/文件错误。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher

MAX_SPAN = 3          # 允许 1~MAX_SPAN 个相邻单位合并成一个窗口
MIN_SENT_WIN = 12     # 句级窗口归一化后的最小长度，避免短句偶然命中

# 元信息块（来源 / 抓取记录）——两侧都跳过
META_RE = re.compile(
    r"^>\s*(来源|实标题|标题|摘要|作者|站点|提取|约字数|说明|发布|原始)\s*[:：]"
)
IMG_ONLY_RE = re.compile(r"^\s*(!\[[^\]]*\]\([^)]*\)|!\[\[[^\]]*\]\])\s*$")
HTML_COMMENT_RE = re.compile(r"^\s*<!--.*?-->\s*$", re.S)
CAPTION_PREFIX_RE = re.compile(r"^▲\s*图\s*\d+\s*[：:\-–—]?\s*")
SENT_RE = re.compile(r"[^。！？；!?;]*[。！？；!?;]|[^。！？；!?;]+")

TAIL_HINTS = ("欢迎转发", "点个关注", "评论区", "不迷路", "首发于", "转载请注明",
              "如果这篇", "如果对你有用")

_TYPO = {
    "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
    "\u2014": "-", "\u2013": "-", "\u2026": "...",
}


# --------------------------------------------------------------------------- #
# 切段与归一化
# --------------------------------------------------------------------------- #

def strip_fm(text: str) -> str:
    """只剥文件头的 frontmatter。正文里的 --- 必须保留。"""
    if text.startswith("---\n"):
        m = re.match(r"^---\n.*?\n---\n", text, re.S | re.M)
        if m:
            return text[m.end():]
    return text


def blocks(text: str, skips):
    """按空行切段；丢掉分隔线、纯图片、元信息块、HTML 注释块、--skip 命中的块。

    代码块内部不切分，避免把一段代码拆散。
    """
    body = strip_fm(text).replace("\r\n", "\n")
    out, buf, in_code = [], [], False
    for line in body.split("\n"):
        if line.strip().startswith("```"):
            in_code = not in_code
            buf.append(line)
            continue
        if in_code:
            buf.append(line)
            continue
        if line.strip() == "":
            if buf:
                out.append("\n".join(buf))
                buf = []
        else:
            buf.append(line)
    if buf:
        out.append("\n".join(buf))

    keep = []
    for b in out:
        s = b.strip()
        if not s or re.fullmatch(r"[-*_]{3,}", s) or IMG_ONLY_RE.match(s):
            continue
        if META_RE.match(s) or HTML_COMMENT_RE.match(s):
            continue
        if any(rx.search(s) for rx in skips):
            continue
        keep.append(s)
    return keep


def normalize(block: str) -> str:
    """把一段 markdown 归一化成「可比较的纯文字内容」。"""
    t = block
    t = re.sub(r"^\s*>\s?", "", t, flags=re.M)
    t = re.sub(r"^\s*#{1,6}\s*", "", t, flags=re.M)
    t = re.sub(r"^\s*[-*+]\s+", "", t, flags=re.M)
    t = re.sub(r"^\s*\d+[.)]\s+", "", t, flags=re.M)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)
    t = re.sub(r"!\[\[[^\]]*\]\]", "", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"`{1,3}", "", t)
    for a in ("**", "__", "==", "++", "~~"):
        t = t.replace(a, "")
    for a, b in _TYPO.items():
        t = t.replace(a, b)
    return re.sub(r"\s+", "", t)


def block_windows(norms):
    """段级窗口：(起始段, 结束段, 合并文本)。"""
    n = len(norms)
    for i in range(n):
        acc = ""
        for k in range(MAX_SPAN):
            if i + k >= n:
                break
            acc += norms[i + k]
            yield i, i + k, acc


def sent_windows(norms):
    """句级窗口：(所属段, 所属段, 合并文本)。用于识别「源稿一段被拆开」。"""
    for i, blk in enumerate(norms):
        sents = [s for s in SENT_RE.findall(blk) if s]
        for a in range(len(sents)):
            acc = ""
            for k in range(MAX_SPAN):
                if a + k >= len(sents):
                    break
                acc += sents[a + k]
                if len(acc) >= MIN_SENT_WIN:
                    yield i, i, acc


def best(needle, win_list):
    """返回 (最高相似度, 窗口起, 窗口止, 次高相似度)。"""
    if not needle or not win_list:
        return 0.0, -1, -1, 0.0
    scored = []
    for a, b, txt in win_list:
        scored.append((SequenceMatcher(None, needle, txt).ratio(), a, b))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[0]
    second = scored[1][0] if len(scored) > 1 else 0.0
    return top[0], top[1], top[2], second


def is_tail(text: str) -> bool:
    return any(h in text for h in TAIL_HINTS)


def snippet(text: str, n: int = 44) -> str:
    one = re.sub(r"\s+", " ", text).strip()
    return one if len(one) <= n else one[:n] + "…"


# --------------------------------------------------------------------------- #
# 审计
# --------------------------------------------------------------------------- #

def audit(draft_path, source_path, threshold, skips):
    dblocks = blocks(open(draft_path, encoding="utf-8").read(), skips)
    sblocks = blocks(open(source_path, encoding="utf-8").read(), skips)
    dn = [normalize(b) for b in dblocks]
    sn = [normalize(b) for b in sblocks]

    s_blk = list(block_windows(sn))
    s_sent = list(sent_windows(sn))
    # 本稿侧额外把「去掉 ▲ 图 N 前缀」的版本算作候选，图注不算遗漏
    dn_plus = list(dn) + [normalize(CAPTION_PREFIX_RE.sub("", b.strip()))
                          for b in dblocks if CAPTION_PREFIX_RE.match(b.strip())]
    dn_plus = [x for x in dn_plus if x]
    d_blk = list(block_windows(dn_plus))
    d_sent = list(sent_windows(dn_plus))

    def judge(r_blk, r_sent, span_blk, span_sent):
        """按「先段级、后句级」判定分类。"""
        if r_blk >= threshold:
            if r_blk >= 0.995:
                return "identical", r_blk, span_blk
            if span_blk[1] > span_blk[0]:
                return "merged", r_blk, span_blk
            return "rewritten", r_blk, span_blk
        if r_sent >= threshold:
            return "split", r_sent, span_sent
        return "unexplained", max(r_blk, r_sent), span_blk

    forward = []
    for i, d in enumerate(dblocks):
        if not dn[i]:
            continue
        rb, ab1, ab2, sb = best(dn[i], s_blk)
        rs, as1, as2, ss = best(dn[i], s_sent)
        capped = bool(CAPTION_PREFIX_RE.match(d.strip()))
        r_nocap = -1.0
        if capped:
            alt = normalize(CAPTION_PREFIX_RE.sub("", d.strip()))
            if alt:
                r_nocap, *_ = best(alt, s_blk)
        top = max(rb, rs, r_nocap)

        if top >= threshold:
            kind, _, span = judge(rb, rs, (ab1, ab2), (as1, as2))
            if capped and r_nocap > max(rb, rs):
                kind = "caption"
            forward.append({"i": i, "kind": kind, "ratio": round(top, 3),
                            "source_span": list(span), "text": snippet(d)})
        elif is_tail(d):
            forward.append({"i": i, "kind": "tail", "ratio": round(top, 3),
                            "source_span": [-1, -1], "text": snippet(d)})
        else:
            forward.append({"i": i, "kind": "unexplained", "ratio": round(top, 3),
                            "second": round(max(sb, ss), 3), "source_span": [ab1, ab2],
                            "text": snippet(d)})

    backward = []
    for i, s in enumerate(sblocks):
        if not sn[i]:
            continue
        rb, ab1, ab2, sb = best(sn[i], d_blk)
        rs, as1, as2, ss = best(sn[i], d_sent)
        kind, ratio, span = judge(rb, rs, (ab1, ab2), (as1, as2))
        if kind == "identical":
            kind = "found"
        rec = {"i": i, "kind": kind, "ratio": round(ratio, 3),
               "draft_span": list(span), "text": snippet(s)}
        if kind == "unexplained":
            rec["second"] = round(max(sb, ss), 3)
        backward.append(rec)

    return {"draft": draft_path, "source": source_path, "threshold": threshold,
            "draft_blocks": len(dblocks), "source_blocks": len(sblocks),
            "forward": forward, "backward": backward}


def report(res) -> int:
    f, b = res["forward"], res["backward"]
    f_un = [x for x in f if x["kind"] == "unexplained"]
    b_un = [x for x in b if x["kind"] == "unexplained"]

    print("溯源审计：%s  ←  %s" % (res["draft"], res["source"]))
    print("阈值 %.2f · 本稿 %d 段 · 源稿 %d 段" %
          (res["threshold"], res["draft_blocks"], res["source_blocks"]))
    print("-" * 78)

    def tally(rows):
        d = {}
        for r in rows:
            d[r["kind"]] = d.get(r["kind"], 0) + 1
        return d

    print("正向（本稿 → 源稿）：", "  ".join("%s %d" % kv for kv in sorted(tally(f).items())))
    print("反向（源稿 → 本稿）：", "  ".join("%s %d" % kv for kv in sorted(tally(b).items())))

    if f_un:
        print("\n⚠ 正向待判定（本稿有、源稿找不到 —— 扩写藏在这里）：")
        for r in f_un:
            print("  段%-4d 相似度 %.2f（次高 %.2f）  「%s」" %
                  (r["i"], r["ratio"], r.get("second", 0), r["text"]))
    if b_un:
        print("\n⚠ 反向待判定（源稿有、本稿落下了）：")
        for r in b_un:
            print("  段%-4d 相似度 %.2f（次高 %.2f）  「%s」" %
                  (r["i"], r["ratio"], r.get("second", 0), r["text"]))

    total = len(f_un) + len(b_un)
    print("-" * 78)
    if total == 0:
        print("✓ 无待判定项：本稿相对源稿只剩排版差异、图注编号与结尾附加句")
        return 0
    print("✗ %d 项待人工判定（正向新增 %d · 反向遗漏 %d）" % (total, len(f_un), len(b_un)))
    print("  判定口径：每一项要么归入「已声明的事实修正 / 已声明的增补」，")
    print("  要么就是不该出现的改动 —— 见技能 SKILL.md「改稿底线」。")
    print("  源稿里后加的块（勘误等）用 --skip '^>\\s*\\[!' 排除。")
    return 1


def main():
    ap = argparse.ArgumentParser(
        description="双向逐段溯源审计：查改稿有没有悄悄扩写或漏掉")
    ap.add_argument("--draft", required=True, help="派生稿（如 公众号稿.md）")
    ap.add_argument("--source", required=True, help="源稿（如 源稿-X长文.md）")
    ap.add_argument("--threshold", type=float, default=0.72,
                    help="相似度阈值，低于它即待判定（默认 0.72）")
    ap.add_argument("--skip", action="append", default=[],
                    help="正则：命中的段直接排除（可重复，两侧都生效）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--verbose", action="store_true", help="打印逐段明细")
    args = ap.parse_args()

    for p in (args.draft, args.source):
        try:
            open(p, encoding="utf-8").close()
        except OSError as e:
            print("✗ 读不到文件：%s（%s）" % (p, e), file=sys.stderr)
            return 2

    try:
        skips = [re.compile(rx) for rx in args.skip]
    except re.error as e:
        print("✗ --skip 正则非法：%s" % e, file=sys.stderr)
        return 2

    res = audit(args.draft, args.source, args.threshold, skips)

    if args.verbose:
        print("逐段明细：")
        for tag, rows in (("正", res["forward"]), ("反", res["backward"])):
            for r in rows:
                print("  %s 段%-4d %-11s %.2f  %s" %
                      (tag, r["i"], r["kind"], r["ratio"], r["text"]))
        print("-" * 78)

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if not any(x["kind"] == "unexplained"
                            for x in res["forward"] + res["backward"]) else 1
    return report(res)


if __name__ == "__main__":
    sys.exit(main())
