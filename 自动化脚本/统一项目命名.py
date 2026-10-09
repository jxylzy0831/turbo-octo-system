from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"垃圾箱", "垃圾桶", "临时存储", ".git", "node_modules", "dist", "__pycache__", "_tmp", "修图成品", "技能验证依赖", "skill-validation-deps"}
FIXED = {"AGENTS.md", "SKILL.md", "package.json", "package-lock.json", "tsconfig.json", "index.html", ".gitignore", ".gitkeep", "openai.yaml", "__init__.py", ".env", "photo.env.ps1", ".npmrc", "LICENSE", "NOTICE", "METADATA", "INSTALLER", "RECORD", "WHEEL", "REQUESTED", "top_level.txt"}
DIRS = {
    "analysis": "分析", "assets": "素材", "drafts": "草稿", "output": "成品", "qa": "质检",
    "scripts": "自动化脚本", "source": "原始资料", "originals": "原始文件", "stageflow": "舞台预演",
    "src": "源码", "ui": "界面", "audio": "音频", "data": "数据", "dialogue": "对话", "domain": "领域",
    "flow": "流程", "rendering": "渲染", "styles": "样式", "config": "配置", "docs": "文档",
    "references": "参考资料", "agents": "智能体配置", "photo": "修图工具", "prompts": "提示词",
    "concordance": "对照索引", "conversations": "会话记录", "extracted": "抽取资料",
    "extracted_pdfs": "抽取的便携文档文本", "reviews": "评审报告", "standards": "评分标准",
    "cover_refs": "封面参考", "template": "排版模板", "final": "成品渲染", "prompt_word_v1": "提示词文档渲染-第一版",
    "末日学校-20260917-v1": "末日学校-20260917-第一版",
    "末日学校-抵达互动-20260930-v1": "末日学校-抵达互动-20260930-第一版",
    "末日学校-抵达后互动-五人出场版-20260930-v2": "末日学校-抵达后互动-五人出场版-20260930-第二版",
    "第一幕人物分色-20260930-v1": "第一幕人物分色-20260930-第一版",
    "app": "应用", "emotional-design-20260916": "情感设计-20260916",
    "末日学校提示词参照-20261008-01a11a1e": "末日学校提示词参照-20261008-01a11a1e",
    "video_03eb80dd_frames": "视频帧_03eb80dd", "final-v3": "成品渲染-第三版", "final-v4": "成品渲染-第四版",
    "scripted-interaction-design": "互动设计技能", "scripted-interaction-design-v2": "互动设计技能第二版",
}
FILES = {
    "README.md": "项目说明.md", "main.ts": "主程序.ts", "vite-env.d.ts": "构建环境声明.d.ts",
    "PlaybackPanel.ts": "播放面板.ts", "AudioService.ts": "音频服务.ts", "World.ts": "世界.ts",
    "DialoguePresenter.ts": "对话展示.ts", "ThreeRoomView.ts": "三维房间视图.ts", "ActorView.ts": "人物视图.ts",
    "App.ts": "应用.ts", "ActionRunner.ts": "动作执行.ts", "SceneDirector.ts": "场景调度.ts",
    "Choreography.ts": "走位编排.ts", "types.ts": "类型.ts", "script.json": "演示流程.json",
    "app.css": "应用样式.css", "room.example.json": "房间配置示例.json", "actors.example.json": "人物配置示例.json",
    "import_v5.py": "导入旧版示例.py", "room-and-cues.md": "场景与提示.md", "mechanisms.md": "互动机制.md",
    "evidence-and-cases.md": "证据与案例.md", "design-templates.md": "设计模板.md",
    "act-2-3-interaction-skill.md": "第二三幕互动设计.md", "qingbai-act-2-3-interaction-skill.md": "青白第二三幕互动设计.md",
    "lmxs-odin-qiang.md": "流氓叙事互动样本.md", "learning-protocol.md": "学习流程.md",
    "interaction-record.md": "互动记录.md", "after-reading-icebreakers.md": "读本后破冰互动.md",
    "photographer-system.md": "摄影提示词.md", "analyze-system.md": "分析提示词.md",
    "Get-PhotoModels.ps1": "获取修图模型.ps1", "Edit-Photo.ps1": "修图.ps1", "photo_models.py": "修图模型.py",
    "photo_retouch.py": "照片修整.py", "photo.env.example.ps1": "修图环境示例.ps1",
    "extract_video_frames.js": "提取视频帧.js", "contact-sheet.jpg": "联系图.jpg", "desktop.png": "桌面版.png",
    "mobile.png": "移动版.png", "dialogue.png": "对话示意.png", "style.json": "样式.json",
    "阿奇封面-v1.png": "阿奇封面-第1版.png",
    "末日学校_母提示词_V12_独立会话版_20261008.md": "末日学校_母提示词_第12版_独立会话版_20261008.md",
    "末日学校_母提示词_v12_独立会话版.md": "末日学校_母提示词_第12版_独立会话版.md",
    "末日学校_母提示词_v11_植物疫病与金色麦田版.md": "末日学校_母提示词_第11版_植物疫病与金色麦田版.md",
    "末日学校_母提示词_v10_日常电影与人物冲突版.md": "末日学校_母提示词_第10版_日常电影与人物冲突版.md",
    "2026-10-05_skill-research.md": "2026-10-05_技能调研.md", "2026-10-08_codex-session.md": "2026-10-08_智能体会话.md",
    "2026-10-08_01a1190a-pull-latest-code.md": "2026-10-08_01a1190a-拉取最新代码.md",
    "2026-09-29_remote-pull.md": "2026-09-29_远程拉取.md",
    "pdf_text_extraction_summary.json": "便携文档文本提取摘要.json",
    "互动HTML呈现约定-20260930.md": "互动网页呈现约定-20260930.md",
    "manifest.json": "资源清单.json", "verification.txt": "核验说明.txt", "report.json": "核查报告.json",
}
SCRIPTS = {
    "convert_manual_pdfs.py": "转换参考手册PDF.py", "contact_sheets.py": "生成联系图.py",
    "build_school_portraits_20260917.py": "构建末日学校人物小传_20260917.py",
    "build_school_arrival_v2.py": "构建末日学校抵达互动第二版.py", "build_school_arrival_interaction.py": "构建末日学校抵达互动.py",
    "build_school_act1_long.py": "构建末日学校第一幕长时互动.py", "build_school_act1_human_v4.py": "构建末日学校第一幕自然对白第四版.py",
    "build_school_act1_g_v5.py": "构建末日学校第一幕人物深化第五版.py", "build_qingbai_editable_docx.py": "构建青白可编辑文档.py",
    "build_prompt_docx.py": "构建提示词文档.py", "build_concordance.py": "构建语料索引.py",
    "build_archie_docx.py": "构建阿奇角色本文档.py", "build_archie_combined_docx.py": "构建阿奇合订本文档.py",
    "build_act1_colored_transcript.py": "构建第一幕分色文稿.py", "act_statistics.py": "统计幕次.py",
    "verify_docx_text.py": "核对文档文本.py", "school_portraits_20260917.template.html": "末日学校人物小传模板.html",
    "render_converted_manuals.py": "渲染转换手册.py", "rasterize_pdf.py": "栅格化PDF.py",
    "qa_school_portraits_20260917.mjs": "质检末日学校人物小传.mjs", "qa_school_arrival_interaction.mjs": "质检末日学校抵达互动.mjs",
    "qa_relationship_html.mjs": "质检人物关系页面.mjs", "qa_act1_colored_transcript.mjs": "质检第一幕分色文稿.mjs",
    "ocr_qingbai_raster.ps1": "识别青白扫描件.ps1", "migrate_pdf_temp_20261002.ps1": "迁移PDF临时文件_20261002.ps1",
    "extract_docx_text.py": "提取文档文本.py", "export_docx_pdf.ps1": "导出文档PDF.ps1",
    "export_act1_after_reading_original.py": "导出读本后互动原文.py", "organize_rejected_drafts_20261009.ps1": "归档弃用旧稿_20261009.ps1",
    "ocr_winrt_pdf.ps1": "识别PDF文本.ps1", "organize_unused_20261002.ps1": "整理弃用文件_20261002.ps1",
    "pdf_find_pages.py": "查找PDF页面.py", "统一项目命名.py": "统一项目命名.py",
}
TEXT_EXT = {".md", ".py", ".ps1", ".mjs", ".js", ".ts", ".css", ".html", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".txt", ".xml"}


