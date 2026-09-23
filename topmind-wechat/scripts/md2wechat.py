#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md2wechat v2 — Markdown -> WeChat MP inline-style HTML.

Zero dependency (stdlib only). WeChat's rich text editor strips <style> blocks
and class attributes, so every style in the output is inlined.

Supported beyond CommonMark:
  - code syntax highlighting (inline span colors, no <style>)
  - ::: container blocks (note/tip/warn/danger/pull/dialogue/stat)
  - [!badge] inline tags, ==highlight==
  - footnote link mode (external links -> end-of-article index)
  - CJK "pangu" spacing between Han and Latin/digits
  - four heading-2 style variants

Usage:
    python3 md2wechat.py --input 稿.md --out-dir 交付包 --slug foo \
        --asset-root /path/to/repo [--theme theme.json] [--link-mode footnote] \
        [--embed-images]

Outputs:
    <out-dir>/<slug>-公众号版.html   full page, copy body section into WeChat
    <out-dir>/images/*               local image assets
    <out-dir>/diagrams/*             extracted mermaid sources (+ png if rendered)
    <out-dir>/图片上传清单.md         manual upload checklist

--embed-images: 把正文 <img> 的本地路径换成 base64 data URI。
公众号后台拿到相对路径或本地/内网地址时无法取图，粘贴过去图片会整段消失；
base64 内嵌后图片字节随剪贴板一起过去，粘贴即带图。images/ 仍照常导出，
作为「后台显示占位符时手动补传」的兜底。
"""

import argparse
import base64
import html
import json
import os
import re
import shutil
import subprocess
import sys

# ---------------------------------------------------------------- theme

DEFAULT_THEME = {
    "name": "极简黑白灰",
    "accent": "#A6524A",
    "text": "#333333",
    "text_strong": "#1A1A1A",
    "text_muted": "#888888",
    "text_light": "#999999",
    "surface": "#F7F7F7",
    "border": "#E8E8E8",
    "code_bg": "#2C2C2C",
    "code_text": "#E8E8E8",
    "c_note": "#C9C9C9",
    "c_tip": "#5B8C5A",
    "c_warn": "#C08A3E",
    "c_danger": "#B5544C",
    "mark_bg": "#FAF0EE",
    "font_size": "16px",
    "line_height": "1.75",
    "para_gap": "22px",
    # 公众号只认 left / center / right，justify 会被判为非标准值
    "align": "left",
    "h2_style": "bar",
    "img_border": "#F0F0F0",
    "img_radius": "4px",
    "font_stack": (
        "-apple-system,BlinkMacSystemFont,'Helvetica Neue',"
        "'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif"
    ),
    "mono_stack": "Menlo,Monaco,Consolas,'Courier New',monospace",
}

# Material Palenight derived, desaturated to survive on #2C2C2C
HIGHLIGHT = {
    "comment": "#6B7A8F",
    "string": "#C3E88D",
    "number": "#F78C6C",
    "keyword": "#C792EA",
    "builtin": "#FFCB6B",
    "func": "#82AAFF",
    "variable": "#FFCB6B",
    "op": "#89DDFF",
    "key": "#82AAFF",
    "punct": "#89DDFF",
    "flag": "#FFCB6B",
    "tag": "#F07178",
    "attr": "#FFCB6B",
    "add": "#C3E88D",
    "del": "#E58B7F",
    "meta": "#6B7A8F",
}

# ordered rules: earlier patterns win
LANG_RULES = {
    "python": [
        ("comment", r"#[^\n]*"),
        ("string", r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\''),
        ("keyword", r"\b(?:def|class|if|elif|else|for|while|return|import|from|as|try|except|finally|with|lambda|yield|pass|break|continue|in|is|not|and|or|None|True|False|self|async|await|raise|assert|global|del|match|case)\b"),
        ("builtin", r"\b(?:print|len|range|int|str|float|list|dict|set|tuple|open|enumerate|zip|map|filter|sum|min|max|abs|sorted|type|isinstance|super|getattr|setattr|hasattr)\b"),
        ("func", r"\b[A-Za-z_]\w*(?=\s*\()"),
        ("number", r"\b\d+\.?\d*\b"),
        ("op", r"[=+\-*/%<>!&|^~]+"),
    ],
    "js": [
        ("comment", r"//[^\n]*|/\*[\s\S]*?\*/"),
        ("string", r"`(?:\\.|[^`\\])*`|\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'"),
        ("keyword", r"\b(?:const|let|var|function|return|if|else|for|while|class|extends|new|await|async|import|export|from|default|try|catch|finally|throw|typeof|instanceof|this|super|null|undefined|true|false|switch|case|break|continue|delete|in|of|yield|static|get|set)\b"),
        ("builtin", r"\b(?:console|JSON|Math|Object|Array|String|Number|Boolean|Promise|window|document|require|module|exports|process)\b"),
        ("func", r"\b[A-Za-z_$]\w*(?=\s*\()"),
        ("number", r"\b\d+\.?\d*\b"),
        ("op", r"[=+\-*/%<>!&|^~?:]+"),
    ],
    "json": [
        ("key", r'"(?:\\.|[^"\\])*"(?=\s*:)'),
        ("string", r'"(?:\\.|[^"\\])*"'),
        ("keyword", r"\b(?:true|false|null)\b"),
        ("number", r"-?\b\d+\.?\d*(?:[eE][+-]?\d+)?\b"),
        ("punct", r"[{}\[\],:]"),
    ],
    "bash": [
        ("comment", r"#[^\n]*"),
        ("string", r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''),
        ("variable", r"\$\w+|\$\{[^}]*\}"),
        ("keyword", r"\b(?:if|then|else|fi|for|in|do|done|while|case|esac|function|return|export|local|source)\b"),
        ("builtin", r"\b(?:npm|npx|node|python3?|pip3?|git|docker|curl|wget|vercel|mmdc|openssl|mkdir|cp|mv|rm|ls|cat|grep|sed|awk|trash|open|echo|cd|sudo|chmod|kill|ps|top)\b"),
        ("flag", r"(?<=\s)-{1,2}[\w-]+"),
        ("op", r"[|&;<>]+"),
    ],
    "yaml": [
        ("comment", r"#[^\n]*"),
        ("key", r"(?m)^\s*[\w.\-/]+(?=\s*:)"),
        ("string", r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''),
        ("keyword", r"\b(?:true|false|null|yes|no|on|off)\b"),
        ("number", r"\b\d+\.?\d*\b"),
        ("punct", r"[-:]"),
    ],
    "sql": [
        ("comment", r"--[^\n]*"),
        ("string", r"'(?:\\.|[^'\\])*'"),
        ("keyword", r"\b(?:SELECT|FROM|WHERE|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|TABLE|ALTER|DROP|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP|BY|ORDER|LIMIT|OFFSET|AS|AND|OR|NOT|NULL|IS|IN|LIKE|COUNT|SUM|AVG|MAX|MIN|DISTINCT|INDEX|PRIMARY|KEY|DEFAULT|CASCADE|WITH|UNION|HAVING)\b"),
        ("number", r"\b\d+\.?\d*\b"),
        ("op", r"[=<>!*/+\-]+"),
    ],
    "diff": [
        ("meta", r"(?m)^@@[^\n]*|^---[^\n]*|^\+\+\+[^\n]*"),
        ("add", r"(?m)^\+[^\n]*"),
        ("del", r"(?m)^-[^\n]*"),
    ],
    "html": [
        ("comment", r"<!--[\s\S]*?-->"),
        ("string", r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''),
        ("tag", r"</?[A-Za-z][\w:.-]*|/?>"),
        ("attr", r"[\w:.-]+(?=\s*=)"),
        ("punct", r"[=]"),
    ],
    "css": [
        ("comment", r"/\*[\s\S]*?\*/"),
        ("keyword", r"@[\w-]+"),
        ("string", r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''),
        ("key", r"[\w-]+(?=\s*:)"),
        ("number", r"-?\b\d+\.?\d*(?:px|em|rem|%|vh|vw|s|ms)?\b|#[0-9a-fA-F]{3,8}"),
        ("punct", r"[{}\[\],;:]"),
    ],
}

