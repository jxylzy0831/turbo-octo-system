from __future__ import annotations

import ctypes
import hashlib
import io
import json
import os
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from 提取文档文本 import extract_part


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / '原始资料/原始文件/流氓叙事手册.docx'
OUTPUT = ROOT / '分析/流氓叙事-第一幕读本后互动原文-20260930-第1版.md'
EXPECTED_HASH = 'F72B9A228226BCD2020535D98B38BB2E75722359FED7EB5261994C1B9D6F8DAB'


def read_shared(path: Path) -> bytes:
    if os.name != 'nt':
        return path.read_bytes()
    import msvcrt
    from ctypes import wintypes

    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                               wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD,
                               wintypes.HANDLE]
    api.CreateFileW.restype = wintypes.HANDLE
    handle = api.CreateFileW(str(path), 0x80000000, 7, None, 3, 0, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    with os.fdopen(fd, 'rb') as stream:
        return stream.read()


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f'Preserve existing version: {OUTPUT}')
    original = read_shared(SOURCE)
    before = hashlib.sha256(original).hexdigest().upper()
    if before != EXPECTED_HASH:
        raise ValueError('Original differs from the reference extraction version.')
    with zipfile.ZipFile(io.BytesIO(original)) as archive:
        records = extract_part(ET.fromstring(archive.read('word/document.xml')),
                               'word/document.xml')
    selected = [row for row in records if 774 <= row['paragraph'] <= 1089]
    assert len(selected) == 316
    assert selected[0]['text'] == '待所有玩家阅读完毕'
    reference = [json.loads(line) for line in
                 (ROOT / '分析/流氓叙事手册-互动研究-20260915.jsonl')
                 .read_text(encoding='utf-8').splitlines() if line.strip()]
    reference = [row for row in reference
                 if row['part'] == 'word/document.xml'
                 and 774 <= row['paragraph'] <= 1089]
    assert selected == reference, 'Original and reference paragraphs differ.'

    intro = ('# 《流氓叙事》第一幕全员读本结束后互动原文\n\n'
             '来源为 `原始资料/原始文件/流氓叙事手册.docx`，整理日期为 2026-09-30。\n\n'
             '范围为正文非空段落 P0774 至 P1089，共 316 段，从“待所有玩家阅读完毕”'
             '到第二幕读本音乐。读本期间私聊与第一幕前置带本要领不在本次摘录内。\n\n'
             '以下直接从原件正文 XML 提取，保留原文顺序、台词、舞台指令、空格、'
             '原有错字及标注差异，不改写、不补台词。段落前的 P 编号用于回查，'
             '不是 Word 页码。Markdown 不复现 Word 的字体、颜色、分页与图片。\n\n'
             f'原件 SHA-256 为 `{before}`。\n\n---\n\n')
    body = '\n\n'.join(f"**P{row['paragraph']:04d}**\n\n{row['text']}"
                         for row in selected) + '\n'
    OUTPUT.write_text(intro + body, encoding='utf-8')
    written = OUTPUT.read_text(encoding='utf-8').split('\n\n---\n\n', 1)[1]
    recovered = re.split(r'\*\*P\d{4}\*\*\n\n', written)[1:]
    recovered = [part[:-2] for part in recovered[:-1]] + [recovered[-1][:-1]]
    assert recovered == [row['text'] for row in selected], 'Output text differs.'
    after = hashlib.sha256(read_shared(SOURCE)).hexdigest().upper()
    assert after == before, 'Source changed during export.'
    report = {'output': str(OUTPUT), 'paragraphs': len(selected),
              'range': 'P0774-P1089', 'matches_original': True,
              'matches_reference': True, 'source_hash_unchanged': True,
              'sha256': after}
    (ROOT / '质检/第一幕互动原文导出核验-20260930-第1版.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
