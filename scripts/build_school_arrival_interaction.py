from __future__ import annotations

import html
import json
from pathlib import Path

from build_act1_colored_transcript import TEMPLATE, inline_text


ROOT = Path(__file__).resolve().parent.parent
BASE = '末日学校-抵达后互动-第一顿饭-20260930-v1'
ROLES = [('q', 'G', '#087268'), ('o', 'N1', '#98500a'),
         ('a', 'N2', '#285dcc'), ('x', 'N3', '#7b48a8'),
         ('d', 'N4', '#af3769')]
KEYS = {name: key for key, name, _ in ROLES}


def main() -> None:
    scenes = json.loads((ROOT / 'drafts' / (BASE + '.json')).read_text(encoding='utf-8'))
    cards, sections, nav, markdown = [], [], [], []
    number = 0
    markdown.append('# 末日学校 · 抵达后互动 · 第一顿饭\n\n'
                    '原创排练稿，预计 36 分钟。只有 G 和 N1 至 N4 主导流程。'
                    'I 编号为本稿互动条目编号，不是参考作品段落号。'
                    '玩家入口和接法描述可发生的回应，不规定玩家必须说出的台词。\n')
    for index, scene in enumerate(scenes, 1):
        entries = []
        start = number + 1
        markdown.append(f"## {index}. {scene['title']}\n\n{scene['subtitle']}\n")
        for who, label, text in scene['rows']:
            number += 1
            key = KEYS.get(who)
            is_note = key is None
            badge = (f'<span class="badge badge-{key}">{who}</span>' if key else
                     f'<span class="kind">{html.escape(label or "动作 / 流程")}</span>')
            if who == 'branch':
                badge += '<span class="kind">非标准回答接法</span>'
            content = inline_text(text, key)
            entries.append(f'<article class="entry {"stage" if is_note else "spoken"}" '
                           f'id="i{number}" data-speakers="{key or ""}">'
                           f'<div class="entry-meta"><a class="pid" href="#i{number}">I{number:03d}</a>'
                           f'<div class="badges">{badge}</div></div>'
                           f'<div class="source">{content}</div></article>')
            markdown.append(f"**I{number:03d} · {who if key else label}**\n\n{text}\n")
            cards.append({'index': number, 'who': who, 'text': text})
        sections.append(f'<section class="scene" id="scene-{index}"><div class="scene-heading">'
                        f'<span class="scene-number">{index:02d}</span><div><h2>{scene["title"]}</h2>'
                        f'<p>{scene["subtitle"]}<span class="range">I{start:03d}–I{number:03d}</span>'
                        '</p></div></div><div class="entries">' + ''.join(entries) + '</div></section>')
        nav.append(f'<a href="#scene-{index}"><span>{index:02d}</span>{scene["title"]}</a>')
    colors = '\n'.join(f'.voice-{key}{{color:{color}}}.badge-{key},.role[data-role="{key}"]'
                       f'{{--role:{color};color:{color}}}' for key, _, color in ROLES)
    buttons = '<button class="role active" data-role="all" aria-pressed="true">全部人物</button>'
    buttons += ''.join(f'<button class="role" data-role="{key}" aria-pressed="false">{name}</button>'
                       for key, name, _ in ROLES)
    legend = ''.join(f'<span class="legend-item" style="--role:{color}"><i></i>{name}</span>'
                     for _, name, color in ROLES)
    page = TEMPLATE.replace('__COLORS__', colors).replace('__BUTTONS__', buttons)
    page = page.replace('__LEGEND__', legend).replace('__NAV__', ''.join(nav))
    page = page.replace('__SECTIONS__', ''.join(sections)).replace('316', str(number))
    page = page.replace('<title>流氓叙事 · 第一幕互动原文</title>', '<title>末日学校 · 第一顿饭 · 抵达后互动</title>')
    page = page.replace('原文阅读 · 第一幕', '原创互动 · 抵达学校')
    page = page.replace('读本结束以后，谁接住了谁。', '第一顿饭，先别急着走。')
    page = page.replace('《流氓叙事》主持人手册的第一幕公共互动。沿着原文顺序阅读，人物台词分色，动作与流程显示为灰色。正文保留原有文字、空格与标注。',
                        '四对来客循广播抵达学校。G 和 N1—N4 带着大家进门、分食、约上课，再录下第一天。台词分色，动作、玩家入口与接法显示为灰色。')
    page = page.replace('段原文</span><span>P0774 — P1089</span><span>11 个阅读段落</span><span>含剧情剧透',
                        '条互动</span><span>6 个环节</span><span>预计 36 分钟</span><span>4 玩家 + 5 演员')
    page = page.replace('搜索台词、人物或段落编号', '搜索台词、人物或互动编号')
    page = page.replace('搜索原文', '搜索互动').replace('显示舞台与流程说明', '显示动作与玩家接法')
    page = page.replace('点人物可突出其话语，其他段落仍保留上下文。玩家的自由回答在手册中多为动作提示，未补写台词。灰色的可选提问保留原文指定的多个提问人。',
                        '点人物可突出其话语，保留其他内容作上下文。只为五位演员写台词；玩家可以回应、拒绝或沉默。灰色说明提供进入方式与演员接法。')
    page = page.replace('四组测试现场顺序随机；页面按手册原文排列。章节标题与人物标签为阅读辅助，不属于原文。',
                        'I 为本稿互动条目编号。全程同一教室，不增加幕后声音演员。时长为设计估计，仍需排练。')
    old_footer = '来源 · 流氓叙事手册.docx / word/document.xml 非空段落 P0774–P1089。编号不是 Word 页码。<br>原始文件未改动。人物分色与阅读标题由整理添加。<a href="流氓叙事-第一幕读本后互动原文-20260930-v1.md">查看对应 Markdown 原文</a>。'
    page = page.replace(old_footer, f'原创提案 · 2026-09-30。根据用户末日学校大纲创作。<br>'
                        f'<a href="{BASE}.md">查看 Markdown 排练稿</a> · '
                        '<a href="../analysis/末日学校-抵达后互动设计说明-20260930-v1.md">查看设计说明与玩家覆盖表</a>。')
    director = '''<details class="director"><summary>排练前说明 · 局部设定、时间与拍摄</summary>
<p>六段时长分别为 4、7、5、6、8、6 分钟，共约 36 分钟。这是抵达后的开场公共戏，不是全本。玩家无须答应长住、原谅或表白。</p>
<p>G 掌食物密码并渴望同学。N1 嘴硬、先做事；N2 是成年妹妹，黏哥哥也有生活能力；N3 以 P3 指令为主，本幕尚未懂爱；N4 保留少量旧轮回日常片段，P4 只有梦境或熟悉感。新增片段为本轮提案，不自动确认为全本最终规则。</p>
<p>座位段并行交流，G 逐桌加入。G 拍摄四桌，N2 只在轮到 G 入镜时接手机；没有额外工作人员。录像使用实际回应，拒绝入镜可拍物件或跳过。</p>
<p>共九只碗、九个座位、可分的饼、热水、旧布、纸笔、粉笔、收音机与一部手机。演员提示不作为 NPC 必须念出的旁白。末尾保留约明天的快乐，不添加灾难预告。</p></details>'''
    page = page.replace('<main><div id="empty"', '<main>' + director + '<div id="empty"')
    page = page.replace('</style>', '.director{background:#fff;border:1px solid #dce6e1;border-radius:8px;padding:16px 20px;margin-bottom:28px;font-size:13px;line-height:1.9;color:#65726b}.director summary{cursor:pointer;font-weight:600;color:#35736a}.director p{margin:12px 0 0}@media print{.director{display:none}}\n</style>')
    assert '流氓叙事' not in page and 'P0774' not in page
    for suffix, content in [('.html', page), ('.md', '\n'.join(markdown))]:
        output = ROOT / 'drafts' / (BASE + suffix)
        output.write_text(content, encoding='utf-8')
    (ROOT / 'qa/末日学校-抵达互动条目-20260930-v1.json').write_text(
        json.dumps(cards, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(ROOT / 'drafts' / (BASE + '.html')),
                      'entries': number, 'scenes': len(scenes)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
