from pathlib import Path
import re
import json
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '草稿/末日学校/第一幕互动/当前稿/末日学校-第一幕读本后互动-G人物深化版-20261002-v5.md'
TARGET = ROOT / '舞台预演/源码/数据/演示流程.json'
text = SOURCE.read_text(encoding='utf-8')
scenes = []
for section in re.split(r'^## \d+\. ', text, flags=re.M)[1:]:
    title, _, rest = section.partition('\n')
    entries = []
    for match in re.finditer(r'\*\*(I\d+) · ([^*]+)\*\*\s*\n(.*?)(?=\n\*\*I\d+ ·|\Z)', rest, re.S):
        entries.append({'id':match[1], 'label':match[2].strip(), 'text':match[3].strip()})
    scenes.append({'title':title.strip(), 'subtitle':rest.strip().split('\n',1)[0], 'entries':entries})
TARGET.parent.mkdir(parents=True, exist_ok=True)
TARGET.write_text(json.dumps({'source':str(SOURCE.relative_to(ROOT)).replace('\\','/'),'scenes':scenes}, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Imported {len(scenes)} scenes and {sum(len(s["entries"]) for s in scenes)} entries')