def new_name(name: str, parent: tuple[str, ...]) -> str:
    if name in FIXED or parent[:2] in (("source", "originals"), ("原始资料", "原始文件")):
        return name
    if parent[:2] in (("analysis", "conversations"), ("分析", "会话记录")):
        return name
    name = SCRIPTS.get(name, FILES.get(name, name))
    if name.startswith("page-") and name.endswith(".png") and name[5:-4].isdigit():
        return f"第{name[5:-4]}页.png"
    if name.startswith("frame-") and name.endswith(".png") and name[6:-4].isdigit():
        return f"帧{name[6:-4]}.png"
    changes = (("OCR", "文字识别"), ("Word", "文档"), ("Skill", "技能"), ("skill", "技能"),
               ("_v1", "_第1版"), ("_v2", "_第2版"), ("-v1", "-第1版"), ("-v2", "-第2版"),
               ("-v3", "-第3版"), ("-v4", "-第4版"), ("-v5", "-第5版"),
               ("_run2", "_第2次"), ("_run3", "_第3次"), ("_run4", "_第4次"),
               ("-run2", "-第2次"), ("-run3", "-第3次"), ("-run4", "-第4次"))
    for old, replacement in changes:
        name = name.replace(old, replacement)
    for old, replacement in (("AgentA", "评审员A"), ("AgentB", "创作者B"), ("PVP", "玩家对抗"),
                             ("PDF", "便携文档"), ("SHA256", "校验值")):
        name = name.replace(old, replacement)
    return name


