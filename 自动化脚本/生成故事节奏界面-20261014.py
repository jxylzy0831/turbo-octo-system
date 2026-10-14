from pathlib import Path
import html
import json
import re

根目录 = Path(__file__).resolve().parents[1]
稿件目录 = 根目录 / '草稿' / '春日点名-节奏与恩书本-20261014-第1版'
输出目录 = Path('C:/Users/Yu/.codex/visualizations/2026/10/13/01a13799-4ae9-7f63-93fb-010be4797e5d')


def 转排版(文本):
    输出 = []
    段落 = []
    表格 = []

    def 收段():
        if 段落:
            输出.append('<p>' + html.escape(' '.join(段落)) + '</p>')
            段落.clear()

    def 收表():
        if not 表格:
            return
        行 = [x for x in 表格 if not re.match(r'^\|[\s|:-]+\|$', x)]
        输出.append('<div class="table-responsive"><table class="table table-sm">')
        for 索引, 内容 in enumerate(行):
            标签 = 'th' if 索引 == 0 else 'td'
            输出.append('<tr>' + ''.join(f'<{标签}>' + html.escape(x.strip()) + f'</{标签}>' for x in 内容.strip('|').split('|')) + '</tr>')
        输出.append('</table></div>')
        表格.clear()

    for 行 in 文本.strip().splitlines():
        if 行.startswith('|'):
            收段()
            表格.append(行)
            continue
        收表()
        if 行.startswith('#'):
            收段()
            输出.append('<h4>' + html.escape(行.lstrip('#').strip()) + '</h4>')
        elif not 行.strip():
            收段()
        else:
            段落.append(行.strip())
    收段()
    收表()
    return '\n'.join(输出)


def 按幕切分(文本):
    切分 = re.split(r'^## (第[一二三四五六七]幕[^\n]*)\n', 文本, flags=re.M)
    return [转排版(切分[i] + '\n' + 切分[i + 1]) for i in range(1, len(切分), 2)]


数据 = json.loads((稿件目录 / '节奏数据.json').read_text(encoding='utf-8'))
玩家文本 = (稿件目录 / '恩书-分幕玩家本.md').read_text(encoding='utf-8')
主持文本 = (稿件目录 / '恩书-互动与主持衔接.md').read_text(encoding='utf-8')
玩家幕 = 按幕切分(玩家文本)
主持切分 = re.split(r'^## (恩0[1-7][^\n]*)\n', 主持文本, flags=re.M)
主持幕 = [转排版(主持切分[i] + '\n' + 主持切分[i+1]) for i in range(1, len(主持切分), 2)]
总览文本 = ['学校、家庭、明日的邀请', '幸福过往与四人相识；停在聚会前', '共同相处；检查与交接出现疑点', '养父主使杀亲；黑袍入场旁观', '执行者供述；陪读与离开安排', '甲册到入场前；乙册在揭露后读', '承接实际结局，回到后续生活']
总览互动 = ['短演绎，回应身份与称呼', '四 NPC 依次与全桌接触', '四室四轮，每人都见四 NPC', '查验与打戏、撤离、辨认专属、短出片', '家属问询后，四对专属陪读与私聊', '全桌对峙、车黑化与重伤、四对结局场', '依次返场，全体谢幕']
assert len(数据) == len(玩家幕) == len(主持幕) == 7
for 索引, 项 in enumerate(数据):
    项['book'] = 玩家幕[索引]
    项['host'] = 主持幕[索引]
    项['overviewText'] = 总览文本[索引]
    项['overviewPlay'] = 总览互动[索引]

模板 = (稿件目录 / '节奏界面模板.html').read_text(encoding='utf-8')
嵌入数据 = json.dumps(数据, ensure_ascii=False).replace('</', '<\\/')
成稿 = 模板.replace('__STORY_DATA__', 嵌入数据)
assert '__STORY_DATA__' not in 成稿
assert len(成稿.encode('utf-8')) < 1_000_000
输出目录.mkdir(parents=True, exist_ok=True)
界面 = 输出目录 / 'spring-story-rhythm.html'
界面.write_text(成稿, encoding='utf-8')

统计 = []
for 索引, 项 in enumerate(数据):
    正文 = re.sub(r'<[^>]+>', '', 玩家幕[索引])
    统计.append({'幕': 项['id'], '名': 项['name'], '玩家文本汉字含标题与入口': len(re.findall(r'[\u4e00-\u9fff]', 正文))})
质检目录 = 根目录 / '质检' / '故事节奏与恩书本-20261014-第1版'
质检目录.mkdir(parents=True, exist_ok=True)
(质检目录 / '字数统计.json').write_text(json.dumps(统计, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'界面': str(界面), '统计': 统计}, ensure_ascii=False))