LANG_ALIASES = {
    "javascript": "js", "jsx": "js", "typescript": "js", "ts": "js", "tsx": "js",
    "py": "python", "sh": "bash", "shell": "bash", "zsh": "bash", "console": "bash",
    "yml": "yaml", "xml": "html", "vue": "html", "scss": "css", "less": "css",
    "http": "json", "diff": "diff", "patch": "diff",
}


def highlight(code, lang):
    """Inline-span syntax highlighting (no <style>, no class)."""
    key = LANG_ALIASES.get(lang, lang)
    rules = LANG_RULES.get(key)
    if not rules:
        return html.escape(code, quote=False)
    pattern = re.compile("|".join("(?P<%s>%s)" % (name, pat) for name, pat in rules), re.S)
    out = []
    pos = 0
    for m in pattern.finditer(code):
        if m.start() > pos:
            out.append(html.escape(code[pos:m.start()], quote=False))
        color = HIGHLIGHT.get(m.lastgroup)
        text = html.escape(m.group(), quote=False)
        out.append('<span style="color:%s;">%s</span>' % (color, text) if color else text)
        pos = m.end()
    out.append(html.escape(code[pos:], quote=False))
    return "".join(out)


def load_theme(path):
    theme = dict(DEFAULT_THEME)
    if path:
        with open(path, encoding="utf-8") as fh:
            theme.update(json.load(fh))
    return theme


# ---------------------------------------------------------------- inline

# shared render state, set once per convert() run
CTX = {
    "theme": DEFAULT_THEME,
    "link_mode": "footnote",
    "footnotes": [],
    "use_pangu": True,
}

CODE_TOKEN = "\x00C%d\x00"
HAN = r"\u4e00-\u9fff\u3400-\u4dbf"
PANGU_A = re.compile(r"([%s])([A-Za-z0-9])" % HAN)
PANGU_B = re.compile(r"([A-Za-z0-9])([%s])" % HAN)


def pangu(text):
    text = PANGU_A.sub(r"\1 \2", text)
    text = PANGU_B.sub(r"\1 \2", text)
    return text


def esc(text):
    return html.escape(text, quote=False)


