"""只读分析作品语料；输出统计、来源索引与六本图片取样，不改原件。"""
from pathlib import Path
from collections import Counter, defaultdict
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from io import BytesIO
import hashlib
import json
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '分析/流氓叙事写作DNA-20261029-第1版'
INDEX = ROOT / '分析/流氓叙事文本研究/资料索引.json'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
HAN = re.compile(r'[\u4e00-\u9fff]')
STARTS = {
    '以撒A本': 156, '程聿怀A本': 145, '程走柳A本': 164,
    '缪宏谟A本': 184, '蒋伯驾A本': 161, '黛利拉A本': 119,
    '以撒B本': 112, '程聿怀B本': 114, '程走柳B本': 133,
    '缪宏谟B本': 110, '蒋伯驾B本': 136, '黛利拉B本': 114,
    '以撒C本': 125, '程聿怀C本': 146, '程走柳C本': 113,
    '缪宏谟C本': 49, '蒋伯驾C本': 113, '黛利拉C本': 86,
}
VISUAL = ['黛利拉A本', '以撒B本', '蒋伯驾C本', '程聿怀C本', '程走柳A本', '缪宏谟B本']


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def clean(text):
    for token in ['极速扫描，就是高效', '夸克扫描王', '侵探案', '侵探 案', '探 案']:
        text = text.replace(token, '')
    text = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', text)
    text = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', text)
    text = re.sub(r'—\s+—', '——', text)
    text = re.sub(r'\s+([，。！？、；：,.!?;:])', r'\1', text)
    return text.strip()


def load_rows(item):
    rows = []
    source = ROOT / item['来源']
    container_ids = set()
    if source.suffix == '.docx':
        with ZipFile(source) as z:
            doc = ET.fromstring(z.read('word/document.xml'))
        for pid, p in enumerate(doc.findall('.//w:body//w:p', NS), 1):
            if p.find('.//w:p', NS) is not None:
                container_ids.add(pid)
    for lineno, line in enumerate((ROOT / item['提取文本']).read_text(encoding='utf-8-sig').splitlines(), 1):
        m = re.match(r'^\[(\d+)\]\s*(.*)$', line)
        if m:
            rows.append({'段号': int(m[1]), '行号': lineno, '原文': m[2], '容器重复': int(m[1]) in container_ids})
    return rows


def prose_rows(stem, rows):
    result = []
    for row in rows:
        if row['段号'] < STARTS.get(stem, 0) or row['容器重复']:
            continue
        text = clean(row['原文'])
        if any(token in text for token in ['-做完这一场', '-请好好珍惜']):
            break
        if any(token in text for token in ['你需要做到', '你需做到']):
            continue
        if not HAN.search(text):
            continue
        if any(token in text for token in ['发行工作室', '人物原画', '后期美术', '制作团队', '媒体支持', 'WEHEAD']):
            continue
        if re.fullmatch(r'第[一二三四五六七八九十]+幕|[侵探案院色]+', text):
            continue
        if re.search(r'请(?:在|出门|等待|停|翻|认真阅读)|【全局有效】|可对.{0,8}说', text):
            continue
        result.append({**row, '规范化': text})
    return result


def describe(texts):
    joined = ''.join(texts)
    chunks = [re.sub(r'[^\w\u4e00-\u9fff]', '', s) for s in re.split(r'[。！？!?]+', joined)]
    lengths = [len(s) for s in chunks if HAN.search(s)]
    lengths.sort()
    def pct(q):
        return lengths[min(len(lengths) - 1, int((len(lengths) - 1) * q))] if lengths else 0
    n = len(HAN.findall(joined))
    return {
        '汉字数': n, '抽取文本块数': len(texts), '句末标点切分片段数': len(lengths),
        '片段平均字长': round(statistics.mean(lengths), 2) if lengths else 0,
        '片段长度中位数': pct(.5), '片段长度四分位': [pct(.25), pct(.75)],
        '不超过15字片段占比': round(sum(x <= 15 for x in lengths) / max(len(lengths), 1), 4),
        '不少于50字片段占比': round(sum(x >= 50 for x in lengths) / max(len(lengths), 1), 4),
        '平均抽取块字长': round(n / max(len(texts), 1), 2),
        '标点字符数': {p: joined.count(p) for p in ['，', '。', '？', '?', '！', '!', '：', ':', '；', '…', '—', '（', '(', '“', '”', '【']},
        '表达观察次数': {p: joined.count(p) for p in ['你想', '你知道', '你以为', '其实', '可是', '但是', '命运', '后来', '不是', '而是', '好像', '仿佛', '哥哥', '母亲', '活着']},
    }


