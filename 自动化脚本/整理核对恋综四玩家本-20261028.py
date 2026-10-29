from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "草稿/春日恋综版四位玩家个人本-20261028-第1版"
QA = ROOT / "质检/春日恋综版四玩家本-20261028-第1版"
BOOKS = ["大姐-韩恩书.md", "二姐-韩知夏.md", "三姐-韩多允.md", "四妹-韩瑞真.md"]
CHAPTERS = ["第一幕", "第二幕", "第三幕", "第四幕", "第五幕", "第六幕", "尾声"]


def han(text):
    return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", text))


def main():
    result = {"文件": [], "失败": []}
    for name in BOOKS:
        path = BASE / name
        if not path.exists():
            result["失败"].append("缺文件 " + name)
            continue
        text = path.read_text(encoding="utf-8")
        markers = list(re.finditer(r"^#{1,3}\s+(第[一二三四五六]幕[^\n]*|(?:现场后)?(?:短)?尾声[^\n]*)\n", text, re.M))
        labels = [match.group(1).strip() for match in markers]
        problems = []
        if labels != CHAPTERS:
            problems.append("幕次不一致或仍有文学标题 " + " / ".join(labels))
        if re.search(r"[零〇一二三四五六七八九十百\d]+\s*(?:周岁|岁)", text):
            problems.append("仍出现数字年龄")
        for word in ("车承宇", "尹时安", "海原高中", "毕业班", "经营一支搬运配送队", "暂无义务", "不必先原谅", "不必原谅任何人"):
            if word in text:
                problems.append("需检查旧设定或剧情外说明 " + word)
        counts = []
        out = BASE / "玩家分幕" / path.stem
        out.mkdir(parents=True, exist_ok=True)
        for i, match in enumerate(markers):
            stop = markers[i + 1].start() if i + 1 < len(markers) else len(text)
            section = text[match.start():stop].strip()
            section = re.sub(r"\n---\s*$", "", section).rstrip()
            overview = re.search(r"^#{1,6}\s+故事概览\s*$", section, re.M)
            action = re.search(r"^#{1,6}\s+这一幕你要做的事\s*$", section, re.M)
            if not overview or not action:
                problems.append(f"第{i + 1}部分缺少概览或行动")
            elif overview.start() > action.start():
                problems.append(f"第{i + 1}部分概览与行动顺序错误")
            elif re.search(r"^#{1,6}\s+", section[action.end():], re.M):
                problems.append(f"第{i + 1}部分行动之后仍有新标题")
            if i < 4:
                leak = [word for word in ("红光", "清晨会", "献祭", "掌权者", "绝症") if word in section]
                if leak:
                    problems.append(f"第{i + 1}幕提前出现反转信息 " + "、".join(leak))
            label = CHAPTERS[i] if i < len(CHAPTERS) else f"未识别{i + 1}"
            (out / f"{i + 1:02d}-{label}.md").write_text(section + "\n", encoding="utf-8")
            body_end = overview.start() if overview else len(section)
            counts.append({"幕次": label, "正文汉字数": han(section[:body_end]), "含概览和行动": han(section)})
        item = {"文件": name, "总汉字数": han(text), "分幕": counts, "问题": problems}
        result["文件"].append(item)
        result["失败"].extend(name + " " + p for p in problems)
    result["合计汉字数"] = sum(book["总汉字数"] for book in result["文件"])
    QA.mkdir(parents=True, exist_ok=True)
    (QA / "四本结构与信息边界核对.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(result["失败"]))


if __name__ == "__main__":
    main()