def render_inline(raw):
    """Escape + markdown inline -> HTML with inline styles.

    Reads shared state from CTX so links/footnotes resolve across all
    block types (paragraphs, tables, lists, containers) uniformly.
    """
    theme = CTX["theme"]
    link_mode = CTX["link_mode"]
    footnotes = CTX["footnotes"]
    use_pangu = CTX["use_pangu"]
    spans = []

    def stash(code):
        spans.append(code)
        return CODE_TOKEN % (len(spans) - 1)

    text = esc(raw)
    text = re.sub(r"`([^`]+)`", lambda m: stash(m.group(1)), text)

    if use_pangu:
        text = pangu(text)

    strong = 'font-weight:600;color:%s;' % theme["text_strong"]
    em = 'font-style:normal;color:%s;' % theme["text_muted"]

    # images
    def img_repl(m):
        alt, src = m.group(1), m.group(2)
        caption = ' alt="%s"' % alt if alt else ""
        return ('<img src="%s"%s style="max-width:100%%;height:auto;'
                'border-radius:3px;vertical-align:middle;">') % (src, caption)

    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", img_repl, text)

    # links
    def link_repl(m):
        label, url = m.group(1), m.group(2)
        if link_mode == "footnote" and footnotes is not None:
            if url not in [f["url"] for f in footnotes]:
                footnotes.append({"url": url, "label": label})
            idx = [f["url"] for f in footnotes].index(url) + 1
            return ('%s<sup style="font-size:11px;color:%s;'
                    'padding-left:1px;">[%d]</sup>'
                    % (label, theme["accent"], idx))
        if link_mode == "inline":
            return ('%s<span style="font-size:13px;color:%s;">（%s）</span>'
                    % (label, theme["text_light"], url))
        return ('<span style="font-size:13px;color:%s;word-break:break-all;">'
                '%s（%s）</span>' % (theme["text_light"], label, url))

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link_repl, text)

    # badges: [!文本]
    text = re.sub(
        r"\[!([^\]]+)\]",
        r'<span style="display:inline-block;font-size:11px;line-height:1.5;'
        r'color:' + theme["accent"] + r';background:' + theme["mark_bg"] + r';'
        r'padding:1px 6px;border-radius:3px;margin:0 2px;'
        r'vertical-align:2px;font-weight:500;">\1</span>',
        text,
    )

    # ==highlight== before bold so inner markup still works
    text = re.sub(
        r"==([^=]+)==",
        r'<strong style="font-weight:600;color:' + theme["text_strong"] + r';'
        r'background:' + theme["mark_bg"] + r';padding:1px 3px;'
        r'border-radius:2px;">\1</strong>',
        text,
    )

    text = re.sub(r"\*\*([^*]+)\*\*", r'<strong style="%s">\1</strong>' % strong, text)
    text = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\*)", r'<em style="%s">\1</em>' % em, text)

    for idx, code in enumerate(spans):
        text = text.replace(
            CODE_TOKEN % idx,
            '<code style="background:%s;color:%s;padding:2px 5px;'
            'border-radius:3px;font-size:14px;font-family:%s;word-break:break-all;">%s</code>'
            % (theme["surface"], theme["accent"], theme["mono_stack"], code),
        )
    return text


# ---------------------------------------------------------------- blocks

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE_RE = re.compile(r"^```(\w*)\s*$")
HR_RE = re.compile(r"^(-{3,}|\*{3,}|_{3,})\s*$")
IMG_ONLY_RE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$")
CAPTION_RE = re.compile(r"^\*(.+)\*\s*$")
TABLE_SEP_RE = re.compile(r"^\|?[\s:|-]+\|[\s:|-]*$")
CONTAINER_RE = re.compile(r"^:::+\s*(\w+)?\s*(.*)$")

CN_NUM = "一二三四五六七八九十"


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_list_item(line):
    return bool(re.match(r"^\s*([-*+]|\d+[.)])\s+", line))


def list_meta(line):
    m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
    indent = len(m.group(1).replace("\t", "    ")) // 2
    return indent, m.group(2), m.group(3)


def para_style(theme):
    return ("margin:0 0 %s;line-height:%s;letter-spacing:0.5px;"
            "text-align:%s;word-break:break-word;"
            % (theme["para_gap"], theme["line_height"], theme["align"]))


def render_heading(level, text, theme, index=None):
    t = render_inline(text)
    accent = theme["accent"]
    if level == 1:
        # 正文大标题不用 <h1>：微信对 h1 有「标题」语义映射，粘贴后字号/样式易被
        # 后台覆盖。改用 <p> + 内联样式，等价且稳（20px/700/居中）。
        return ('<p style="font-size:20px;font-weight:700;color:%s;'
                'text-align:center;margin:0 0 18px;line-height:1.5;'
                'letter-spacing:0.5px;">%s</p>' % (theme["text_strong"], t))

    if level == 2:
        style = theme.get("h2_style", "bar")
        # don't double-number headings already written as 一、/ 01
        numbered = bool(re.match(r"^(第?[" + CN_NUM + r"]+[、.．]|\d+[、.．]|\d+\s)", text))
        if style == "number" and index and not numbered:
            t = ('<span style="color:%s;font-weight:700;margin-right:8px;">'
                 '%02d</span>%s' % (accent, index, t))
            return ('<h2 style="font-size:18px;font-weight:700;color:%s;'
                    'margin:34px 0 16px;line-height:1.5;letter-spacing:0.5px;">%s</h2>'
                    % (theme["text_strong"], t))
        if style == "center":
            return ('<h2 style="font-size:18px;font-weight:700;color:%s;'
                    'text-align:center;margin:36px 0 18px;padding:12px 0;'
                    'line-height:1.5;border-top:1px solid %s;'
                    'border-bottom:1px solid %s;letter-spacing:1px;">%s</h2>'
                    % (theme["text_strong"], theme["border"], theme["border"], t))
        if style == "underline":
            return ('<h2 style="font-size:18px;font-weight:700;color:%s;'
                    'margin:34px 0 16px;line-height:1.5;display:inline-block;'
                    'border-bottom:2px solid %s;padding-bottom:4px;">%s</h2>'
                    % (theme["text_strong"], accent, t))
        return ('<h2 style="font-size:18px;font-weight:700;color:%s;'
                'margin:34px 0 16px;padding-left:11px;line-height:1.5;'
                'border-left:4px solid %s;">%s</h2>'
                % (theme["text_strong"], accent, t))

    if level == 3:
        return ('<h3 style="font-size:16px;font-weight:600;color:%s;'
                'margin:26px 0 12px;line-height:1.5;">%s</h3>'
                % (theme["text_strong"], t))
    return ('<h4 style="font-size:15px;font-weight:600;color:%s;'
            'margin:22px 0 10px;line-height:1.5;">%s</h4>' % (theme["text"], t))


