#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""push-to-topstream.py — 反向回推：公众号稿 → topstream/notes 纯 Markdown。

反向链路的最后一公里最容易出错：`::: 容器`、`==高亮==`、`[!徽章]` 等公众号专用语法
绝不能写进 notes/（仓库原文保持纯 Markdown）。本脚本做「降级转换」并生成 README 索引条目。

降级规则：
  - 剥离 frontmatter
  - `:::` 围栏行删除，容器内文本原样保留
  - `==高亮==` → 去掉 `==`
  - `[!徽章]` / `[!xxx]` → 整段删除
  - `[文字](url)` 外链保留（GitHub markdown 支持）
  - 中英文盘古之白保留（对 notes 同样适用）

Usage:
    python3 push-to-topstream.py <包目录> [--target notes/xxx.md] [--apply]
    # 默认 dry-run：打印降级预览 + 语法统计 + README 索引条目，不写盘
"""

import argparse
import os
import re
import sys

def _default_base():
    """交付包根：CLI --base → env TOPMIND_WECHAT_BASE → env TOPMIND_WORKSPACE 发现 → 惯例路径。"""
    env = os.environ.get("TOPMIND_WECHAT_BASE") or os.environ.get("TOPMIND_WECHAT_PACKAGE_ROOT")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    ws = os.environ.get("TOPMIND_WORKSPACE")
    if ws:
        for rel in (
            ("40-创作", "2026-公众号"),
            ("20-专题", "2026-公众号"),
            ("88-交付", "2026-公众号"),
        ):
            p = os.path.join(ws, *rel)
            if os.path.isdir(p):
                return p
        return os.path.join(ws, "40-创作", "2026-公众号")
    # 惯例：父工作区（可被 CLI 覆盖）
    return os.path.join(
        os.path.expanduser("~"), "TopWorkSpace", "topmind-workspace",
        "40-创作", "2026-公众号")


def _default_topstream():
    env = os.environ.get("TOPSTREAM_ROOT") or os.environ.get("TOPMIND_TOPSTREAM")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    return os.path.join(os.path.expanduser("~"), "TopWorkSpace", "topstream")

DEFAULT_BASE = _default_base()
DEFAULT_TOPSTREAM = _default_topstream()

CONTAINER_RE = re.compile(r"^:::\s*\w*\s*$")
HIGHLIGHT_RE = re.compile(r"==([^=]+)==")
BADGE_RE = re.compile(r"\[![^\]]*\]")


def split_fm(text):
    if not text.startswith("---\n"):
        return None, text
    i = text.find("\n---", 3)
    if i < 0:
        return None, text
    return text[4:i], text[i + 4:].lstrip("\n")


def get_field(fm, key, default=""):
    if not fm:
        return default
    m = re.search(r"^%s:\s*(.*)$" % re.escape(key), fm, re.M)
    if not m:
        return default
    v = m.group(1).strip()
    return v.strip('"').strip("'") if v else default


def downgrade(body):
    """公众号稿正文 → notes 纯 Markdown。返回 (文本, 统计)"""
    stats = {"container": 0, "highlight": 0, "badge": 0}
    out = []
    for line in body.split("\n"):
        if CONTAINER_RE.match(line.strip()):
            stats["container"] += 1
            continue
        if BADGE_RE.search(line):
            stats["badge"] += len(BADGE_RE.findall(line))
            line = BADGE_RE.sub("", line).strip()
            if not line:
                continue
        line, n = HIGHLIGHT_RE.subn(r"\1", line)
        stats["highlight"] += n
        out.append(line)
    return "\n".join(out).strip("\n") + "\n", stats


def make_readme_entry(title, target, tags):
    tag_str = " ".join("`%s`" % t for t in tags)
    return (
        "- [**%s**](%s)  \n"
        "  描述：<一句话介绍这篇文章解决了什么问题、读者能带走什么>  \n"
        "  %s\n" % (title, target, tag_str)
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pkg", help="包目录名（相对 base）或绝对路径")
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--topstream", default=DEFAULT_TOPSTREAM)
    ap.add_argument("--target", help="回推目标 notes/xxx.md（缺省读 frontmatter target_file）")
    ap.add_argument("--apply", action="store_true", help="实际写盘（默认只预览）")
    ap.add_argument("--force", action="store_true", help="目标已存在时覆盖")
    args = ap.parse_args()

    pkg_path = args.pkg if os.path.isabs(args.pkg) else os.path.join(args.base, args.pkg)
    draft = os.path.join(pkg_path, "公众号稿.md")
    if not os.path.exists(draft):
        print("✗ 找不到公众号稿：%s" % draft)
        return 1

    text = open(draft, encoding="utf-8").read()
    fm, body = split_fm(text)
    title = get_field(fm, "title") or get_field(fm, "title", "")
    status = get_field(fm, "status", "草稿")
    target_file = get_field(fm, "target_file", "")
    tags = []
    mt = re.search(r"^tags:\s*\[(.*)\]$", fm or "", re.M)
    if mt:
        tags = [t.strip().strip('"').strip("'") for t in mt.group(1).split(",") if t.strip()]
    tags = [t for t in tags if t not in ("公众号", "排版")]

    target = args.target or (target_file if target_file != "pending" else "")
    if not target:
        print("✗ 需要回推目标：--target notes/xxx.md（frontmatter target_file 仍为 pending）")
        return 1
    if not target.startswith("notes/"):
        print("✗ target 应以 notes/ 开头：%s" % target)
        return 1

    body_md, stats = downgrade(body)

    # 确保有 H1 标题开头
    if not body_md.lstrip().startswith("# "):
        body_md = "# %s\n\n%s" % (title, body_md)

    out_path = os.path.join(args.topstream, target)

    print("回推预览：%s" % os.path.basename(pkg_path))
    print("  标题     : %s" % title)
    print("  状态     : %s" % status)
    print("  目标     : %s" % target)
    print("  降级统计 : 容器 %d · 高亮 %d · 徽章 %d"
          % (stats["container"], stats["highlight"], stats["badge"]))
    if status != "定稿":
        print("  ⚠ status=%s，回推前应先定稿（sync-status.py --set 定稿）" % status)
    print("")
    print("—— README 索引条目（复制到 topstream/README.md 的「研析心得」段）——")
    print(make_readme_entry(title, target, tags))

    if args.apply:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        if os.path.exists(out_path) and not args.force:
            print("✗ 目标已存在，加 --force 覆盖：%s" % out_path)
            return 1
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(body_md)
        print("")
        print("✓ 已写入 %s（%d 字节）" % (out_path, len(body_md.encode("utf-8"))))
        print("  下一步：把上面的 README 条目插进 topstream/README.md；")
        print("  然后回本包改 frontmatter：target_file 从 pending 改为 %s" % target)
        print("  （可用：sync-status.py 之外手动改 target_file 字段，或用编辑器）")
    else:
        print("")
        print("[dry-run] 加 --apply 实际写盘。写盘不会自动改 README 与 frontmatter，")
        print("        这两步由你/agent 手工完成，保证索引不漂移。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
