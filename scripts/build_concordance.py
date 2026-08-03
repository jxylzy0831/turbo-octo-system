from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ACT_RE = re.compile(r"^(第[一二三四五六七八九十]+幕|尾声)$")
YEAR_RE = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")
FUNCTION_RE = re.compile(r"任务|心里话|分享|不可分享|可以公开|请继续|翻页|线索|选择")


def load(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary: list[str] = ["# 语料结构统计", ""]
    for path in sorted(args.input_dir.glob("*.jsonl")):
        rows = [row for row in load(path) if row["part"] == "word/document.xml"]
        text = "".join(str(row["text"]) for row in rows)
        acts = [
            (int(row["paragraph"]), str(row["text"]))
            for row in rows
            if ACT_RE.fullmatch(str(row["text"]).strip())
        ]
        summary.extend(
            [
                f"## {path.stem}",
                "",
                f"- 非空段落：{len(rows)}",
                f"- 字符数：{len(text)}",
                f"- 阿奇提及：{text.count('阿奇')}",
                f"- 黛利拉提及：{text.count('黛利拉')}",
                f"- 分幕：{'；'.join(f'{name}@{number}' for number, name in acts) or '未识别'}",
                "",
            ]
        )

        concordance: list[str] = [f"# {path.stem}：阿奇/黛利拉/年份/功能页索引", ""]
        current_act = "幕外"
        for row in rows:
            paragraph = int(row["paragraph"])
            value = str(row["text"]).strip()
            if ACT_RE.fullmatch(value):
                current_act = value
            tags: list[str] = []
            if "阿奇" in value:
                tags.append("阿奇")
            if "黛利拉" in value:
                tags.append("黛利拉")
            years = YEAR_RE.findall(value)
            if years:
                tags.append("年份:" + ",".join(years))
            if FUNCTION_RE.search(value):
                tags.append("功能")
            if tags:
                concordance.append(
                    f"- [{current_act}｜段{paragraph}｜{'/'.join(tags)}] {value}"
                )
        (args.output_dir / f"{path.stem}-索引.md").write_text(
            "\n".join(concordance) + "\n", encoding="utf-8"
        )

    (args.output_dir / "语料结构统计.md").write_text(
        "\n".join(summary) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