def render_code(code, lang, theme):
    body = highlight(code.rstrip("\n"), (lang or "").lower())
    label = ('<div style="font-size:11px;color:#8A8A8A;padding:0 0 8px;'
             'letter-spacing:1px;font-family:%s;">%s</div>'
             % (theme["mono_stack"], esc(lang.upper())) if lang else "")
    # 不用 <pre>：公众号端 pre 不自动换行，窄屏会横向溢出。
    # 改用 section + pre-wrap + break-all，长行自动折行。
    return ('<section style="margin:0 0 %s;background:%s;border-radius:4px;'
            'padding:16px;">%s<section style="margin:0;'
            'white-space:pre-wrap;word-break:break-all;color:%s;font-size:13.5px;'
            'line-height:1.65;font-family:%s;">%s</section></section>'
            % (theme["para_gap"], theme["code_bg"], label,
               theme["code_text"], theme["mono_stack"], body))


def render_quote(lines, theme):
    inner = []
    buf = []
    for line in lines:
        if not line.strip():
            if buf:
                inner.append(render_paragraph(" ".join(buf), theme, tight=True))
                buf = []
            continue
        buf.append(line.strip())
    if buf:
        inner.append(render_paragraph(" ".join(buf), theme, tight=True))
    return ('<blockquote style="margin:0 0 %s;padding:14px 16px;'
            'background:%s;border-left:3px solid %s;border-radius:2px;'
            'color:#666666;font-size:15px;line-height:1.7;">%s</blockquote>'
            % (theme["para_gap"], theme["surface"], theme["accent"], "".join(inner)))


def render_paragraph(text, theme, tight=False, align=None):
    style = para_style(theme)
    if tight:
        style = style.replace("margin:0 0 %s;" % theme["para_gap"], "margin:0 0 10px;")
    if align:
        style += "text-align:%s;" % align
    return '<p style="%s">%s</p>' % (style, render_inline(text))


def render_list(items, theme, ordered, depth=0):
    tag = "ol" if ordered else "ul"
    style = ("margin:0 0 20px;padding-left:%dpx;line-height:%s;"
             % (26 if depth == 0 else 22, theme["line_height"]))
    if ordered:
        style += "list-style-type:decimal;"
    else:
        style += "list-style-type:disc;color:%s;" % theme["accent"]
    out = ["<%s style=\"%s\">" % (tag, style)]
    for item in items:
        line = '<li style="margin-bottom:9px;color:%s;">' % theme["text"]
        line += '<span style="color:%s;">%s</span>' % (theme["text"], item["text"])
        if item["children"]:
            line += render_list(item["children"], theme,
                                bool(item["children_ordered"]), depth + 1)
        line += "</li>"
        out.append(line)
    out.append("</%s>" % tag)
    return "".join(out)


def build_list(lines, theme, start=0):
    items = []
    root = {"indent": -1, "children": items, "ordered": False, "children_ordered": None}
    stack = [root]
    i = start
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            if i + 1 < len(lines) and is_list_item(lines[i + 1]):
                i += 1
                continue
            break
        if not is_list_item(line):
            if line.startswith("    ") or line.startswith("\t"):
                if items:
                    items[-1]["text"] += " " + line.strip()
                i += 1
                continue
            break
        indent, marker, content = list_meta(line)
        node = {
            "text": render_inline(content),
            "children": [],
            "children_ordered": None,
            "indent": indent,
            "ordered": not marker.startswith(("-", "*", "+")),
        }
        while stack and stack[-1]["indent"] >= indent:
            stack.pop()
        if not stack:
            stack = [root]
        parent = stack[-1]
        if parent["children_ordered"] is None:
            parent["children_ordered"] = node["ordered"]
        parent["children"].append(node)
        stack.append(node)
        i += 1

    ordered = bool(re.match(r"^\s*(\d+[.)])\s+", lines[start]))
    return render_list(items, theme, ordered), i


def render_table(rows, theme):
    head, body = rows[0], rows[1:]
    th = "".join(
        '<th style="background:%s;border:1px solid %s;padding:10px 12px;'
        'text-align:left;font-weight:600;color:%s;font-size:14px;'
        'word-break:break-word;">%s</th>' % (theme["surface"], theme["border"],
                                            theme["text_strong"], render_inline(c))
        for c in head
    )
    trs = "".join(
        "<tr>%s</tr>" % "".join(
            '<td style="border:1px solid %s;padding:10px 12px;color:%s;'
            'font-size:14px;line-height:1.6;">%s</td>'
            % (theme["border"], theme["text"], render_inline(c))
            for c in row
        )
        for row in body
    )
    return ('<section style="margin:0 0 %s;">'
            '<table style="border-collapse:collapse;width:100%%;font-size:14px;'
            'table-layout:fixed;">'
            '<thead><tr>%s</tr></thead><tbody>%s</tbody></table></section>'
            % (theme["para_gap"], th, trs))


def render_hr(theme):
    # 宽度用百分比：公众号端 px 固定值在不同屏宽下表现不一致
    return ('<p style="text-align:center;margin:32px 0;">'
            '<span style="display:inline-block;width:12%%;height:2px;'
            'background:%s;"></span></p>' % theme["accent"])


def render_figure(src, caption, theme):
    cap = ""
    if caption:
        cap = ('<p style="font-size:13px;color:%s;text-align:center;'
               'margin:9px 0 %s;line-height:1.6;">%s</p>'
               % (theme["text_light"], theme["para_gap"], render_inline(caption)))
    border = ("border:1px solid %s;" % theme["img_border"]
              if theme.get("img_border") else "")
    # 不用 <figure>：微信对 figure 的兼容不可靠（粘贴时可能剥离包裹导致图注错位）。
    # 改用 <section> 包「居中图片 <p> + 独立图注 <p>」，微信 100% 兼容，且避免 <p> 嵌套。
    return ('<section style="margin:0 0 %s;">'
            '<p style="margin:0;text-align:center;">'
            '<img src="%s" style="width:100%%;display:block;%s'
            'border-radius:%s;margin:0 auto;"></p>%s</section>'
            % ("9px" if caption else theme["para_gap"], src, border,
               theme["img_radius"], cap))


# ---------------------------------------------------------------- containers

