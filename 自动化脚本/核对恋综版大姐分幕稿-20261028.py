from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "草稿" / "春日恋综版-大姐个人本-20261028-第1版"
REPORT = ROOT / "质检" / "春日恋综版大姐本-20261028-第1版" / "分幕与信息边界核对.json"
NUMBERS = "一二三四五六"


def han_count(text):
    return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", text))


def main():
    files = sorted((DRAFT / "玩家分幕").glob("*.md"))
    result = {"检查类型": "分幕结构与可见文本静态核对", "文件": [], "失败": []}
    chapters = []
    for path in files:
        content = path.read_text(encoding="utf-8")
        title = content.splitlines()[0]
        chapter = re.search(r"第([一二三四五六])幕", title)
        is_tail = "尾声" in path.name
        overview = re.search(r"^#{1,6}\s+故事概览\s*$", content, re.M)
        action = re.search(r"^#{1,6}\s+这一幕你要做的事\s*$", content, re.M)
        body_end = overview.start() if overview else len(content)
        issues = []
        if not overview or not action:
            issues.append("缺故事概览或玩家行动")
        elif overview.start() > action.start():
            issues.append("概览与玩家行动顺序错误")
        elif re.search(r"^#{1,6}\s+", content[action.end():], re.M):
            issues.append("玩家行动之后仍有新章节")
        if chapter and not is_tail:
            number = NUMBERS.index(chapter.group(1)) + 1
            chapters.append(number)
            if number <= 4:
                forbidden = [word for word in ("红光", "献祭", "清晨会", "绝症", "掌权者") if word in content]
                if forbidden:
                    issues.append("前四幕提前出现反转词 " + "、".join(forbidden))
        item = {"文件": str(path.relative_to(ROOT)), "正文汉字数": han_count(content[:body_end]), "全文件汉字数": han_count(content), "尾声": is_tail, "问题": issues}
        result["文件"].append(item)
        result["失败"].extend([path.name + " " + issue for issue in issues])
    if sorted(chapters) != [1, 2, 3, 4, 5, 6]:
        result["失败"].append("未恰好取得六幕独立玩家文件")
    if sum(item["尾声"] for item in result["文件"]) != 1:
        result["失败"].append("未恰好取得一个独立现场后尾声")
    result["合计汉字数"] = sum(item["全文件汉字数"] for item in result["文件"])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(result["失败"]))


if __name__ == "__main__":
    main()
