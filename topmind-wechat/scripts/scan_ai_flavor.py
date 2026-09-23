#!/usr/bin/env python3
"""
scan_ai_flavor.py — 中文 AI 味检测脚本

用法：
  python3 scan_ai_flavor.py <file>            # 输出 Markdown 报告
  python3 scan_ai_flavor.py --json <file>     # 输出 JSON
  python3 scan_ai_flavor.py -o report.md <file>
  cat article.md | python3 scan_ai_flavor.py - # 管道

设计目标：纯 stdlib，无第三方依赖，能在普通 Mac / Linux 上直接跑。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable


# --------------------------------------------------------------------------- #
# 模式定义：每条 (类别代码, 类别名, 正则, 单次扣分, 严重度, 开头末尾加权, 备注)
# --------------------------------------------------------------------------- #


@dataclass
class Pattern:
    code: str          # e.g. "A1"
    name: str          # e.g. "开头套话"
    regex: str         # 正则字符串
    penalty: int       # 单次扣分（绝对值）
    severity: str      # high / mid / low
    weighted: str = "" # "head" | "tail" | ""（加权区段）
    note: str = ""

    def compiled(self) -> re.Pattern:
        return re.compile(self.regex)


# 头部加权的模式（命中位置 ≤ 200 字 权重 ×1.5）
HEAD_PATTERNS: list[Pattern] = [
    Pattern("A1", "开头套话", r"在当今(社会|时代)", 8, "high", "head"),
    Pattern("A1", "开头套话", r"随着[^，。]{2,30}的(发展|日益|不断)", 8, "high", "head"),
    Pattern("A1", "开头套话", r"众所周知[，,]", 7, "high", "head"),
    Pattern("A1", "开头套话", r"毋庸置疑[，,]|不可否认[，,]", 7, "high", "head"),
    Pattern("A1", "开头套话", r"近年来[^，。]{0,15}日益", 6, "high", "head"),
    Pattern("A1", "开头套话", r"伴随着[^，。]{2,30}的(快速|迅猛)", 8, "high", "head"),
    Pattern("A1", "开头套话", r"在[^，。]{2,20}的背景下", 5, "mid", "head"),
    Pattern("A1", "开头套话", r"一直以来[^，。]{2,20}都", 4, "low", "head"),
    Pattern("A10", "模板口水", r"大家好[，,]", 6, "high", "head"),
    Pattern("A10", "模板口水", r"本文将从[^，。]{0,30}个方面", 7, "high", "head"),
    Pattern("A10", "模板口水", r"希望本文能够", 5, "mid", "head"),
    Pattern("A10", "模板口水", r"如(有不当|有疏漏|有错误)[，,]", 4, "low", "head"),
]

# 全文模式
BODY_PATTERNS: list[Pattern] = [
    # A2 转折连接
    Pattern("A2", "转折连接", r"此外[，,]", 2, "low"),
    Pattern("A2", "转折连接", r"与此同时[，,]", 2, "low"),
    Pattern("A2", "转折连接", r"不仅如此[，,]", 2, "low"),
    Pattern("A2", "转折连接", r"综上所述[，,]", 4, "mid"),
    Pattern("A2", "转折连接", r"总而言之[，,]", 4, "mid"),
    Pattern("A2", "转折连接", r"一方面[^，。]{1,15}[，,另一方面]", 3, "low"),
    Pattern("A2", "转折连接", r"既[^，。]{1,12}又[^，。]{1,12}还", 3, "low"),
    Pattern("A2", "转折连接", r"无可厚非", 4, "mid"),
    Pattern("A2", "转折连接", r"瑕不掩瑜", 4, "mid"),

    # A3 形容词/官腔
    Pattern("A3", "官腔形容词", r"至关重要", 5, "high"),
    Pattern("A3", "官腔形容词", r"举足轻重", 5, "high"),
    Pattern("A3", "官腔形容词", r"不可或缺", 4, "mid"),
    Pattern("A3", "官腔形容词", r"深入(探讨|分析|研究)", 5, "high"),
    Pattern("A3", "官腔形容词", r"高度重视", 5, "high"),
    Pattern("A3", "官腔形容词", r"深入推进", 5, "high"),
    Pattern("A3", "官腔形容词", r"扎实开展", 5, "high"),
    Pattern("A3", "官腔形容词", r"积极探索", 4, "mid"),
    Pattern("A3", "官腔形容词", r"有效落实", 4, "mid"),
    Pattern("A3", "官腔形容词", r"持续优化", 4, "mid"),
    Pattern("A3", "官腔形容词", r"凝聚共识", 5, "high"),
    Pattern("A3", "官腔形容词", r"汇聚合力", 5, "high"),
    Pattern("A3", "官腔形容词", r"协同推进", 4, "mid"),
    Pattern("A3", "官腔形容词", r"全方位(提升|推进|优化)", 4, "mid"),
    Pattern("A3", "官腔形容词", r"多角度(分析|审视)", 4, "mid"),
    Pattern("A3", "官腔形容词", r"立体化", 3, "low"),
    # 注：数字化/智能化 是领域术语，不作为 AI 味标志，跳过

    # A5 排比/三段式
    Pattern("A5", "排比三段式", r"这不仅[^，。]{2,20}[，,][^，。]{2,15}也[^，。]{2,15}[，,更]?", 6, "high"),
    Pattern("A5", "排比三段式", r"从[^，。]{2,15}到[^，。]{2,15}[，,从][^，。]{2,15}到", 4, "mid"),

    # A6 营销体
    Pattern("A6", "营销黑话", r"赋能", 5, "high"),
    Pattern("A6", "营销黑话", r"加持", 5, "high"),
    Pattern("A6", "营销黑话", r"引爆", 5, "high"),
    Pattern("A6", "营销黑话", r"破圈", 5, "high"),
    Pattern("A6", "营销黑话", r"一站式", 4, "mid"),
    Pattern("A6", "营销黑话", r"全链路", 4, "mid"),
    Pattern("A6", "营销黑话", r"闭环", 4, "mid"),
    Pattern("A6", "营销黑话", r"抓手", 5, "high"),
    Pattern("A6", "营销黑话", r"底层逻辑", 5, "high"),
    Pattern("A6", "营销黑话", r"顶层设计", 5, "high"),
    Pattern("A6", "营销黑话", r"(打造|构建|重塑)[^，。]{2,15}(方案|生态|体系|平台)", 3, "low"),
    Pattern("A6", "营销黑话", r"拉通|对齐|复盘", 3, "low"),
    # 工程圈行话：用户明确点过——「踩坑」这类词读起来像圈内口令，不像人在说话
    Pattern("A6", "工程圈行话", r"踩坑|避坑|干货|踩出来的坑|踩过的坑", 3, "low"),

    # A7 模糊归因
    Pattern("A7", "模糊归因", r"专家指出", 5, "high"),
    Pattern("A7", "模糊归因", r"业内人士表示", 5, "high"),
    Pattern("A7", "模糊归因", r"据相关(研究|调查|数据)表明", 5, "high"),
    Pattern("A7", "模糊归因", r"大量数据表明", 5, "high"),
    Pattern("A7", "模糊归因", r"有学者认为", 4, "mid"),
    Pattern("A7", "模糊归因", r"专家(普遍|一致)认为", 4, "mid"),
    Pattern("A7", "模糊归因", r"大家普遍认为", 3, "low"),

    # A8 伪深度
    Pattern("A8", "伪深度", r"(是|为)[^，。]{2,15}的(体现|证明|象征)", 5, "high"),
    Pattern("A8", "伪深度", r"彰显了[^，。]{2,20}(意义|价值|精神)", 5, "high"),
    Pattern("A8", "伪深度", r"凸显了[^，。]{2,20}(意义|价值)", 5, "high"),
    Pattern("A8", "伪深度", r"反映了更深(层次)的", 4, "mid"),

    # A9 假大空成语
    Pattern("A9", "假大空成语", r"博大精深", 4, "mid"),
    Pattern("A9", "假大空成语", r"源远流长", 4, "mid"),
    Pattern("A9", "假大空成语", r"历久弥新", 4, "mid"),
    Pattern("A9", "假大空成语", r"与时俱进", 3, "low"),
    Pattern("A9", "假大空成语", r"开拓创新", 3, "low"),
    Pattern("A9", "假大空成语", r"锐意进取", 3, "low"),
    Pattern("A9", "假大空成语", r"举世(瞩目|无双)", 4, "mid"),

    # A10 模板口水
    Pattern("A10", "模板口水", r"感谢(您的)?(观看|阅读|支持)", 5, "high"),
    Pattern("A10", "模板口水", r"以上就是[^，。]{2,30}(全部)?内容", 5, "high"),
    Pattern("A10", "模板口水", r"欢迎(指正|交流|留言)", 4, "mid"),
]

# 尾部加权
TAIL_PATTERNS: list[Pattern] = [
    Pattern("A4", "结尾升华", r"让我们(共同|一起)", 8, "high", "tail"),
    Pattern("A4", "结尾升华", r"未来可期", 6, "high", "tail"),
    Pattern("A4", "结尾升华", r"任重道远", 6, "high", "tail"),
    Pattern("A4", "结尾升华", r"砥砺前行|扬帆远航", 5, "high", "tail"),
    Pattern("A4", "结尾升华", r"在[^，。]{2,20}的道路上(不断)?前行", 6, "high", "tail"),
    Pattern("A4", "结尾升华", r"为[^，。]{2,15}贡献(自己)?的?力量", 6, "high", "tail"),
    Pattern("A4", "结尾升华", r"谱写[^，。]{2,15}新篇章", 6, "high", "tail"),
    Pattern("A4", "结尾升华", r"展望未来", 4, "mid", "tail"),
]

ALL_PATTERNS = HEAD_PATTERNS + BODY_PATTERNS + TAIL_PATTERNS


# --------------------------------------------------------------------------- #
# 数据结构
# --------------------------------------------------------------------------- #


@dataclass
class Hit:
    code: str
    name: str
    pattern: str
    text: str
    line: int
    column: int
    severity: str
    penalty: int
    raw_penalty: int  # 加权前


@dataclass
class Report:
    score: int
    level: str
    level_emoji: str
    hits: list[Hit] = field(default_factory=list)
    lexical_deduction: int = 0
    structural_deduction: int = 0
    stats: dict = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# 扫描逻辑
# --------------------------------------------------------------------------- #


def scan_text(text: str) -> Report:
    lines = text.splitlines()
    total_chars = len(text)
    total_lines = len(lines)
    head_chars = "".join(lines[: max(1, total_lines // 5)])  # 前 20%
    tail_chars = "".join(lines[-max(1, total_lines // 5):])  # 后 20%

    hits: list[Hit] = []
    seen_in_text: dict[tuple[str, str], int] = {}  # (pattern, exact_text) → 第 N 次出现

    for p in ALL_PATTERNS:
        regex = p.compiled()
        for m in regex.finditer(text):
            # 计算行号/列号
            start = m.start()
            line_no = text.count("\n", 0, start) + 1
            col_no = start - (text.rfind("\n", 0, start) + 1) + 1

            # 计算加权：位置决定
            region = "body"
            if p.weighted == "head" and start < len(head_chars):
                region = "head"
            elif p.weighted == "tail" and start >= len(text) - len(tail_chars):
                region = "tail"

            raw = p.penalty
            if region != "body":
                raw = int(raw * 1.5)

            # 重复衰减：同一模式第 N 次出现
            key = (p.regex, m.group(0))
            n = seen_in_text.get(key, 0) + 1
            seen_in_text[key] = n
            multiplier = min(n, 3)  # 最多 3 次

            final = raw * multiplier

            hits.append(
                Hit(
                    code=p.code,
                    name=p.name,
                    pattern=p.regex,
                    text=m.group(0),
                    line=line_no,
                    column=col_no,
                    severity=p.severity,
                    penalty=final,
                    raw_penalty=raw,
                )
            )

    # 结构扣分
    structural = 0
    # 重复的段首加粗标签：**结论**：/ **踩坑提醒**：/ **注意**： …
    # 这是模板化写作最典型的痕迹，词面词表抓不到，只能按"同一标签重复出现"判定。
    # 判据取 ≥3 次：用两次属于正常强调，用三次以上就是在套模板。
    lead_labels = re.findall(r"^\s*\*\*([^*\n]{1,10})\*\*\s*[：:]", text, re.M)
    repeated_labels: list[str] = []
    if lead_labels:
        counts = Counter(lead_labels)
        repeated_labels = [k for k, v in counts.items() if v >= 3]
    if total_lines >= 5:
        # 破折号过多
        dash_count = text.count("——")
        if dash_count >= max(3, total_chars // 200):
            structural -= 5
        # 感叹号过多
        if text.count("！！！") >= 1 or text.count("!!") >= 3:
            structural -= 3
        # 缺乏具体细节（无任何数字）
        if not re.search(r"\d", text):
            structural -= 12
        # 缺乏个性化声音（无第一人称）
        if not re.search(r"[我我们]", text):
            structural -= 8
        # 标题 emoji 滥用
        emoji_count = len(re.findall(r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF]", text))
        if emoji_count >= 3:
            structural -= min(9, (emoji_count - 2) * 3)
        # 段首加粗标签模板化
        if repeated_labels:
            structural -= min(12, sum(lead_labels.count(k) for k in repeated_labels) * 2)

    # 词面扣分汇总
    # 注意：structural 累加时是负数（structural -= n），必须取绝对值再相加。
    # 若直接相加，lexical + structural 会变成"加分"，结构扣分整条维度静默失效。
    lexical = sum(h.penalty for h in hits)
    structural = abs(structural)
    total_deduction = lexical + structural
    score = max(0, min(100, 100 - total_deduction))

    level, level_emoji = grade(score)

    # 生成建议（Top 3）
    suggestions = build_suggestions(hits, score)
    if repeated_labels:
        tips = "、".join(f"**{k}**：×{lead_labels.count(k)}" for k in repeated_labels)
        suggestions.insert(0, f"段首加粗标签模板化 — {tips}，同一标签重复 3 次以上就是在套模板，改成直陈句")

    return Report(
        score=score,
        level=level,
        level_emoji=level_emoji,
        hits=hits,
        lexical_deduction=lexical,
        structural_deduction=structural,
        stats={
            "total_chars": total_chars,
            "total_lines": total_lines,
            "ai_pattern_count": len(hits),
            "repeated_lead_labels": repeated_labels,
        },
        suggestions=suggestions,
    )


def grade(score: int) -> tuple[str, str]:
    if score >= 85:
        return "人话", "🟢"
    if score >= 70:
        return "微 AI 味", "🟡"
    if score >= 50:
        return "中度 AI 味", "🟠"
    if score >= 30:
        return "重度 AI 味", "🔴"
    return "完全 AI 体", "⚫"


def build_suggestions(hits: list[Hit], score: int) -> list[str]:
    """按类别聚类，给出 3 条优先建议。"""
    by_code: dict[str, list[Hit]] = {}
    for h in hits:
        by_code.setdefault(h.code, []).append(h)

    # 优先级：A4>A3>A6>A7>A1>A8>A10>A5>A9
    priority = ["A4", "A3", "A6", "A7", "A1", "A8", "A10", "A5", "A9"]
    tips_map = {
        "A1": "开头套话 — 删掉'在当今社会'等模板开头，直接说事实",
        "A2": "转折词 — 用句号断开，靠上下文自然过渡",
        "A3": "官腔形容词 — 换成大白话或具体数字",
        "A4": "结尾升华 — 删掉'让我们共同'等空话，给具体计划",
        "A5": "排比三段式 — 砍到两项或四项，别硬凑三段",
        "A6": "营销黑话 — 改为具体动词，如'做了一个工具'",
        "A7": "模糊归因 — 给具体名字/出处/数字",
        "A8": "伪深度 — 删除'是 XX 的体现/证明'句式",
        "A9": "假大空成语 — 用白话翻译一遍",
        "A10": "模板口水 — 删掉口水句，直接进入正文",
    }

    suggestions = []
    for code in priority:
        if code in by_code:
            n = len(by_code[code])
            suggestions.append(f"{tips_map[code]}（命中 {n} 处）")
        if len(suggestions) >= 3:
            break

    if not suggestions:
        suggestions.append("未发现明显 AI 模式，但建议人工通读检查结构/个性化声音")

    return suggestions


# --------------------------------------------------------------------------- #
# 输出格式
# --------------------------------------------------------------------------- #


def render_markdown(report: Report, source: str) -> str:
    md: list[str] = []
    md.append(f"## AI 味检测报告\n")
    md.append(f"**文件：** `{source}`  ")
    md.append(f"**总分：** **{report.score}** / 100  {report.level_emoji} {report.level}\n")

    md.append("### 分项评分")
    md.append(f"- 词面命中扣分：**-{report.lexical_deduction}**")
    md.append(f"- 结构问题扣分：**{report.structural_deduction}**")
    md.append(f"- 总计：**-{report.lexical_deduction + abs(report.structural_deduction)}** → {report.score} 分\n")

    md.append("### 基础统计")
    md.append(f"- 字符数：{report.stats.get('total_chars', 0)}")
    md.append(f"- 行数：{report.stats.get('total_lines', 0)}")
    md.append(f"- AI 模式命中数：**{report.stats.get('ai_pattern_count', 0)}**")
    reps = report.stats.get("repeated_lead_labels") or []
    if reps:
        md.append(f"- 重复段首加粗标签：**{'、'.join(reps)}**")
    md.append("")

    if report.hits:
        md.append("### 命中位置（按严重度排序）")
        md.append("| # | 类别 | 命中内容 | 位置 | 严重度 | 扣分 |")
        md.append("|---|---|---|---|---|---|")
        sorted_hits = sorted(report.hits, key=lambda h: -h.penalty)
        for i, h in enumerate(sorted_hits[:30], 1):
            preview = h.text if len(h.text) <= 25 else h.text[:25] + "…"
            md.append(f"| {i} | {h.code} {h.name} | `{preview}` | 第 {h.line} 行 | {h.severity} | -{h.penalty} |")
        if len(report.hits) > 30:
            md.append(f"\n*（还有 {len(report.hits) - 30} 处命中未显示）*\n")
    else:
        md.append("### 命中位置")
        md.append("无命中 🎉\n")

    md.append("### Top 3 优先改写建议")
    for s in report.suggestions:
        md.append(f"1. {s}")
    md.append("")

    return "\n".join(md)


def render_json(report: Report) -> str:
    return json.dumps(
        {
            "score": report.score,
            "level": report.level,
            "level_emoji": report.level_emoji,
            "deductions": {
                "lexical": report.lexical_deduction,
                "structural": report.structural_deduction,
            },
            "stats": report.stats,
            "hits": [asdict(h) for h in report.hits],
            "suggestions": report.suggestions,
        },
        ensure_ascii=False,
        indent=2,
    )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="中文 AI 味检测器 — 给文章打 AI 味分数"
    )
    parser.add_argument("input", help="输入文件路径，或 '-' 表示 stdin")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("-o", "--output", help="输出文件（默认 stdout）")
    args = parser.parse_args(argv)

    # 读取输入
    if args.input == "-":
        text = sys.stdin.read()
        source = "<stdin>"
    else:
        p = Path(args.input)
        if not p.exists():
            print(f"❌ 文件不存在: {args.input}", file=sys.stderr)
            return 1
        text = p.read_text(encoding="utf-8")
        source = str(p)

    report = scan_text(text)

    if args.json:
        out = render_json(report)
    else:
        out = render_markdown(report, source)

    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        print(f"✅ 已写入 {args.output}（{report.score} 分 / {report.level}）")
    else:
        print(out)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))