CONTAINER_KINDS = {
    "note": "note", "info": "note", "memo": "note",
    "tip": "tip", "success": "tip", "ok": "tip",
    "warn": "warn", "warning": "warn",
    "danger": "danger", "error": "danger",
    "pull": "pull", "quote": "pull", "golden": "pull",
    "dialogue": "dialogue", "chat": "dialogue", "talk": "dialogue",
    "stat": "stat", "data": "stat", "metric": "stat",
}

DEFAULT_LABELS = {
    "note": "说明", "tip": "提示", "warn": "注意", "danger": "警告",
}


def render_container(kind, label, inner_lines, theme):
    kind = CONTAINER_KINDS.get(kind, "note")
    text = "\n".join(inner_lines)

    if kind == "pull":
        body = render_paragraph(text.strip(), theme, align="center")
        return ('<section style="margin:28px 0;padding:18px 10px;'
                'border-top:1px solid %s;border-bottom:1px solid %s;">'
                '<div style="font-size:17px;line-height:1.85;color:%s;'
                'font-weight:600;letter-spacing:0.5px;">%s</div></section>'
                % (theme["border"], theme["border"], theme["text_strong"],
                   render_inline(text.strip())))

    if kind == "dialogue":
        rows = []
        for line in inner_lines:
            if not line.strip():
                continue
            m = re.match(r"^\s*(.{1,12}?)\s*[:：]\s*(.+)$", line)
            if m:
                name, say = m.group(1), m.group(2)
                rows.append(
                    '<p style="margin:0 0 6px;font-size:13px;color:%s;">%s</p>'
                    '<p style="margin:0 0 14px;padding:11px 14px;background:%s;'
                    'border-radius:8px;font-size:15px;line-height:1.72;'
                    'color:%s;">%s</p>'
                    % (theme["text_light"], render_inline(name),
                       theme["surface"], theme["text"], render_inline(say)))
            else:
                rows.append('<p style="margin:0 0 14px;padding:11px 14px;'
                            'background:%s;border-radius:8px;font-size:15px;'
                            'line-height:1.72;color:%s;">%s</p>'
                            % (theme["surface"], theme["text"],
                               render_inline(line.strip())))
        return '<section style="margin:0 0 %s;">%s</section>' % (
            theme["para_gap"], "".join(rows))

    if kind == "stat":
        rows = []
        for line in inner_lines:
            if not line.strip() or "|" not in line:
                continue
            value, desc = line.split("|", 1)
            rows.append(
                '<p style="margin:0 0 14px;line-height:1.3;">'
                '<span style="font-size:26px;font-weight:700;color:%s;'
                'margin-right:10px;">%s</span>'
                '<span style="font-size:13px;color:%s;">%s</span></p>'
                % (theme["accent"], esc(value.strip()),
                   theme["text_light"], esc(desc.strip())))
        return '<section style="margin:0 0 %s;padding:16px 18px;' \
               'background:%s;border-radius:6px;">%s</section>' % (
                   theme["para_gap"], theme["surface"], "".join(rows))

    color = {"note": theme["c_note"], "tip": theme["c_tip"],
             "warn": theme["c_warn"], "danger": theme["c_danger"]}[kind]
    label_html = ""
    if label:
        label_html = ('<div style="font-size:12px;font-weight:600;color:%s;'
                      'letter-spacing:1px;margin-bottom:6px;">%s</div>'
                      % (color, esc(label)))
    body = []
    buf = []
    for line in inner_lines:
        if not line.strip():
            if buf:
                body.append(render_paragraph(" ".join(buf), theme, tight=True))
                buf = []
            continue
        buf.append(line.strip())
    if buf:
        body.append(render_paragraph(" ".join(buf), theme, tight=True))
    return ('<section style="margin:0 0 %s;padding:14px 16px;background:%s;'
            'border-left:3px solid %s;border-radius:2px;">%s%s</section>'
            % (theme["para_gap"], theme["surface"], color, label_html, "".join(body)))


# ---------------------------------------------------------------- images