def visual_sample():
    from PIL import Image, ImageOps, ImageDraw, ImageFont
    folder = OUT / '版面取样'
    folder.mkdir(exist_ok=True)
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 16)
    details = []
    for stem in VISUAL:
        src = ROOT / '原始资料/原始文件/流氓叙事' / (stem + '.docx')
        with ZipFile(src) as z:
            names = [n for n in z.namelist() if n.startswith('word/media/') and not n.endswith('/')]
            cols, cw, ch = 4, 270, 235
            canvas = Image.new('RGB', (cw * cols, ch * ((len(names) + cols - 1) // cols)), '#e8e8e8')
            draw = ImageDraw.Draw(canvas)
            items = []
            for i, name in enumerate(names):
                try:
                    data = z.read(name)
                    im = Image.open(BytesIO(data)).convert('RGB')
                except Exception as error:
                    items.append({'图像': name, '错误': str(error)})
                    continue
                x, y = i % cols * cw, i // cols * ch
                scale = min((cw - 16) / im.width, (ch - 54) / im.height)
                thumb = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))))
                canvas.paste(thumb, (x + 8, y + 42))
                draw.text((x + 8, y + 4), Path(name).name, font=font, fill='black')
                draw.text((x + 8, y + 22), f'{im.width}×{im.height}', font=font, fill='black')
                items.append({'图像': name, '宽': im.width, '高': im.height, '字节': len(data)})
            canvas.save(folder / (stem + '-内嵌图片索引.jpg'), quality=88)
            doc = ET.fromstring(z.read('word/document.xml'))
            sizes, fonts, colors = Counter(), Counter(), Counter()
            for r in doc.findall('.//w:r', NS):
                text = ''.join(t.text or '' for t in r.findall('.//w:t', NS))
                count = len(HAN.findall(text))
                if not count:
                    continue
                props = r.find('w:rPr', NS)
                if props is None:
                    continue
                for key, tag in [(sizes, 'sz'), (colors, 'color')]:
                    node = props.find('w:' + tag, NS)
                    if node is not None:
                        key[node.get('{' + NS['w'] + '}val', '')] += count
                node = props.find('w:rFonts', NS)
                if node is not None:
                    fonts[node.get('{' + NS['w'] + '}eastAsia', node.get('{' + NS['w'] + '}ascii', ''))] += count
            details.append({'文件': stem, '图片': items, '半磅字号按汉字计数': sizes.most_common(8), '字体按汉字计数': fonts.most_common(8), '颜色按汉字计数': colors.most_common(8)})
    dump('版面取样数据.json', details)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = json.loads(INDEX.read_text(encoding='utf-8-sig'))
    metadata, clean_corpus, stage_corpus = [], [], defaultdict(list)
    for item in index:
        src = ROOT / item['来源']
        actual = hashlib.sha256(src.read_bytes()).hexdigest()
        if actual != item['sha256']:
            raise ValueError('源文件哈希与索引不符 ' + str(src))
        rows = load_rows(item)
        is_role = src.stem in STARTS
        cleaned = prose_rows(src.stem, rows) if is_role else []
        stage = src.stem[-2] if is_role else None
        texts = [x['规范化'] for x in cleaned]
        if is_role:
            clean_corpus.extend(texts)
            stage_corpus[stage].extend(texts)
        metadata.append({
            '文件': src.name, '作者': '本次分析作品级合成风格，不裁定独立作者', '发布日期': None,
            '资料类型': '玩家本' if is_role else '主持或互动手册', '角色': src.stem[:-2] if is_role else None,
            '册次': stage, '正文起段': STARTS.get(src.stem), '来源': item['来源'].replace('\\', '/'),
            '提取文本': item['提取文本'].replace('\\', '/'), 'SHA256': actual,
            '开头类型': {'A': '人物立场与命运预告', 'B': '共同创伤后重启私人记忆', 'C': '公共行动现场承接'}.get(stage, '执行说明'),
            '统计分组': '叙事近似统计' if is_role else '执行语境单列不混入叙事统计',
            '正文近似统计': describe(texts) if is_role else None,
            '注意': '扫描转Word含断行、乱码及识别误差；块长不等于原作段长；内容涵盖部分角色内引导',
        })
    dump('语料元数据.json', metadata)
    stats = {
        '说明': '全量扫描20份资料，18份玩家本参与叙事近似统计。保留P段号；去封面、容器重复、明显水印页码及少量流程句。不是人工全文通读。抽取块不是作者原始自然段。',
        '全部玩家本': describe(clean_corpus), '按册次': {k: describe(v) for k, v in stage_corpus.items()},
        '跨本相同抽取块去重': describe(list(dict.fromkeys(clean_corpus))),
    }
    sys.path.insert(0, str(ROOT / '自动化脚本/工具依赖/中文分词'))
    try:
        import jieba
        import jieba.posseg as posseg
        jieba.setLogLevel(40)
        for name in ['程聿怀', '程走柳', '缪宏谟', '蒋伯驾', '黛利拉', '以撒', '肖须言', '羌青瓷', '布雷诺', '布雷族', '诺族', '莱诺', '缪家', '奥丁', '摩伊拉', '撒该']:
            jieba.add_word(name, tag='nr')
        for name in ['莱诺家族', '金狮医院', '狂草帮', '怒河', '延迟']:
            jieba.add_word(name, tag='nt')
        for name in ['人', '事', '东西', '哥哥', '姐姐', '父亲', '母亲']:
            jieba.add_word(name, tag='n')
        jieba.add_word('无法', tag='d')
        buckets = {'名词': Counter(), '动词': Counter(), '副词': Counter(), '专名': Counter()}
        # 每块分词，避免跨块断行误连；跨行词仍可能被拆分，统计仅作辅助。
        for text in clean_corpus:
            for word, flag in posseg.cut(text):
                if not HAN.search(word):
                    continue
                if flag.startswith('nr') or flag.startswith('ns') or flag.startswith('nt'):
                    buckets['专名'][word] += 1
                elif flag.startswith('n'):
                    buckets['名词'][word] += 1
                elif flag.startswith('v'):
                    buckets['动词'][word] += 1
                elif flag == 'd':
                    buckets['副词'][word] += 1
        stats['分词器'] = 'jieba 0.42.1；词性自动标注，不是人工确认的词表'
        stats['高频词'] = {k: v.most_common({'名词': 100, '动词': 50, '副词': 50, '专名': 50}[k]) for k, v in buckets.items()}
    except ImportError:
        stats['分词器'] = '不可用；未生成伪词性统计'
    dump('语言统计.json', stats)
    visual_sample()
    print(json.dumps({'输出': str(OUT.relative_to(ROOT)), '资料数': len(metadata), '玩家本': 18, '汉字数': stats['全部玩家本']['汉字数'], '分词器': stats['分词器'], '图片取样本数': len(VISUAL)}, ensure_ascii=False))


def read_windows(ids):
    windows = json.loads((OUT / '精读窗口.json').read_text(encoding='utf-8'))
    by_id = {x['编号']: x for x in windows}
    for identifier in ids:
        item = by_id[identifier]
        print('\n' + identifier + ' ' + item['文件'] + ' ' + item['名称'])
        path = ROOT / '分析/流氓叙事文本研究/提取文本' / (item['文件'] + '.txt')
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            match = re.match(r'^\[(\d+)\]', line)
            if match and item['起段'] <= int(match[1]) <= item['止段']:
                print(line)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--读选段':
        read_windows(sys.argv[2:])
    else:
        main()
