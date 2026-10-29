"""仅统一 Markdown/Word 文档内容，保留路径。默认预览；--apply 备份后执行；--check 检查。"""
from __future__ import annotations
import argparse
import bisect
from collections import Counter
from datetime import datetime, timezone, timedelta
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import quote
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
# Unicode escapes keep the historical mapping stable during future scans.
PAIRS = [
    ('\u6625\u65e5\u70b9\u540d', '春日'),
    ('\u8f66\u53d9\u5f8b', '车承宇'),
    ('\u59dc\u6cf0\u4f0d', '姜泰俊'),
    ('\u97e9\u6210\u5bb0', '韩正勋'),
    ('\u53d9\u5f8b', '承宇'),
    ('\u6cf0\u4f0d', '泰俊'),
    ('\u6210\u5bb0', '正勋'),
]
SKIP = {'工具依赖', '.git', '垃圾箱', '垃圾桶', '临时存储', 'node_modules', 'dist', '__pycache__',
        '.venv', 'venv', '依赖', '命名统一依赖', '命名统一记录', 'skill-validation-deps',
        '技能验证依赖', '.pytest_cache', '.mypy_cache'}
TEXT_EXT = {'.md'}
RAW = re.compile('|'.join(re.escape(a) for a, _ in PAIRS))
RAW_MAP = dict(PAIRS)
VARIANTS = dict(PAIRS)
for old, new in PAIRS:
    VARIANTS[quote(old)] = quote(new)
    VARIANTS[quote(old).lower()] = quote(new).lower()
    VARIANTS[json.dumps(old, ensure_ascii=True)[1:-1]] = json.dumps(new, ensure_ascii=True)[1:-1]
PATTERN = re.compile('|'.join(re.escape(k) for k in sorted(VARIANTS, key=len, reverse=True)))


# Existing paths are kept intact; the user requested document contents only.
PATH_RE = re.compile(
    r'(?:[A-Za-z]:[\\/]|(?:\.\.?[\\/])|(?:草稿|分析|成品|质检|自动化脚本|原始资料|垃圾箱|临时存储|舞台预演|\.agents|drafts)[\\/])'
    r'[^\s`"<>|()\[\]，。；]*'
)
INLINE_FILE = re.compile(r'`([^`\n]+\.(?:md|docx|pdf|py|html|json|jpg|png|svg))`', re.I)


def replace(text, counts=None):
    spans = [(m.start(), m.end()) for m in PATH_RE.finditer(text)]
    spans += [(m.start(), m.end()) for m in INLINE_FILE.finditer(text)]
    def change(match):
        if any(start <= match.start() and match.end() <= end for start, end in spans):
            return match[0]
        if counts is not None:
            counts.append(match[0])
        return VARIANTS[match[0]]
    return PATTERN.sub(change, text)


def safe(path):
    path = Path(path)
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError(f'路径越出项目，已停止：{path}')
    return path


def walk():
    for current, dirs, files in os.walk(ROOT):
        rel = Path(current).relative_to(ROOT)
        dirs[:] = sorted(d for d in dirs if d not in SKIP
                         and not (rel == Path('原始资料') and d == '原始文件')
                         and not (Path(current) / d).is_symlink()
                         and not getattr(Path(current) / d, 'is_junction', lambda: False)())
        for name in sorted(files):
            p = safe(Path(current) / name)
            if p != SELF and not p.is_symlink():
                yield p


def decode(data):
    if data.startswith(b'\xff\xfe'):
        return data[2:].decode('utf-16-le'), 'utf-16-le', b'\xff\xfe'
    if data.startswith(b'\xfe\xff'):
        return data[2:].decode('utf-16-be'), 'utf-16-be', b'\xfe\xff'
    if data.startswith(b'\xef\xbb\xbf'):
        return data[3:].decode('utf-8'), 'utf-8', b'\xef\xbb\xbf'
    return data.decode('utf-8'), 'utf-8', b''