def resolve_image(src, md_path, out_dir, assets, asset_root):
    if re.match(r"^https?://", src):
        assets.append({"src": src, "local": None, "remote": True})
        return src
    abs_path = os.path.normpath(os.path.join(os.path.dirname(md_path), src))
    if not os.path.exists(abs_path) and asset_root:
        rel = re.sub(r"^(\.\./)+", "", src)
        candidate = os.path.normpath(os.path.join(asset_root, rel))
        if os.path.exists(candidate):
            abs_path = candidate
    if not os.path.exists(abs_path):
        return src
    img_dir = os.path.join(out_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    base = os.path.basename(abs_path)
    target = os.path.join(img_dir, base)
    n = 1
    while os.path.exists(target) and not os.path.samefile(abs_path, target):
        stem, ext = os.path.splitext(base)
        target = os.path.join(img_dir, "%s-%d%s" % (stem, n, ext))
        n += 1
    if not os.path.exists(target):
        shutil.copy2(abs_path, target)
    rel = os.path.relpath(target, out_dir)
    assets.append({"src": src, "local": rel, "remote": False,
                   "basename": os.path.basename(target),
                   "size": os.path.getsize(abs_path)})
    return rel


def handle_mermaid(code, out_dir, diagrams, theme, render):
    os.makedirs(os.path.join(out_dir, "diagrams"), exist_ok=True)
    idx = len(diagrams) + 1
    mmd = os.path.join(out_dir, "diagrams", "diagram-%02d.mmd" % idx)
    with open(mmd, "w", encoding="utf-8") as fh:
        fh.write(code)
    png = os.path.join(out_dir, "diagrams", "diagram-%02d.png" % idx)
    rel_png = os.path.relpath(png, out_dir)
    ok = False
    if render and shutil.which("mmdc"):
        try:
            subprocess.run(
                ["mmdc", "-i", mmd, "-o", png, "-b", "white", "-w", "1080"],
                check=True, capture_output=True, timeout=180,
            )
            ok = os.path.exists(png)
        except Exception:
            ok = False
    diagrams.append({"index": idx, "mmd": os.path.relpath(mmd, out_dir),
                     "png": rel_png if ok else None})
    if ok:
        return render_figure(rel_png, None, theme)
    note = ("［此处为流程图 %02d，公众号不支持 mermaid。请渲染 diagrams/%s 为图片后手动插入］"
            % (idx, os.path.basename(mmd)))
    return ('<section style="margin:0 0 %s;padding:14px 16px;'
            'background:%s;border-left:3px solid %s;color:#777;'
            'font-size:14px;line-height:1.7;border-radius:2px;">%s</section>'
            % (theme["para_gap"], theme["surface"], theme["accent"], esc(note)))


# ---------------------------------------------------------------- parser

def strip_frontmatter(lines):
    if lines and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                return lines[idx + 1:]
    return lines


def convert_blocks(lines, md_path, out_dir, theme, ctx):
    out = []
    i = 0
    n = len(lines)
    h2_index = 0

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        m = FENCE_RE.match(stripped)
        if m:
            lang = m.group(1)
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            code = "\n".join(buf)
            if lang.lower() == "mermaid":
                out.append(handle_mermaid(code, out_dir, ctx["diagrams"], theme,
                                          ctx["render_mermaid"]))
            else:
                out.append(render_code(code, lang, theme))
            continue

        if HR_RE.match(stripped) and not is_list_item(line):
            out.append(render_hr(theme))
            i += 1
            continue

        m = HEADING_RE.match(stripped)
        if m:
            level = len(m.group(1))
            if level == 2:
                h2_index += 1
            out.append(render_heading(level, m.group(2).strip(), theme, h2_index))
            i += 1
            continue

        m = CONTAINER_RE.match(stripped)
        if m:
            kind = (m.group(1) or "note").lower()
            label = m.group(2).strip()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith(":::"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append(render_container(kind, label or DEFAULT_LABELS.get(
                CONTAINER_KINDS.get(kind, "note"), ""), buf, theme))
            continue

        if stripped.startswith("|") and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1].strip()):
            rows = [split_row(stripped)]
            i += 2
            while i < n and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i].strip()))
                i += 1
            out.append(render_table(rows, theme))
            continue

        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(render_quote(buf, theme))
            continue

        if is_list_item(line):
            block_html, i = build_list(lines, theme, i)
            out.append(block_html)
            continue

        m = IMG_ONLY_RE.match(stripped)
        if m:
            caption = None
            if i + 1 < n:
                cm = CAPTION_RE.match(lines[i + 1].strip())
                if cm:
                    caption = cm.group(1)
                    i += 1
            src = resolve_image(m.group(2), md_path, out_dir,
                                ctx["assets"], ctx["asset_root"])
            out.append(render_figure(src, caption, theme))
            i += 1
            continue

        buf = [stripped]
        i += 1
        while i < n:
            cur = lines[i].strip()
            if (not cur or HEADING_RE.match(cur) or HR_RE.match(cur)
                    or CONTAINER_RE.match(cur) or cur.startswith(">")
                    or cur.startswith("|") or is_list_item(lines[i])
                    or IMG_ONLY_RE.match(cur) or FENCE_RE.match(cur)):
                break
            buf.append(cur)
            i += 1
        out.append(render_paragraph(" ".join(buf), theme))

    return "".join(out)


def convert(md_text, md_path, out_dir, theme, link_mode="footnote",
            render_mermaid=False, asset_root=None, use_pangu=True):
    ctx = {"assets": [], "diagrams": [], "footnotes": [],
           "render_mermaid": render_mermaid, "asset_root": asset_root}
    CTX["theme"] = theme
    CTX["link_mode"] = link_mode
    CTX["footnotes"] = ctx["footnotes"]
    CTX["use_pangu"] = use_pangu
    lines = strip_frontmatter(md_text.split("\n"))
    body = convert_blocks(lines, md_path, out_dir, theme, ctx)

    if link_mode == "footnote" and ctx["footnotes"]:
        body += render_footnotes(ctx["footnotes"], theme)
    return body, ctx["assets"], ctx["diagrams"], ctx["footnotes"]


def render_footnotes(footnotes, theme):
    items = "".join(
        '<p style="margin:0 0 8px;font-size:13px;line-height:1.7;color:%s;'
        'word-break:break-all;">[%d] %s — %s</p>'
        % (theme["text_muted"], idx, esc(f["label"]), esc(f["url"]))
        for idx, f in enumerate(footnotes, 1)
    )
    return ('<section style="margin:34px 0 %s;padding:16px 18px;'
            'background:%s;border-radius:6px;">'
            '<div style="font-size:13px;font-weight:600;color:%s;'
            'letter-spacing:1px;margin-bottom:10px;">参考链接</div>%s</section>'
            % (theme["para_gap"], theme["surface"], theme["text_strong"], items))


# ---------------------------------------------------------------- embed

MIME_BY_EXT = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}


def embed_images_inline(body, out_dir):
    """把正文里指向本地文件的 <img src> 换成 base64 data URI。

    公众号后台会丢相对路径与本地地址：粘贴过去的 <img> 没有可抓取的 URL，
    整张图直接消失（连占位符都没有）。内嵌成 data URI 后，图片字节跟着
    剪贴板一起过去。远程 http(s) 图与已经是 data: 的图不动。
    返回 (新正文, 统计)。
    """
    stats = {"count": 0, "bytes": 0, "skipped": []}

    def repl(m):
        src = m.group(1)
        if re.match(r"^(https?:|data:|//)", src):
            return m.group(0)
        path = os.path.normpath(os.path.join(out_dir, src))
        mime = MIME_BY_EXT.get(os.path.splitext(path)[1].lower())
        if not mime or not os.path.exists(path):
            stats["skipped"].append(src)
            return m.group(0)
        with open(path, "rb") as fh:
            raw = fh.read()
        stats["count"] += 1
        stats["bytes"] += len(raw)
        return 'src="data:%s;base64,%s"' % (
            mime, base64.b64encode(raw).decode("ascii"))

    return re.sub(r'src="([^"]+)"', repl, body), stats


