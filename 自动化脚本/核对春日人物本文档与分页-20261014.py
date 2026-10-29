"""检查 Word 转换的正文完整性、实际页数、边界与逐页预览。"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from docx import Document
from PIL import Image, ImageDraw, ImageFont
import pdfplumber


ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / '质检/春日四位玩家个人本-20261014-排版第1版'


def han(text):
    return ''.join(re.findall(r'[\u4e00-\u9fff]', text))


def main():
    entries = json.loads((QA / '正文与来源核对.json').read_text(encoding='utf-8'))
    all_results = []
    contact_paths = []
    for entry in entries:
        name = entry['人物']
        document_path = ROOT / entry['文档']
        assert hashlib.sha256(document_path.read_bytes()).hexdigest() == entry['文档sha256']
        assert hashlib.sha256((ROOT / entry['来源']).read_bytes()).hexdigest() == entry['来源sha256']
        document = Document(document_path)
        body = [paragraph.text for paragraph in document.paragraphs if paragraph.text][2:]
        expected = han(''.join(body))
        preview = QA / name / '逐页预览'
        pdf_path = preview / (document_path.stem + '.pdf')
        pictures = sorted(preview.glob('page-*.png'), key=lambda path: int(path.stem.split('-')[-1]))
        page_results = []
        extracted = []
        with pdfplumber.open(pdf_path) as pdf:
            assert len(pdf.pages) == len(pictures), (name, '预览缺页')
            for index, page in enumerate(pdf.pages):
                bounds = (69, 63, page.width - 69, page.height - 55)
                text = page.crop(bounds).extract_text(x_tolerance=1.5, y_tolerance=3) or ''
                if index:
                    extracted.append(han(text))
                    assert han(text), (name, index + 1, '空白正文页')
                for char in page.chars:
                    assert -1 <= char['x0'] <= char['x1'] <= page.width + 1, (name, index + 1, '横向越界')
                    assert -1 <= char['top'] <= char['bottom'] <= page.height + 1, (name, index + 1, '纵向越界')
                page_results.append({
                    '物理页': index + 1,
                    '正文汉字': len(han(text)),
                    '首行': text.splitlines()[0] if text.splitlines() else '',
                    '末行': text.splitlines()[-1] if text.splitlines() else '',
                    '字体': sorted({char['fontname'] for char in page.chars}),
                    '待目视检查的短页': index > 0 and len(han(text)) < 100,
                })
        actual = ''.join(extracted)
        if actual != expected:
            mismatch = next((index for index, pair in enumerate(zip(expected, actual)) if pair[0] != pair[1]), min(len(expected), len(actual)))
            raise AssertionError((name, '预览正文不一致', len(expected), len(actual), mismatch,
                                  expected[max(0, mismatch - 20):mismatch + 60], actual[max(0, mismatch - 20):mismatch + 60]))
        font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 20)
        for offset in range(0, len(pictures), 4):
            group = pictures[offset:offset + 4]
            pages = [Image.open(path).convert('RGB') for path in group]
            width, height = pages[0].size
            label = 32
            gutter = 14
            sheet = Image.new('RGB', (width * 2 + gutter * 3, (height + label) * 2 + gutter * 3), '#e8e8e8')
            draw = ImageDraw.Draw(sheet)
            for number, page_image in enumerate(pages):
                x = gutter + (number % 2) * (width + gutter)
                y = gutter + (number // 2) * (height + label + gutter)
                draw.text((x + 4, y + 3), f'{name}  第{offset + number + 1}页', fill='black', font=font)
                sheet.paste(page_image, (x, y + label))
            contact = QA / name / f'原尺寸逐页总览-{offset // 4 + 1}.png'
            sheet.save(contact)
            contact_paths.append(str(contact.relative_to(ROOT)))
            for page_image in pages:
                page_image.close()
        result = {'人物': name, '总页数含封面': len(pictures), '正文汉字': len(expected),
                  '渲染正文逐字一致': True, '无空白正文页': True, '文字无页面越界': True, '逐页': page_results}
        all_results.append(result)
        print(name, len(pictures), '页，正文核对一致，短页', [page['物理页'] for page in page_results if page['待目视检查的短页']], flush=True)
    (QA / '实际分页与正文核对.json').write_text(json.dumps(all_results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (QA / '逐页总览索引.json').write_text(json.dumps(contact_paths, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
