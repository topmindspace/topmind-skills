#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scan_ai_flavor.py — 转发器：调用 qu-aiwei-zh 的 canonical 检测脚本。

**本文件不含检测实现。** 原因见下。

## 为什么是转发器而不是自带副本

topmind-wechat 曾自带一份 463 行的实现副本，它是 `qu-aiwei-zh` 在加入「E 类 · 作者姿态层」
**之前**的旧快照 —— 不输出姿态参考分，也识别不了姿态类 AI 痕迹。照 SKILL.md 跑它，会拿到一个
**没有姿态维度的「100 分」**：看着干净，其实少了一整个维度。

两版实测差异：旧副本 0 处「姿态」相关代码，canonical 20 处。

副本必然再次漂移（一边改了另一边不知道），所以这里只保留入口，实现归 canonical 一处。

## canonical 查找顺序（命中即用）

1. `$QU_AIWEI_SCAN`                       显式指定（测试与非标准安装用）
2. `~/.workbuddy/skills/qu-aiwei-zh/scripts/scan_ai_flavor.py`
3. `~/.agents/skills/qu-aiwei-zh/scripts/scan_ai_flavor.py`
4. `~/.claude/skills/qu-aiwei-zh/scripts/scan_ai_flavor.py`
5. `~/.codex/skills/qu-aiwei-zh/scripts/scan_ai_flavor.py`

## 行为

- 参数原样透传（位置参数 `<file>` / `--json` / `-o` / `-` 管道都可用），stdin / stdout / stderr 继承
- 退出码取 canonical 的退出码
- `--which` 只打印解析到的 canonical 路径并退出 0（转发器自有开关，canonical 无此参数）
- **找不到 canonical 时报错退出（exit 3），不静默降级** —— 宁可这一步跑不了，
  也不要给出一个没有姿态分的分数

## 用法

    python3 scripts/scan_ai_flavor.py <包>/公众号稿.md      # 目标 ≥85
    python3 scripts/scan_ai_flavor.py --which
"""

from __future__ import annotations

import os
import sys

REL = os.path.join("qu-aiwei-zh", "scripts", "scan_ai_flavor.py")

CANDIDATES = [
    os.path.join("~", ".workbuddy", "skills", REL),
    os.path.join("~", ".agents", "skills", REL),
    os.path.join("~", ".claude", "skills", REL),
    os.path.join("~", ".codex", "skills", REL),
]

MISSING = """\
✗ 找不到 qu-aiwei-zh 的 canonical 检测脚本，无法执行「文字关」。

  本目录不再自带实现 —— 曾经那份是 E 类姿态检测之前的旧快照，会漏掉姿态维度。
  已查找：
{paths}

  解决：安装 qu-aiwei-zh 技能，或用环境变量显式指定：
      export QU_AIWEI_SCAN=/path/to/qu-aiwei-zh/scripts/scan_ai_flavor.py
"""


def resolve():
    """返回 canonical 脚本的绝对路径；找不到返回 None。"""
    env = os.environ.get("QU_AIWEI_SCAN")
    if env:
        p = os.path.abspath(os.path.expanduser(env))
        return p if os.path.isfile(p) else None
    for c in CANDIDATES:
        p = os.path.abspath(os.path.expanduser(c))
        if os.path.isfile(p):
            return p
    return None


def main():
    args = sys.argv[1:]

    if args and args[0] == "--which":
        target = resolve()
        if target:
            print(target)
            return 0
        print("✗ 未解析到 canonical 脚本；用 QU_AIWEI_SCAN 指定或安装 qu-aiwei-zh",
              file=sys.stderr)
        return 3

    target = resolve()
    if not target:
        shown = [os.path.abspath(os.path.expanduser(c)) for c in CANDIDATES]
        sys.stderr.write(MISSING.format(paths="\n".join("      " + p for p in shown)))
        return 3

    os.execv(sys.executable, [sys.executable, target] + args)
    return 0  # 不会到达


if __name__ == "__main__":
    sys.exit(main())
