from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def paragraph_text(node: ET.Element) -> str:
    parts: list[str] = []
    for child in node.iter():
        if child.tag == f"{W}t":
            parts.append(child.text or "")
        elif child.tag == f"{W}tab":
            parts.append("\t")
        elif child.tag in {f"{W}br", f"{W}cr"}:
            parts.append("\n")
    return "".join(parts).strip()


def paragraph_style(node: ET.Element) -> str | None:
    props = node.find(f"{W}pPr")
    style = props.find(f"{W}pStyle") if props is not None else None
    return style.get(f"{W}val") if style is not None else None


def extract_part(root: ET.Element, part_name: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    index = 0
    for node in root.iter():
        if node.tag != f"{W}p":
            continue
        text = paragraph_text(node)
        if not text:
            continue
        index += 1
        records.append(
            {
                "part": part_name,
                "paragraph": index,
                "style": paragraph_style(node),
                "text": text,
            }
        )
    return records


def extract_docx(path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    with zipfile.ZipFile(path) as archive:
        names = [
            name
            for name in archive.namelist()
            if name == "word/document.xml"
            or name.startswith("word/header") and name.endswith(".xml")
            or name.startswith("word/footer") and name.endswith(".xml")
            or name in {"word/footnotes.xml", "word/endnotes.xml", "word/comments.xml"}
        ]
        for name in sorted(names, key=lambda item: (item != "word/document.xml", item)):
            records.extend(extract_part(ET.fromstring(archive.read(name)), name))
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    records = extract_docx(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in records) + "\n",
        encoding="utf-8",
    )
    print(f"{args.source.name}: {len(records)} records -> {args.output}")


if __name__ == "__main__":
    main()
