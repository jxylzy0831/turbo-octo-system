from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / '分析/流氓叙事-第一幕互动原文-人物分色-20260930-第1版.html'
ROLES = [('q', '羌青瓷', '#087268'), ('o', '奥丁', '#98500a'),
         ('a', '阿奇', '#285dcc'), ('x', '肖须言', '#7b48a8'),
         ('d', '黛利拉', '#af3769'), ('y', '以撒', '#557517'),
         ('m', '缪宏谟', '#236d86'), ('j', '蒋伯驾', '#a13f31'),
         ('c', '程聿怀', '#5155a0'), ('l', '程走柳', '#825d32')]
NAMES = {key: name for key, name, _ in ROLES}
SECTIONS = [(774, 791, '开业与审问', '羌青瓷邀请众人追问来意'),
            (792, 828, '奥丁救场', '从阵营冲突进入世界背景'),
            (829, 919, '关系式自我介绍', '八人介绍，穿插第一通电话'),
            (920, 947, '轮盘规则与分组', '从对立转向互相了解'),
            (948, 966, '阿奇公开出场', '玫瑰、邀请与爱人身份'),
            (967, 990, '测试操作与特殊互动', '轮盘触发测试，现场顺序随机'),
            (991, 1006, '程聿怀与羌青瓷', '初见、年数、纹面与耳语'),
            (1007, 1021, '以撒与缪宏谟', '初见差异、蛇与蝴蝶标本'),
            (1022, 1048, '蒋伯驾与程走柳', '前任问答、第二通电话与约会卡'),
            (1049, 1066, '黛利拉与阿奇', '初见、一见钟情与扑克牌'),
            (1067, 1089, '魔术与退场', '背景资料、雨声与下一幕')]

# Explicitly annotate only speech continuations and spoken prompts. All other
# paragraphs remain stage/instruction text; speaker names are not inferred
# merely because a person is mentioned.
CONTINUATIONS = {}


def assign(key: str, *ranges: tuple[int, int]) -> None:
    for start, end in ranges:
        for number in range(start, end + 1):
            CONTINUATIONS[number] = key


assign('q', (776, 778), (780, 783), (786, 786), (788, 789), (791, 791),
       (839, 839), (938, 939), (1006, 1006), (1039, 1039), (1083, 1083),
       (1085, 1085))
assign('o', (800, 800), (814, 814), (820, 823), (861, 862), (884, 885),
       (889, 889), (898, 900), (903, 907), (919, 919), (934, 935),
       (943, 947), (1017, 1018), (1070, 1070))
CONTINUATIONS[814] = 'q'
assign('a', (961, 961), (1060, 1060))
assign('x', (869, 869), (871, 871), (1042, 1042))
ALTERNATIVE_PROMPTS = {993: ['a', 'd'], 1010: ['a', 'd'], 1024: ['a', 'd']}
NAME_REGEX = re.compile(r'(羌\s*青\s*瓷|奥\s*丁|阿\s*奇|羌)([^：:"“\n]{0,20})[:：]')


def role_for(value: str) -> str:
    compact = re.sub(r'\s+', '', value)
    return {'羌青瓷': 'q', '羌': 'q', '奥丁': 'o', '阿奇': 'a'}[compact]


def segments(number: int, text: str) -> list[tuple[str | None, str]]:
    if number in ALTERNATIVE_PROMPTS or number in [991, 1049]:
        return [(None, text)]
    if number == 1060:
        start = text.index('“第一次见小黛')
        return [(None, text[:start]), ('a', text[start:])]
    matches = list(NAME_REGEX.finditer(text))
    if not matches:
        return [(CONTINUATIONS.get(number), text)]
    parts = []
    if matches[0].start():
        parts.append((CONTINUATIONS.get(number), text[:matches[0].start()]))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        parts.append((role_for(match.group(1)), text[match.start():end]))
    return parts