# ---------------------------------------------------------------- page

PAGE_TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
/* 仅本地预览用：公众号会剥离 style 标签，正文内联样式保持百分比宽度 */
body>div,body>article{{max-width:677px!important;margin-left:auto!important;
margin-right:auto!important;box-sizing:border-box;}}
</style>
</head>
<body style="margin:0;padding:24px 12px 64px;background:#EDEDED;font-family:{font_stack};">

<div style="max-width:100%;margin:0 auto 18px;padding:13px 18px;background:#FFF8E6;
border:1px solid #F0D9A8;border-radius:8px;font-size:13px;line-height:1.7;color:#7A5C1E;">
{notice}
</div>

<div style="max-width:100%;margin:0 auto 14px;display:flex;align-items:center;gap:10px;
flex-wrap:wrap;">
<button onclick="copyBody()" style="padding:9px 20px;font-size:14px;color:#fff;
background:{accent};border:none;border-radius:6px;cursor:pointer;">复制正文</button>
<span id="wx-tip" style="font-size:13px;color:#4A7A3A;"></span>
<span style="margin-left:auto;font-size:12px;color:#888;">{title}</span>
</div>

<div style="max-width:100%;margin:0 auto;padding:0 0 8px;font-size:12px;
color:#999;text-align:center;">↓ 正文开始 ↓</div>

<article id="wx-body" style="max-width:100%;margin:0 auto;padding:26px 20px 32px;
background:#FFFFFF;border:1px dashed #C9C9C9;border-radius:8px;
font-size:{font_size};color:{text};line-height:{line_height};
font-family:{font_stack};">
{body}
</article>

