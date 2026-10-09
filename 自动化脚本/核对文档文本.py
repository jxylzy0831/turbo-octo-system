from pathlib import Path
import re
import sys

from docx import Document


def expected_lines(markdown: str) -> list[str]:
    lines: list[str] = []
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line or line == "---" or line.startswith("# "):
            continue
        if line.startswith("## ") and line[3:].startswith("阿奇 ·"):
            continue
        line = re.sub(r"^#{2,3}\s+", "", line)
        line = re.sub(r"^>\s+", "", line)
        line = re.sub(r"^-\s+", "", line)
        lines.append(line)
    return lines


def main() -> int:
    markdown_path = Path(sys.argv[1])
    docx_path = Path(sys.argv[2])
    expected = expected_lines(markdown_path.read_text(encoding="utf-8"))
    actual = [p.text.strip() for p in Document(docx_path).paragraphs if p.text.strip()]
    actual_set = set(actual)
    missing = [line for line in expected if line not in actual_set]
    print(f"{docx_path.name}: expected={len(expected)}, actual={len(actual)}, missing={len(missing)}")
    for line in missing[:20]:
        print(f"MISSING: {line}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