def inline_text(text: str, speaker: str | None) -> str:
    # Complete parenthetical directions are visually secondary. Keep every
    # character, including source whitespace and imperfect bracket pairs.
    pattern = re.compile(r'\([^()]*\)|（[^（）]*）|【[^【】]*】')
    pieces = []
    offset = 0
    for match in pattern.finditer(text):
        pieces.append(html.escape(text[offset:match.start()]))
        pieces.append('<span class="inline-direction">' + html.escape(match.group()) + '</span>')
        offset = match.end()
    pieces.append(html.escape(text[offset:]))
    rendered = ''.join(pieces)
    if speaker:
        return f'<span class="voice voice-{speaker}">{rendered}</span>'
    return '<span class="direction">' + rendered + '</span>'


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    rows = [json.loads(line) for line in
            (ROOT / '分析/流氓叙事手册-互动研究-20260915.jsonl')
            .read_text(encoding='utf-8').splitlines() if line.strip()]
    rows = [row for row in rows if row['part'] == 'word/document.xml'
            and 774 <= row['paragraph'] <= 1089]
    markdown = (ROOT / '分析/流氓叙事-第一幕读本后互动原文-20260930-第1版.md').read_text(encoding='utf-8')
    for row in rows:
        assert f"**P{row['paragraph']:04d}**\n\n{row['text']}" in markdown
    assert len(rows) == 316
    sections = []
    nav = []
    assignments = []
    for index, (start, end, title, subtitle) in enumerate(SECTIONS, 1):
        cards = []
        for row in rows:
            number, text = row['paragraph'], row['text']
            if not start <= number <= end:
                continue
            parts = segments(number, text)
            assert ''.join(fragment for _, fragment in parts) == text
            speakers = list(dict.fromkeys(key for key, _ in parts if key))
            alternative = number in ALTERNATIVE_PROMPTS
            if alternative:
                speakers = ALTERNATIVE_PROMPTS[number]
            badges = ''.join(f'<span class="badge badge-{key}">{NAMES[key]}</span>' for key in speakers)
            if alternative:
                badges += '<span class="kind">提问人可选</span>'
            elif '问：' in text or '问，' in text:
                badges += '<span class="kind">提问提示</span>'
            elif not speakers:
                badges = '<span class="kind">动作 / 流程</span>'
            if number in [869, 871, 1042]:
                badges += '<span class="kind">电话</span>'
            if number == 1006 or number == 1039:
                badges += '<span class="kind">耳语</span>'
            body = ''.join(inline_text(fragment, key) for key, fragment in parts)
            cards.append(f'<article class="entry {"spoken" if speakers else "stage"}" '
                         f'id="p{number}" data-speakers="{" ".join(speakers)}">'
                         f'<div class="entry-meta"><a class="pid" href="#p{number}">P{number:04d}</a>'
                         f'<div class="badges">{badges}</div></div>'
                         f'<div class="source">{body}</div></article>')
            assignments.append({'paragraph': number, 'speakers': speakers,
                                'alternative_prompt': alternative, 'segments': parts})
        sections.append(f'<section class="scene" id="scene-{index}"><div class="scene-heading">'
                        f'<span class="scene-number">{index:02d}</span><div><h2>{title}</h2>'
                        f'<p>{subtitle}<span class="range">P{start:04d}–P{end:04d}</span></p></div>'
                        '</div><div class="entries">' + ''.join(cards) + '</div></section>')
        nav.append(f'<a href="#scene-{index}"><span>{index:02d}</span>{title}</a>')
    colors = '\n'.join(f'.voice-{key}{{color:{color}}}.badge-{key},.role[data-role="{key}"]'
                       f'{{--role:{color};color:{color}}}' for key, _, color in ROLES)
    legend = ''.join(f'<span class="legend-item" style="--role:{color}"><i></i>{name}</span>'
                     for _, name, color in ROLES)
    buttons = '<button class="role active" data-role="all" aria-pressed="true">全部人物</button>'
    buttons += ''.join(f'<button class="role" data-role="{key}" aria-pressed="false">{name}</button>'
                       for key, name, _ in ROLES if key in ['q', 'o', 'a', 'x'])
    page = TEMPLATE.replace('__COLORS__', colors).replace('__LEGEND__', legend)
    page = page.replace('__NAV__', ''.join(nav)).replace('__BUTTONS__', buttons)
    page = page.replace('__SECTIONS__', ''.join(sections))
    OUTPUT.write_text(page, encoding='utf-8')
    (ROOT / '质检/第一幕人物分色标注-20260930-第1版.json').write_text(
        json.dumps(assignments, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(OUTPUT), 'paragraphs': len(rows),
                      'sections': len(SECTIONS)}, ensure_ascii=False))


