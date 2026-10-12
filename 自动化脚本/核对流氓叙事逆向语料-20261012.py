"""核对本轮语料与原件，生成可追溯清单，不修改原始资料或既有摘录。"""
from pathlib import Path
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "原始资料/原始文件/流氓叙事"
EXTRACTED = ROOT / "分析/流氓叙事文本研究/提取文本"
OUT = ROOT / "分析/流氓叙事创作逆向/20261012第1轮"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    structure = []
    for source in sorted(SOURCE.iterdir()):
        if source.suffix.lower() not in {".docx", ".txt"}:
            continue
        data = source.read_bytes()
        images = 0
        if source.suffix.lower() == ".docx":
            with zipfile.ZipFile(source) as archive:
                document = ET.fromstring(archive.read("word/document.xml"))
                paragraphs = ["".join(t.text or "" for t in p.findall(".//w:t", NS))
                              for p in document.findall(".//w:body//w:p", NS)]
                images = sum(n.startswith("word/media/") for n in archive.namelist())
        else:
            paragraphs = data.decode("utf-8-sig").splitlines()
        expected = "\n".join(f"[{i:04d}] {p}" for i, p in enumerate(paragraphs, 1) if p.strip())
        extracted = EXTRACTED / (source.stem + ".txt")
        matches = extracted.exists() and extracted.read_text(encoding="utf-8") == expected
        if not matches:
            raise ValueError(f"摘录与原件不一致 {source.name}")
        rows.append({"原件": str(source.relative_to(ROOT)), "摘录": str(extracted.relative_to(ROOT)),
                     "原件SHA256": hashlib.sha256(data).hexdigest(), "逐段文本核对一致": matches,
                     "字符数": sum(map(len, paragraphs)), "非空段落数": sum(bool(p.strip()) for p in paragraphs),
                     "媒体文件数": images})
        structure.append(f"\n## {source.name}\n")
        for i, p in enumerate(paragraphs, 1):
            compact = re.sub(r"\s+", "", p)
            if (len(p) < 100 and re.search(r"第[一二三四五六七八九十\d]+幕|阅读|小黑屋|流程|环节|沉浸|复盘|互动|演绎|年表|任务|结局", compact)):
                structure.append(f"[{i:04d}] {p}")
    (OUT / "原件与摘录核对.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "幕次与流程定位.txt").write_text("\n".join(structure), encoding="utf-8")
    print(json.dumps({"文件数": len(rows), "总字符数": sum(r["字符数"] for r in rows),
                      "全部摘录与原件一致": all(r["逐段文本核对一致"] for r in rows)}, ensure_ascii=False))
    for r in rows:
        print(f"{Path(r['原件']).name}\t{r['字符数']} 字符\t{r['媒体文件数']} 媒体")


if __name__ == "__main__":
    main()