<script>
function copyBody() {{
  var node = document.getElementById('wx-body');
  var sel = window.getSelection();
  var range = document.createRange();
  range.selectNodeContents(node);
  sel.removeAllRanges();
  sel.addRange(range);
  try {{
    document.execCommand('copy');
    document.getElementById('wx-tip').textContent = '已复制，去公众号后台粘贴';
  }} catch (e) {{
    document.getElementById('wx-tip').textContent = '复制失败，请手动全选';
  }}
  sel.removeAllRanges();
}}
</script>
</body>
</html>
"""


def build_notice(embedded, n_images):
    """页顶「发布前须知」文案。内嵌模式与手动上传模式的说明不同。"""
    code = ('<code style="background:#F5F5F5;padding:1px 4px;border-radius:3px;">%s</code>')
    head = ("<strong>发布前须知</strong>：上方为操作提示，<strong>不要一起复制</strong>。"
            "请点「复制正文」或全选下方虚线框内容，粘贴到公众号后台编辑器。")
    if embedded:
        tail = ("<br>本页 %d 张图已 base64 内嵌，粘贴时会跟着一起过去，正常情况下"
                "无需再手动插图。若后台某张图显示为占位符，按 %s 的顺序，"
                "从 %s 手动补传这一张。"
                % (n_images, code % "图片上传清单.md", code % "images/"))
    else:
        tail = ("<br>图片需手动上传：本页图片仅供本地预览 —— 按 %s 的顺序"
                "逐张插入素材库。" % (code % "图片上传清单.md"))
    return head + tail


def audit_inline(body):
    """正文内联样式的平台合规自检。

    对应公众号格式检测会告警的问题：对齐非标准值、px 固定宽度、
    pre 标签不换行、flex/grid/float/position 等公众号会吞掉的布局属性，
    以及 <h1>/<figure> 等微信兼容不稳定的标签。
    返回去重后的告警列表，空列表即通过。
    """
    issues = []

    # 标签级：微信对 h1（标题语义映射）/ figure（图片包裹）/ pre（不换行）兼容不稳
    if "<h1" in body:
        issues.append("使用了 <h1> 标签（微信会按标题语义覆盖样式，正文标题应用 <p>）")
    if "<figure" in body:
        issues.append("使用了 <figure> 标签（微信粘贴可能剥离包裹，图片用 <section>+<p>）")
    if "<pre" in body:
        issues.append("使用了 <pre> 标签（移动端不换行，会横向溢出）")

    # 属性级：公众号会吞掉或导致排错的布局属性
    BLOCKLIST = {
        "display": ("flex", "grid"),
        "float": (),
        "position": (),
        "flex": (),
        "grid": (),
    }
    for m in re.finditer(r'style="([^"]*)"', body):
        for decl in m.group(1).split(";"):
            decl = decl.strip()
            if not decl:
                continue
            prop, _, val = decl.partition(":")
            prop, val = prop.strip(), val.strip()
            if prop == "text-align" and val not in ("left", "center", "right"):
                issues.append("text-align:%s 非标准值（改 left/center/right）" % val)
            elif re.fullmatch(r"(max-|min-)?width", prop) and "px" in val:
                issues.append("%s:%s 固定像素宽度（改百分比）" % (prop, val))
            elif prop == "white-space" and val in ("pre", "nowrap"):
                issues.append("white-space:%s 不换行（窄屏溢出）" % val)
            elif prop in BLOCKLIST:
                bad = BLOCKLIST[prop]
                if not bad or any(b in val for b in bad):
                    issues.append("%s:%s 布局属性（公众号可能吞掉或排错）" % (prop, val))
            elif prop.startswith("-"):
                issues.append("%s 私有属性（公众号可能不支持）" % prop)
    seen, out = set(), []
    for item in issues:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def write_manifest(out_dir, slug, title, assets, diagrams, theme, footnotes,
                   embedded=False):
    lines = ["# 图片上传清单 · %s" % title, ""]
    if embedded:
        lines.append("> 本页图片已 base64 内嵌，正常情况下粘贴到后台即带图。"
                     "若有图显示为占位符，再按此顺序逐张上传到素材库替换。")
    else:
        lines.append("> 公众号不会抓取本地图片，请在后台编辑器按此顺序逐张上传到素材库并插入正文。")
    lines.append("")
    if assets:
        lines.append("## 正文图片（按出现顺序）")
        lines.append("")
        lines.append("| 序号 | 文件名 | 体积 | 原 Markdown 引用 |")
        lines.append("|---|---|---|---|")
        for idx, a in enumerate(assets, 1):
            size = ""
            if a.get("size"):
                kb = a["size"] / 1024
                size = "%.0f KB" % kb if kb < 1024 else "%.1f MB" % (kb / 1024)
            if a.get("remote"):
                lines.append("| %d | %s（远程） | %s | `%s` |" % (idx, a["src"], size, a["src"]))
            else:
                lines.append("| %d | `%s` | %s | `%s` |"
                             % (idx, a.get("basename", ""), size, a["src"]))
        lines.append("")
        lines.append("图片目录：`images/`（公众号单图建议 < 2 MB，宽度 1080 px 左右）")
        lines.append("")
    else:
        lines.append("## 正文图片")
        lines.append("")
        lines.append("_无_")
        lines.append("")
    lines.append("## 图表（mermaid）")
    lines.append("")
    if diagrams:
        lines.append("| 序号 | 源文件 | 已渲染 PNG |")
        lines.append("|---|---|---|")
        for d in diagrams:
            lines.append("| %d | `%s` | %s |" % (d["index"], d["mmd"],
                                                 ("`%s`" % d["png"]) if d["png"] else "未渲染"))
        lines.append("")
        lines.append("渲染：`mmdc -i diagrams/xx.mmd -o diagrams/xx.png -b white -w 1080`")
    else:
        lines.append("_无_")
    if footnotes:
        lines.append("")
        lines.append("## 参考链接（正文上标序号对应）")
        lines.append("")
        for idx, f in enumerate(footnotes, 1):
            lines.append("%d. %s — %s" % (idx, f["label"], f["url"]))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("主题：%s · 点缀色 `%s` · 标题样式 `%s`"
                 % (theme["name"], theme["accent"], theme.get("h2_style", "bar")))
    path = os.path.join(out_dir, "图片上传清单.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return path


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--theme", default="")
    ap.add_argument("--link-mode", default="footnote",
                    choices=["footnote", "note", "inline"])
    ap.add_argument("--asset-root", default="",
                    help="源仓库根目录，用于解析稿中 ../assets/ 形式的图片路径")
    ap.add_argument("--no-pangu", action="store_true", help="关闭中英文自动加空格")
    ap.add_argument("--render-mermaid", action="store_true")
    ap.add_argument("--embed-images", action="store_true",
                    help="把正文图片转成 base64 内嵌，粘贴到公众号时带图（推荐）")
    args = ap.parse_args()

    theme = load_theme(args.theme)
    with open(args.input, encoding="utf-8") as fh:
        md_text = fh.read()

    os.makedirs(args.out_dir, exist_ok=True)
    body, assets, diagrams, footnotes = convert(
        md_text, os.path.abspath(args.input), args.out_dir, theme,
        args.link_mode, args.render_mermaid, args.asset_root or None,
        not args.no_pangu,
    )

    title = args.title
    if not title and md_text.startswith("---"):
        end = md_text.find("\n---", 3)
        fm = md_text[3:end] if end > 0 else ""
        m = re.search(r"^title:\s*(.+)$", fm, re.M)
        if m:
            title = m.group(1).strip().strip("\"'")
    if not title:
        for line in md_text.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break
    title = title or args.slug

    embed_stats = None
    if args.embed_images:
        body, embed_stats = embed_images_inline(body, args.out_dir)

    page = PAGE_TPL.format(
        title=esc(title), body=body, accent=theme["accent"],
        text=theme["text"], font_size=theme["font_size"],
        line_height=theme["line_height"], font_stack=theme["font_stack"],
        notice=build_notice(embed_stats is not None,
                            embed_stats["count"] if embed_stats else len(assets)),
    )
    html_path = os.path.join(args.out_dir, "%s-公众号版.html" % args.slug)
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(page)

    manifest = write_manifest(args.out_dir, args.slug, title, assets, diagrams,
                              theme, footnotes, embed_stats is not None)

    plain = re.sub(r"<[^>]+>", "", body)
    print("HTML     : %s" % html_path)
    audit = audit_inline(body)
    if audit:
        print("合规自检 : ✗ %d 项告警（公众号格式检测会报）" % len(audit))
        for item in audit[:10]:
            print("   - %s" % item)
    else:
        print("合规自检 : ✓ 无告警（对齐/宽度/代码块）")
    print("清单     : %s" % manifest)
    if embed_stats:
        print("图片内嵌 : ✓ %d 张 / %.0f KB（base64 后约 %.1f MB）"
              % (embed_stats["count"], embed_stats["bytes"] / 1024,
                 embed_stats["bytes"] * 4 / 3 / 1024 / 1024))
        if embed_stats["skipped"]:
            print("           未内嵌：%s" % "、".join(embed_stats["skipped"]))
    print("主题     : %s / 标题样式 %s" % (theme["name"], theme.get("h2_style", "bar")))
    print("图片     : %d 张（%d 远程）" % (len(assets), sum(1 for a in assets if a.get("remote"))))
    print("图表     : %d 个 mermaid" % len(diagrams))
    print("脚注     : %d 条" % len(footnotes))
    print("正文字数 : %d" % len(plain))


if __name__ == "__main__":
    sys.exit(main())
