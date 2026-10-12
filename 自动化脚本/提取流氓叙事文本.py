"""只读提取指定原始资料，保留原段落序号与来源哈希。"""
from pathlib import Path
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "原始资料" / "原始文件" / "流氓叙事"
OUTPUT = ROOT / "分析" / "流氓叙事文本研究" / "提取文本"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    index = []
    for source in sorted(SOURCE.iterdir()):
        if source.suffix.lower() not in {".docx", ".txt"}:
            continue
        data = source.read_bytes()
        if source.suffix.lower() == ".docx":
            with zipfile.ZipFile(source) as archive:
                root = ET.fromstring(archive.read("word/document.xml"))
            paragraphs = ["".join(t.text or "" for t in p.findall(".//w:t", NS))
                          for p in root.findall(".//w:body//w:p", NS)]
        else:
            paragraphs = data.decode("utf-8-sig").splitlines()
        target = OUTPUT / (source.stem + ".txt")
        target.write_text("\n".join(f"[{i:04d}] {p}" for i, p in enumerate(paragraphs, 1) if p.strip()), encoding="utf-8")
        index.append({"来源": str(source.relative_to(ROOT)), "提取文本": str(target.relative_to(ROOT)),
                      "sha256": hashlib.sha256(data).hexdigest(), "原段落数": len(paragraphs),
                      "非空段落数": sum(bool(p.strip()) for p in paragraphs), "字符数": sum(map(len, paragraphs))})
    (OUTPUT.parent / "资料索引.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    for row in index:
        print(f"{Path(row['来源']).name}\t{row['非空段落数']} 段\t{row['字符数']} 字符")


if __name__ == "__main__":
    main()