def new_directory(name: str) -> str:
    mapped = DIRS.get(name, name)
    for old, replacement in (("_v1", "_第1版"), ("_v2", "_第2版"), ("-v1", "-第一版"),
                             ("-v2", "-第二版"), ("-v3", "-第三版"), ("-v4", "-第四版"),
                             ("-v5", "-第五版"), ("_run2", "_第2次"), ("_run3", "_第3次"),
                             ("_run4", "_第4次"), ("-run2", "-第2次"), ("-run3", "-第3次"),
                             ("-run4", "-第4次")):
        mapped = mapped.replace(old, replacement)
    return mapped


def scan():
    dirs, files = [], []
    for current, child_dirs, child_files in os.walk(ROOT, topdown=True):
        rel = Path(current).relative_to(ROOT)
        parts = rel.parts
        child_dirs[:] = [d for d in child_dirs if d not in SKIP]
        if parts[:2] in (("source", "originals"), ("原始资料", "原始文件")):
            child_dirs[:] = []
            child_files = []
        for item in child_dirs:
            old = rel / item if parts else Path(item)
            updated = new_directory(item)
            if updated != item:
                dirs.append((old, old.with_name(updated)))
        for item in child_files:
            old = rel / item if parts else Path(item)
            updated = new_name(item, parts)
            if updated != item:
                files.append((old, old.with_name(updated)))
    # Translate only the protected source directory labels; original files themselves are never opened or renamed.
    return dirs, files


def final_destination(old: Path, intermediate: Path, is_directory: bool) -> Path:
    parent = tuple(DIRS.get(part, part) for part in old.parts[:-1])
    parts = parent + (intermediate.name,)
    return Path(*parts)