TEMPLATE = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>流氓叙事 · 第一幕互动原文</title><style>
:root{--paper:#f7f6f2;--ink:#242b34;--muted:#727a83;--line:#e4e5e4;--accent:#087268}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:150px}body{margin:0;background:var(--paper);color:var(--ink);font-family:"Microsoft YaHei","PingFang SC",sans-serif}button,input{font:inherit}button,a,input{touch-action:manipulation}a{color:inherit}button{cursor:pointer}button:focus-visible,a:focus-visible,input:focus-visible{outline:3px solid #338d85;outline-offset:3px}
.top{background:#fff;border-bottom:1px solid var(--line);padding:38px max(28px,calc((100vw - 1280px)/2)) 25px}.eyebrow{font-size:12px;color:var(--accent);letter-spacing:3px;margin:0 0 14px}.top h1{font-size:32px;margin:0 0 12px;letter-spacing:1px;line-height:1.35}.intro{color:var(--muted);font-size:14px;line-height:1.8;margin:0;max-width:890px}.stats{display:flex;gap:18px;flex-wrap:wrap;margin-top:20px;color:#58616b;font-size:12px}.stats span{padding:6px 10px;border:1px solid var(--line);border-radius:6px;background:#fafbf9}
.toolbar{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.97);border-bottom:1px solid var(--line);padding:15px max(28px,calc((100vw - 1280px)/2));box-shadow:0 3px 12px #24302905}.tools{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.roles{display:flex;gap:7px;flex-wrap:wrap}.role{border:1px solid #e3e6e8;background:#fff;padding:7px 13px;border-radius:30px;font-size:13px;--role:#38444f}.role.active{background:color-mix(in srgb,var(--role) 9%,white);border-color:var(--role);box-shadow:inset 0 0 0 1px var(--role)}.search{margin-left:auto;position:relative}.search input{width:230px;max-width:100%;border:1px solid #dfe3e4;border-radius:7px;padding:9px 12px;font-size:13px;background:#fbfcfa}.subtools{display:flex;align-items:center;gap:18px;margin-top:12px;font-size:12px;color:#68717a;flex-wrap:wrap}.subtools label{display:flex;align-items:center;gap:5px}.count{margin-left:auto}.reset{border:0;background:transparent;color:var(--accent);padding:0;font-size:12px}.layout{max-width:1280px;margin:0 auto;display:grid;grid-template-columns:225px minmax(0,1fr);gap:34px;padding:30px 28px 80px}
.aside-inner{position:sticky;top:145px;max-height:calc(100vh - 170px);overflow:auto;scrollbar-width:thin}.aside h2{font-size:11px;letter-spacing:2px;font-weight:600;color:#858b90;margin:0 0 14px}.nav a{display:flex;align-items:baseline;gap:10px;text-decoration:none;padding:10px 0;font-size:12px;line-height:1.6;color:#56616b}.nav a:hover{color:var(--accent)}.nav a span{color:#98a2aa;font-size:10px;letter-spacing:1px;min-width:17px}.legend{margin-top:28px;border-top:1px solid var(--line);padding-top:20px;display:grid;grid-template-columns:1fr 1fr;gap:13px 5px}.legend-item{font-size:11px;display:flex;align-items:center;gap:7px;color:var(--role)}.legend-item i{width:7px;height:7px;flex:none;border-radius:50%;background:var(--role)}.note{font-size:11px;line-height:1.9;color:#858b91;margin:18px 0}.scene{margin:0 0 38px}.scene-heading{display:flex;gap:15px;align-items:center;margin-bottom:17px}.scene-number{font-size:26px;font-weight:300;color:#a6b7b3;font-family:Georgia,serif}.scene h2{font-size:18px;font-weight:600;margin:0 0 5px}.scene-heading p{font-size:11px;color:#818991;margin:0;line-height:1.8}.range{margin-left:15px;font-family:Consolas,monospace;color:#9aa1a6}.entries{display:grid;gap:9px}.entry{background:#fff;border:1px solid #e2e6e5;border-radius:8px;padding:16px 20px;transition:opacity .15s,box-shadow .15s}.entry:target{box-shadow:0 0 0 2px #449a91}.entry-meta{display:flex;gap:13px;align-items:center;margin-bottom:8px;min-height:18px}.pid{font-family:Consolas,monospace;text-decoration:none;font-size:10px;letter-spacing:.4px;color:#a1a8ae;flex:none}.pid:hover{color:var(--accent)}.badges{display:flex;gap:6px;flex-wrap:wrap;align-items:center}.badge{font-size:10px;background:color-mix(in srgb,var(--role) 8%,white);padding:3px 7px;border-radius:4px}.kind{font-size:10px;color:#8a9299}.source{font-size:15px;line-height:1.95;white-space:pre-wrap;overflow-wrap:anywhere;tab-size:4}.voice{font-weight:500}.direction,.inline-direction{color:#7b848c;font-weight:400}.inline-direction{font-size:.92em}.stage{background:#eff1ef;border-color:#e7e9e5;padding-top:12px;padding-bottom:12px}.stage .source{font-size:13px;line-height:1.9}.entry.dimmed{opacity:.27}.entry.dimmed:hover{opacity:.9}[hidden]{display:none!important}.empty{background:#fff;border:1px dashed #cbd4d0;border-radius:8px;padding:45px 20px;text-align:center;color:#748079}.footer{font-size:11px;color:#899099;line-height:1.9;border-top:1px solid var(--line);padding-top:20px}.footer a{color:#477f79}body.hide-directions .stage{display:none}body.hide-directions .inline-direction{display:none}
@media(max-width:900px){.layout{grid-template-columns:170px minmax(0,1fr);gap:20px}.top h1{font-size:27px}.toolbar{padding-inline:24px}.search{margin-left:0}.search input{width:200px}.aside-inner{top:165px}}
@media(max-width:640px){html{scroll-padding-top:210px}.top{padding:26px 18px 22px}.top h1{font-size:24px}.intro{font-size:12px}.toolbar{padding:12px 18px}.tools{gap:11px}.role{font-size:12px;padding:6px 10px}.search{width:100%}.search input{width:100%}.subtools{gap:12px}.layout{display:block;padding:22px 16px 50px}.aside-inner{position:static;max-height:none;overflow:visible}.aside{margin-bottom:25px}.aside h2{display:none}.nav{display:flex;gap:7px;overflow-x:auto;white-space:nowrap;padding-bottom:7px}.nav a{padding:6px 10px;border:1px solid var(--line);border-radius:5px;flex:none;font-size:11px;gap:6px}.legend{margin-top:12px;padding-top:13px;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px 5px}.legend-item{font-size:10px;gap:4px}.note{margin-bottom:0}.entry{padding:13px 14px}.source{font-size:14px}.range{display:block;margin-left:0}.scene h2{font-size:17px}.scene{margin-bottom:28px}.count{margin-left:0}}
@media print{.toolbar,.aside,.stats{display:none}.top{padding:10px 0;border:0}.layout{display:block;padding:20px 0}.entry{break-inside:avoid;opacity:1!important;box-shadow:none!important}.entry[hidden],.scene[hidden]{display:block!important}.stage{display:block!important}.inline-direction{display:inline!important}.voice,.badge{print-color-adjust:exact;-webkit-print-color-adjust:exact}.scene-heading{break-after:avoid}.footer{font-size:9px}}
__COLORS__
</style></head><body>
<header class="top"><p class="eyebrow">原文阅读 · 第一幕</p><h1>读本结束以后，谁接住了谁。</h1><p class="intro">《流氓叙事》主持人手册的第一幕公共互动。沿着原文顺序阅读，人物台词分色，动作与流程显示为灰色。正文保留原有文字、空格与标注。</p><div class="stats"><span>316 段原文</span><span>P0774 — P1089</span><span>11 个阅读段落</span><span>含剧情剧透</span></div></header>
<div class="toolbar"><div class="tools"><div class="roles" aria-label="突出显示人物">__BUTTONS__</div><label class="search"><input id="search" type="search" placeholder="搜索台词、人物或段落编号" aria-label="搜索原文"></label></div><div class="subtools"><label><input id="directions" type="checkbox" checked> 显示舞台与流程说明</label><button id="reset" class="reset">重置阅读</button><span id="count" class="count" aria-live="polite">显示 316 / 316 段</span></div></div>
<div class="layout"><aside class="aside"><div class="aside-inner"><h2>阅读顺序</h2><nav class="nav" aria-label="章节导航">__NAV__</nav><div class="legend" aria-label="人物颜色">__LEGEND__</div><p class="note">点人物可突出其话语，其他段落仍保留上下文。玩家的自由回答在手册中多为动作提示，未补写台词。灰色的可选提问保留原文指定的多个提问人。</p><p class="note">四组测试现场顺序随机；页面按手册原文排列。章节标题与人物标签为阅读辅助，不属于原文。</p></div></aside><main><div id="empty" class="empty" hidden>没有找到相符段落。试试其他词，或重置阅读。</div>__SECTIONS__<footer class="footer">来源 · 流氓叙事手册.docx / word/document.xml 非空段落 P0774–P1089。编号不是 Word 页码。<br>原始文件未改动。人物分色与阅读标题由整理添加。<a href="流氓叙事-第一幕读本后互动原文-20260930-第1版.md">查看对应 Markdown 原文</a>。</footer></main></div>
<script>
const entries=[...document.querySelectorAll('.entry')], scenes=[...document.querySelectorAll('.scene')], search=document.querySelector('#search'), directions=document.querySelector('#directions');
let selected='all';
function update(){const query=search.value.trim().toLocaleLowerCase();document.body.classList.toggle('hide-directions',!directions.checked);let visible=0;entries.forEach(el=>{const match=!query||(el.querySelector('.pid').textContent+' '+el.querySelector('.source').textContent).toLocaleLowerCase().includes(query);el.hidden=!match;el.classList.toggle('dimmed',selected!=='all'&&!el.dataset.speakers.split(' ').includes(selected));if(match&&(directions.checked||!el.classList.contains('stage')))visible++});scenes.forEach(el=>{el.hidden=![...el.querySelectorAll('.entry')].some(row=>!row.hidden&&(directions.checked||!row.classList.contains('stage')))});document.querySelector('#count').textContent=`显示 ${visible} / 316 段`;document.querySelector('#empty').hidden=visible!==0;}
document.querySelectorAll('.role').forEach(button=>button.addEventListener('click',()=>{selected=button.dataset.role;document.querySelectorAll('.role').forEach(b=>{b.classList.toggle('active',b===button);b.setAttribute('aria-pressed',String(b===button))});update()}));
search.addEventListener('input',update);directions.addEventListener('change',update);document.querySelector('#reset').addEventListener('click',()=>{search.value='';directions.checked=true;document.querySelector('.role[data-role="all"]').click()});
update();
</script></body></html>'''


if __name__ == '__main__':
    main()
