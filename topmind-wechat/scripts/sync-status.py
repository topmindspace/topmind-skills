#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sync-status.py — 同步公众号交付包的「状态 ⇄ 目录名 ⇄ 字数」。

规则（与专题 topic.md 的目录规范一致）：
  status = 草稿            → 目录名 YYYY-MM-DD-<中文名>
  status = 定稿 / 已发布    → 目录名 YYYY-MM-DD-<中文名>-released

同时刷新 frontmatter 的 word_count（正文中文字数）。

Usage:
    python3 sync-status.py                       # 扫描全部，只报告（dry-run）
    python3 sync-status.py --apply               # 实际重命名并回写字数
    python3 sync-status.py --set 定稿 <包目录>    # 改状态 + 同步目录名
    python3 sync-status.py --base <专题目录>
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

FINAL_STATUSES = ("定稿", "已发布")
VALID_STATUSES = ("草稿",) + FINAL_STATUSES
RELEASED_SUFFIX = "-released"


def split_fm(text):
    """返回 (frontmatter, body, head, tail_sep)；无 frontmatter 时 fm=None"""
    if not text.startswith("---\n"):
        return None, text, "", ""
    i = text.find("\n---", 3)
    if i < 0:
        return None, text, "", ""
    return text[4:i], text[i + 4:].lstrip("\n"), text[:4], text[i:i + 4]


def get_field(fm, key):
    m = re.search(r"^%s:\s*(.*)$" % re.escape(key), fm, re.M)
    return m.group(1).strip().strip('"') if m else None


def set_field(fm, key, val):
    line = "%s: %s" % (key, val)
    pat = re.compile(r"^%s:\s*.*$" % re.escape(key), re.M)
    if pat.search(fm):
        return pat.sub(line, fm, count=1)
    return fm.rstrip("\n") + "\n" + line + "\n"


def scan(base):
    """返回 [(dirname, status, word_count, needs_rename, target_name)]"""
    rows = []
    for name in sorted(os.listdir(base)):
        pkg = os.path.join(base, name)
        draft = os.path.join(pkg, "公众号稿.md")
        if not os.path.isdir(pkg) or not os.path.exists(draft):
            continue
        text = open(draft, encoding="utf-8").read()
        fm, body, head, sep = split_fm(text)
        if fm is None:
            rows.append((name, None, None, False, None, "无 frontmatter"))
            continue
        status = get_field(fm, "status") or "草稿"
        cn = len(re.findall(r"[\u4e00-\u9fff]", body))

        want_final = status in FINAL_STATUSES
        stem = name[:-len(RELEASED_SUFFIX)] if name.endswith(RELEASED_SUFFIX) else name
        target = stem + (RELEASED_SUFFIX if want_final else "")
        rows.append((name, status, cn, target != name, target, ""))
    return rows


def apply_rename(base, name, target, draft_path, fm, body, head, new_fm):
    """写回 frontmatter 后重命名目录"""
    open(draft_path, "w", encoding="utf-8").write("---\n" + new_fm + "\n---\n\n" + body)
    if target != name:
        os.rename(os.path.join(base, name), os.path.join(base, target))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--apply", action="store_true", help="实际执行（默认只报告）")
    ap.add_argument("--set", metavar="STATUS", choices=VALID_STATUSES,
                    help="把指定包改成该状态（需配合包名）")
    ap.add_argument("pkg", nargs="?", help="包目录名（配合 --set 使用）")
    args = ap.parse_args()

    if not os.path.isdir(args.base):
        print("✗ 专题目录不存在：%s" % args.base)
        return 1

    # 单包改状态
    if args.set:
        if not args.pkg:
            print("✗ --set 需要指定包目录名")
            return 1
        draft = os.path.join(args.base, args.pkg, "公众号稿.md")
        if not os.path.exists(draft):
            print("✗ 找不到：%s" % draft)
            return 1
        text = open(draft, encoding="utf-8").read()
        fm, body, head, sep = split_fm(text)
        if fm is None:
            print("✗ 该文件无 frontmatter")
            return 1
        fm = set_field(fm, "status", args.set)
        cn = len(re.findall(r"[\u4e00-\u9fff]", body))
        fm = set_field(fm, "word_count", str(cn))

        want_final = args.set in FINAL_STATUSES
        stem = args.pkg[:-len(RELEASED_SUFFIX)] if args.pkg.endswith(RELEASED_SUFFIX) else args.pkg
        target = stem + (RELEASED_SUFFIX if want_final else "")

        if args.apply:
            apply_rename(args.base, args.pkg, target, draft, fm, body, head, fm)
            print("✓ %s → status=%s，目录 %s（%d 中文字）" % (
                args.pkg, args.set, target if target != args.pkg else "不变", cn))
        else:
            print("[dry-run] %s → status=%s，目录将变为 %s" % (args.pkg, args.set, target))
        return 0

    rows = scan(args.base)
    if not rows:
        print("专题下没有交付包：%s" % args.base)
        return 0

    print("%-44s %-6s %8s  %s" % ("包目录", "状态", "中文字", "待同步"))
    print("-" * 84)
    changed = 0
    for name, status, cn, needs, target, note in rows:
        if status is None:
            print("%-44s %-6s %8s  %s" % (name, "-", "-", note))
            continue
        flag = "→ " + target if needs else ""
        print("%-44s %-6s %8s  %s" % (name, status, cn, flag))

        if args.apply:
            draft = os.path.join(args.base, name, "公众号稿.md")
            text = open(draft, encoding="utf-8").read()
            fm, body, head, sep = split_fm(text)
            fm = set_field(fm, "word_count", str(cn))
            apply_rename(args.base, name, target, draft, fm, body, head, fm)
            if needs:
                changed += 1

    if args.apply:
        print("\n✓ 已刷新 %d 个包的 word_count，重命名 %d 个目录" % (len(rows), changed))
    else:
        pending = sum(1 for r in rows if r[3])
        print("\n[dry-run] %d 个包目录名与状态不一致，加 --apply 执行" % pending)
    return 0


if __name__ == "__main__":
    sys.exit(main())