def replace_paths(all_moves):
    replacements = {}
    components = {}
    for old, intermediate in all_moves:
        new = final_destination(old, intermediate, False)
        a, b = old.as_posix(), new.as_posix()
        replacements[a] = b
        replacements[a.replace("/", "\\")] = b.replace("/", "\\")
        if old.name != new.name:
            replacements[old.name] = new.name
        for left, right in zip(old.parts, new.parts):
            if left != right:
                components[left] = right
    for old, new in components.items():
        replacements[old + "/"] = new + "/"
        replacements[old + "\\"] = new + "\\"
        if old != "stageflow":
            replacements["'" + old + "'"] = "'" + new + "'"
            replacements['"' + old + '"'] = '"' + new + '"'
    replacements = sorted(replacements.items(), key=lambda pair: len(pair[0]), reverse=True)
    stem_moves = [(a.stem, b.stem) for a, b in all_moves
                  if a.suffix == b.suffix and a.stem != b.stem and a.suffix in {".ts", ".js", ".mjs", ".py", ".css"}]
    for current, child_dirs, child_files in os.walk(ROOT, topdown=True):
        rel = Path(current).relative_to(ROOT)
        child_dirs[:] = [d for d in child_dirs if d not in SKIP]
        if rel.parts[:2] in (("source", "originals"), ("原始资料", "原始文件"), ("analysis", "conversations"), ("分析", "会话记录")):
            child_dirs[:] = []
            continue
        for filename in child_files:
            if Path(filename).suffix.lower() not in TEXT_EXT and filename != ".gitignore":
                continue
            if filename in {".env", "photo.env.ps1"}:
                continue
            file_path = Path(current) / filename
            if file_path.resolve() == Path(__file__).resolve():
                continue
            try:
                raw = file_path.read_bytes()
                text = raw.decode("utf-8-sig")
            except (OSError, UnicodeDecodeError):
                continue
            changed = text
            for old, new in replacements:
                changed = changed.replace(old, new)
            changed = re.sub(r"(?<=[/'\"\\])page-(?=\d|\{|\*)", "第", changed)
            changed = re.sub(r"(?<=[/'\"\\])frame-(?=\d|\{|\*)", "帧", changed)
            changed = re.sub(r"(?<=[/'\"\\])contact-(?=\d|\{|\*)", "联系图-", changed)
            for old, new in stem_moves:
                # Change extensionless path/module specifiers and Python import names, not code identifiers.
                escaped = re.escape(old)
                changed = re.sub(r"(?<=[/\\])" + escaped + r"(?=(?:[./\\'\"]|$))", new, changed)
                changed = re.sub(r"(?m)(\bimport\s+)" + escaped + r"(\b)", r"\g<1>" + new + r"\2", changed)
            if changed != text:
                bom = raw.startswith(b"\xef\xbb\xbf")
                file_path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + changed.encode("utf-8"))


