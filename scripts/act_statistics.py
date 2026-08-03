from __future__ import annotations

import json
import re
import statistics
from pathlib import Path


ACT_RE = re.compile(r"^(第[一二三四五六七八九十]+幕|尾声)$")
NOISE_RE = re.compile(r"^(?:\d+|侵探案|探案|流氓叙事)$")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    source_dir = root / "analysis" / "extracted"
    lines = ["# 角色本分幕篇幅统计", ""]
    for path in sorted(source_dir.glob("*本.jsonl")):
        if "手册" in path.stem:
            continue
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line
        ]
        acts: dict[str, list[str]] = {}
        current = "幕外"
        for row in rows:
            if row["part"] != "word/document.xml":
                continue
            text = str(row["text"]).strip()
            if ACT_RE.fullmatch(text):
                current = text
                acts.setdefault(current, [])
                continue
            if current != "幕外" and text and not NOISE_RE.fullmatch(text):
                acts[current].append(text)
        lines.extend([f"## {path.stem}", ""])
        for act, values in acts.items():
            lengths = [len(value) for value in values]
            lines.append(
                f"- {act}：{sum(lengths)} 字符，{len(values)} 段，"
                f"段落中位数 {statistics.median(lengths):.0f} 字符"
            )
        lines.append("")
    target = root / "analysis" / "分幕篇幅统计.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