def atomic(path, data):
    path = safe(path)
    fd, name = tempfile.mkstemp(prefix='命名替换-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        os.replace(name, path)
    finally:
        if Path(name).exists():
            Path(name).unlink()


def docx_bytes(data):
    from lxml import etree as ET
    output = io.BytesIO()
    changed = 0
    with ZipFile(io.BytesIO(data)) as src, ZipFile(output, 'w') as dst:
        for info in src.infolist():
            content = src.read(info.filename)
            if info.filename.endswith(('.xml', '.rels')):
                tree = ET.fromstring(content)
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                # A name may be split across formatting runs. Replace backwards,
                # preserving the prefix/suffix and each unaffected run's format.
                for paragraph in tree.xpath('.//w:p', namespaces=ns):
                    nodes = paragraph.xpath('.//w:t', namespaces=ns)
                    full = ''.join(n.text or '' for n in nodes)
                    starts = []
                    pos = 0
                    for node in nodes:
                        starts.append(pos)
                        pos += len(node.text or '')
                    for match in reversed(list(RAW.finditer(full))):
                        first = bisect.bisect_right(starts, match.start()) - 1
                        last = bisect.bisect_right(starts, match.end() - 1) - 1
                        begin, end = match.start() - starts[first], match.end() - starts[last]
                        if first == last:
                            value = nodes[first].text or ''
                            nodes[first].text = value[:begin] + RAW_MAP[match[0]] + value[end:]
                        else:
                            nodes[first].text = (nodes[first].text or '')[:begin] + RAW_MAP[match[0]]
                            for j in range(first + 1, last):
                                nodes[j].text = ''
                            nodes[last].text = (nodes[last].text or '')[end:]
                        changed += 1
                for node in tree.iter():
                    for key, value in list(node.attrib.items()):
                        updated = replace(value)
                        if updated != value:
                            node.set(key, updated)
                            changed += 1
                    if node.text:
                        updated = replace(node.text)
                        if updated != node.text:
                            node.text = updated
                            changed += 1
                if changed:
                    content = ET.tostring(tree, encoding='UTF-8', xml_declaration=True, standalone=True)
            dst.writestr(info, content)
    return (output.getvalue(), changed) if changed else (data, 0)


def hash_originals():
    result = {}
    root = ROOT / '原始资料' / '原始文件'
    if root.exists():
        for current, _, files in os.walk(root):
            for name in files:
                p = Path(current) / name
                result[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result


def renames(files):
    # Do not rename paths used by the excluded scripts and web previews.
    return []


def scan(files):
    changes = []
    for p in files:
        suffix = p.suffix.lower()
        if suffix not in TEXT_EXT | {'.docx'}:
            continue
        data = p.read_bytes()
        count, pages = 0, []
        if suffix == '.docx':
            updated, count = docx_bytes(data)
        else:
            try:
                text, encoding, bom = decode(data)
            except UnicodeError:
                continue
            replacements = []
            updated_text = replace(text, replacements)
            count = len(replacements)
            if p == ROOT / '项目说明.md':
                header = re.sub(r'\A# [^\r\n]+', '# 春日剧本创作工程', updated_text, count=1)
                count += int(header != updated_text)
                updated_text = header
            updated = bom + updated_text.encode(encoding)
        if updated != data:
            changes.append({'path': p, 'before': data, 'after': updated, 'count': count, 'pages': pages})
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--apply', action='store_true', help='先备份，再替换文档内容；不改名')
    action.add_argument('--check', action='store_true', help='检查旧名称残留，成功时退出码为零')
    args = parser.parse_args()
    files = list(walk())
    moves = renames(files)
    changes = scan(files)
    counts = Counter(item['path'].suffix.lower() for item in changes)
    print(json.dumps({'待更新文件': len(changes), '文件类型': dict(counts), '待改名路径': len(moves),
                      '替换次数': sum(item['count'] for item in changes)}, ensure_ascii=False))
    if args.check:
        for item in changes:
            print('内容残留：', item['path'].relative_to(ROOT))
        for src, _ in moves:
            print('名称残留：', src.relative_to(ROOT))
        return 1 if changes or moves else 0
    if not args.apply:
        for item in changes:
            print('内容：', item['path'].relative_to(ROOT), item['count'])
        for src, dst in moves:
            print('改名：', src.relative_to(ROOT), '->', dst.relative_to(ROOT))
        return 0
    if not changes and not moves:
        print('已是现行命名，无需重复修改。')
        return 0
    stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d-%H%M%S')
    record = ROOT / '分析' / '命名统一记录' / stamp
    record.mkdir(parents=True, exist_ok=False)
    originals = hash_originals()
    backups = {item['path'] for item in changes}
    for src, _ in moves:
        if src.is_file():
            backups.add(src)
    manifest = {
        'time': stamp, 'status': 'started', 'mapping': PAIRS,
        'changed': [{'from': x['path'].relative_to(ROOT).as_posix(),
                     'to': x['path'].relative_to(ROOT).as_posix(),
                     'sha256_before': hashlib.sha256(x['before']).hexdigest(),
                     'sha256_after': hashlib.sha256(x['after']).hexdigest(),
                     'count': x['count'], 'pdf_pages': x['pages']} for x in changes],
        'renamed': [{'from': a.relative_to(ROOT).as_posix(),
                     'to': replace(a.relative_to(ROOT).as_posix())} for a, _ in moves],
        'original_files': len(originals),
        'scope': ['.md', '.docx'],
        'paths_kept_for_existing_references': True,
        'pdf_content_and_previews_skipped': True,
    }
    report = record / '执行清单.json'
    def save_report():
        report.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + '\n', encoding='utf-8')
    save_report()
    with ZipFile(record / '原文件备份.zip', 'w', compression=8) as archive:
        for p in sorted(backups):
            archive.write(p, p.relative_to(ROOT).as_posix())
    try:
        for item in changes:
            if item['path'].read_bytes() != item['before']:
                raise RuntimeError(f'文件在扫描后被改动，已停止：{item["path"]}')
            atomic(item['path'], item['after'])
        for src, dst in moves:
            safe(src).rename(safe(dst))
        if hash_originals() != originals:
            raise RuntimeError('原始资料校验不一致，请检查。')
        manifest['originals_unchanged'] = True
        remaining = scan(list(walk()))
        if remaining or renames(list(walk())):
            raise RuntimeError('仍有旧名残留，请检查执行清单。')
        manifest['status'] = 'complete'
    except Exception as exc:
        manifest['status'] = 'failed'
        manifest['error'] = str(exc)
        raise
    finally:
        save_report()
    print('已完成，备份和清单：', record.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