def repair_text_from_git():
    manifest_path = ROOT / "分析/项目中文命名迁移清单-20261009.json"
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout
    file_map, dir_map = {}, {}
    for raw_path in tracked.split(b"\0"):
        if not raw_path:
            continue
        old = raw_path.decode("utf-8")
        parts = Path(old).parts
        if old == "drafts/README.md":
            continue
        new_parts = tuple(new_directory(part) for part in parts[:-1]) + (new_name(parts[-1], parts[:-1]),)
        new = Path(*new_parts).as_posix()
        if new != old:
            file_map[old] = new
        for length in range(1, len(parts)):
            old_prefix = Path(*parts[:length]).as_posix()
            new_prefix = Path(*(new_directory(part) for part in parts[:length])).as_posix()
            if old_prefix != new_prefix:
                dir_map[old_prefix] = new_prefix
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["renamed_directories"] = [{"from": old, "to": new} for old, new in dir_map.items()]
    manifest["renamed_files"] = [{"from": old, "to": new} for old, new in file_map.items()]
    manifest["tracked_path_mapping_rebuilt_from_git"] = True
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    suffixes = TEXT_EXT | {".gitignore"}
    restored = []
    for old in [raw.decode("utf-8") for raw in tracked.split(b"\0") if raw]:
        parts = Path(old).parts
        if old == "drafts/README.md" or parts[:2] in (("source", "originals"), ("analysis", "conversations")):
            continue
        current = file_map.get(old)
        if current is None:
            for length in range(len(parts) - 1, 0, -1):
                prefix = Path(*parts[:length]).as_posix()
                if prefix in dir_map:
                    current = (Path(dir_map[prefix]) / Path(*parts[length:])).as_posix()
                    break
        if current is None:
            current = old
        if Path(old).suffix.lower() not in suffixes and Path(old).name != ".gitignore":
            continue
        target = ROOT / Path(current)
        if not target.is_file():
            continue
        blob = subprocess.run(["git", "show", "HEAD:" + old], cwd=ROOT, stdout=subprocess.PIPE, check=True).stdout
        target.write_bytes(blob)
        restored.append((old, current))

    components, replacements, stem_moves = {}, {}, []
    for old, new in dir_map.items():
        a, b = Path(old), Path(new)
        if len(a.parts) > 1:
            replacements[a.as_posix()] = b.as_posix()
            replacements[a.as_posix().replace("/", "\\")] = b.as_posix().replace("/", "\\")
        for left, right in zip(a.parts, b.parts):
            if left != right:
                components[left] = right
    for old, new in file_map.items():
        a, b = Path(old), Path(new)
        replacements[a.as_posix()] = b.as_posix()
        replacements[a.as_posix().replace("/", "\\")] = b.as_posix().replace("/", "\\")
        replacements[a.name] = b.name
        if a.suffix == b.suffix and a.stem != b.stem and a.suffix in {".ts", ".js", ".mjs", ".py", ".css"}:
            stem_moves.append((a.stem, b.stem))
    replacements = sorted(replacements.items(), key=lambda pair: len(pair[0]), reverse=True)
    changed_count = 0
    for current, child_dirs, child_files in os.walk(ROOT, topdown=True):
        rel = Path(current).relative_to(ROOT)
        child_dirs[:] = [d for d in child_dirs if d not in SKIP]
        if rel.parts[:2] in (("原始资料", "原始文件"), ("分析", "会话记录")):
            child_dirs[:] = []
            continue
        for filename in child_files:
            if Path(filename).suffix.lower() not in suffixes and filename != ".gitignore":
                continue
            if filename in {".env", "photo.env.ps1", "统一项目命名.py", "项目中文命名迁移清单-20261009.json"}:
                continue
            if filename in {"package.json", "package-lock.json"}:
                continue
            target = Path(current) / filename
            try:
                raw = target.read_bytes()
                text = raw.decode("utf-8-sig")
            except (OSError, UnicodeDecodeError):
                continue
            updated = text
            for old, new in replacements:
                updated = updated.replace(old, new)
            if filename not in {"package.json", "package-lock.json"}:
                for old, new in components.items():
                    updated = updated.replace(old + "/", new + "/").replace(old + "\\", new + "\\")
                lines = updated.splitlines(keepends=True)
                for index, line in enumerate(lines):
                    if re.search(r"\b(?:ROOT|root)\s*/|Join-Path\s|Path\(", line):
                        for old, new in components.items():
                            line = re.sub(r"(?<=[/'\"\\])" + re.escape(old) + r"(?=['\"])", new, line)
                    lines[index] = line
                updated = "".join(lines)
            if filename == "tsconfig.json":
                updated = updated.replace('"src"', '"源码"')
            updated = re.sub(r"(?<=[/'\"\\])page-(?=\d|\{|\*)", "第", updated)
            updated = re.sub(r"(?<=[/'\"\\])frame-(?=\d|\{|\*)", "帧", updated)
            updated = re.sub(r"(?<=[/'\"\\])contact-(?=\d|\{|\*)", "联系图-", updated)
            for old, new in stem_moves:
                escaped = re.escape(old)
                updated = re.sub(r"(?<=[/\\])" + escaped + r"(?=(?:[./\\'\"]|$))", new, updated)
                updated = re.sub(r"(?m)(\bimport\s+)" + escaped + r"(\b)", r"\g<1>" + new + r"\2", updated)
                updated = re.sub(r"(?m)(\bfrom\s+)" + escaped + r"(\s+import\b)", r"\g<1>" + new + r"\2", updated)
            if updated != text:
                bom = raw.startswith(b"\xef\xbb\xbf")
                target.write_bytes((b"\xef\xbb\xbf" if bom else b"") + updated.encode("utf-8"))
                changed_count += 1
    print(f"已从 HEAD 恢复 {len(restored)} 个受跟踪文本文件，再按路径边界更新了 {changed_count} 个文件。")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--repair-text-from-git", action="store_true")
    args = parser.parse_args()
    if args.repair_text_from_git:
        repair_text_from_git()
        return
    dirs, files = scan()
    plan = [(a, b) for a, b in dirs + files]
    targets = [str(b).casefold() for _, b in plan]
    if len(targets) != len(set(targets)):
        raise RuntimeError("目标路径重复，已停止。")
    for old, new in plan:
        if (ROOT / new).exists() and (ROOT / new) != (ROOT / old):
            raise FileExistsError(f"目标已存在：{new}")
    print(f"发现 {len(dirs)} 个目录、{len(files)} 个文件需要中文化。")
    remaining = []
    for current, child_dirs, child_files in os.walk(ROOT, topdown=True):
        rel = Path(current).relative_to(ROOT)
        parts = rel.parts
        child_dirs[:] = [d for d in child_dirs if d not in SKIP]
        if parts[:2] in (("source", "originals"), ("原始资料", "原始文件"),
                         ("analysis", "conversations"), ("分析", "会话记录")):
            child_dirs[:] = []
            continue
        for item in child_dirs:
            if re.search(r"[A-Za-z]", new_directory(item)):
                remaining.append(str(rel / item))
        for item in child_files:
            candidate = new_name(item, parts)
            if candidate not in FIXED and re.search(r"[A-Za-z]", Path(candidate).stem):
                remaining.append(str(rel / item) + " -> " + candidate)
    if remaining:
        print("仍有名称含拉丁字母（固定工具名或需补充中文名）：")
        print("\n".join(remaining[:100]))
    if not args.apply:
        for old, new in dirs:
            print(f"目录：{old} -> {new}")
        return
    protected_hashes = {}
    original_root = ROOT / "source/originals"
    if original_root.exists():
        for current, _, names in os.walk(original_root):
            for name in names:
                path = Path(current) / name
                protected_hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    replace_paths([(old, final_destination(old, new, False)) for old, new in plan])
    for old, new in sorted(files, key=lambda pair: len(pair[0].parts), reverse=True):
        (ROOT / old).rename(ROOT / new)
    for old, new in sorted(dirs, key=lambda pair: len(pair[0].parts), reverse=True):
        source, target = ROOT / old, ROOT / new
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            source.rename(target)
    updated_hashes = {}
    new_original_root = ROOT / "原始资料/原始文件"
    if new_original_root.exists():
        for current, _, names in os.walk(new_original_root):
            for name in names:
                path = Path(current) / name
                old_rel = path.relative_to(ROOT / "原始资料").as_posix()
                updated_hashes["source/" + old_rel.replace("原始文件/", "originals/", 1)] = hashlib.sha256(path.read_bytes()).hexdigest()
    if protected_hashes != updated_hashes:
        raise RuntimeError("原始资料哈希不一致，需立即检查。")
    manifest = {"date": "2026-10-09", "renamed_directories": [{"from": a.as_posix(), "to": final_destination(a, b, True).as_posix()} for a, b in dirs],
                "renamed_files": [{"from": a.as_posix(), "to": final_destination(a, b, False).as_posix()} for a, b in files],
                "original_files_sha256_unchanged": True, "protected_file_count": len(protected_hashes)}
    dest = ROOT / "分析/项目中文命名迁移清单-20261009.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已完成迁移：{dest.relative_to(ROOT)}；原始资料 {len(protected_hashes)} 个文件哈希一致。")


if __name__ == "__main__":
    main()
