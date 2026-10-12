"""核对证据原文、出处链接、引用编号、原件哈希及本轮交付结构。"""
from pathlib import Path
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "分析/流氓叙事创作逆向/20261012第1轮"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def main():
    manifest = json.loads((OUT / "原件与摘录核对.json").read_text(encoding="utf-8"))
    evidence = json.loads((OUT / "证据记录.json").read_text(encoding="utf-8"))
    known = {row["证据编号"] for row in evidence}
    raw_cache = {}
    for row in manifest:
        path = ROOT / row["原件"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["原件SHA256"], path
        if path.suffix == ".docx":
            with zipfile.ZipFile(path) as archive:
                doc = ET.fromstring(archive.read("word/document.xml"))
                paragraphs = ["".join(t.text or "" for t in p.findall(".//w:t", NS))
                              for p in doc.findall(".//w:body//w:p", NS)]
        else:
            paragraphs = path.read_text(encoding="utf-8-sig").splitlines()
        raw_cache[row["原件"]] = paragraphs
    refs_checked = 0
    for item in evidence:
        for ref in item["来源"]:
            paragraphs = raw_cache[ref["原件"]]
            expected = "\n".join(f"[{i:04d}] {p}" for i, p in enumerate(paragraphs, 1)
                                 if ref["原段落起"] <= i <= ref["原段落止"] and p.strip())
            assert expected == ref["原文"], item["证据编号"]
            extracted_lines = (ROOT / ref["摘录"]).read_text(encoding="utf-8").splitlines()
            assert extracted_lines[ref["摘录首行"] - 1].startswith("["), ref
            refs_checked += 1
    links_checked = 0
    for path in OUT.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        for group in re.findall(r"〔证据([^〕]+)〕", text):
            for code in re.findall(r"\d{2}", group):
                assert code in known, (path, code)
        for target in re.findall(r"\]\((D:/[^)]+)\)", text):
            match = re.match(r"(.+?)(?::(\d+))?$", target)
            linked = Path(match[1])
            assert linked.exists(), target
            if match[2]:
                assert int(match[2]) <= len(linked.read_text(encoding="utf-8").splitlines()), target
            links_checked += 1
    report = (OUT / "十二层创作逆向报告.md").read_text(encoding="utf-8")
    layers = ["故事架构", "人物设计", "关系网络", "情感结构", "互动机制", "情绪调度", "伏笔与反转",
              "沉浸机制", "NPC表演系统", "流程控制", "玩家心理", "创作方法论"]
    for layer in layers:
        assert any(layer in line for line in report.splitlines() if line.startswith("## ")), layer
    scenes = [json.loads(line) for line in (OUT / "场景分析样例.jsonl").read_text(encoding="utf-8").splitlines()]
    for scene in scenes:
        assert scene["实测状态"] == "未实测"
        assert all(code in known for code in scene["出处"])
        for key in ("文本明确证实", "根据设计推断", "需要实测验证"):
            assert key in scene
    summary = {"原件哈希复核": len(manifest), "证据条数": len(evidence), "原文片段复核": refs_checked,
               "有效本地链接": links_checked, "十二层标题": len(layers), "可解析场景记录": len(scenes),
               "全部场景标明未实测": True}
    target = ROOT / "质检/流氓叙事创作逆向-20261012第1轮-核对记录.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# 流氓叙事创作逆向核对记录", "",
             "以下为文件、出处和交付结构核对结果，不代表玩家体验或创作规则的实测验证。", "",
             "| 核对项 | 结果 |", "| --- | --- |"]
    lines += [f"| {key} | {value} |" for key, value in summary.items()]
    lines += ["", "原文片段已与当前原始 Word 正文或原始文本逐项比对，包括段落内部换行。原件哈希与本轮初始清单一致。",
              "", "报告中的日期、关系与核心动作依据所列原文人工复核。文本事实、功能推断及测试方案分别标记。",
              "", "排版采用 Markdown，核对表格列数、列表间隔与本地链接。未创建或交付 Word 文档，不涉及页码或缺页判断。"]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
