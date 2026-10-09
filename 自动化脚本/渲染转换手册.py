from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = Path(
    r"C:\Users\Yu\.codex\plugins\cache\openai-primary-runtime\documents\26.909.11814\skills\documents\render_docx.py"
)
SOFFICE = Path(r"D:\Software\LibreOffice\program\soffice.exe")
POPPLER = Path(
    r"C:\Users\Yu\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin"
)


def main() -> None:
    spec = importlib.util.spec_from_file_location("docx_renderer", RENDERER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the document renderer")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    renderer._resolve_soffice = lambda: str(SOFFICE)
    os.environ["PATH"] = str(POPPLER) + os.pathsep + os.environ.get("PATH", "")
    temporary = ROOT / "临时存储" / "pdf_to_docx"
    docx_files = sorted((temporary / "converted_manuals").glob("*.docx"))
    output_root = temporary / "rendered_manuals"
    output_root.mkdir(parents=True, exist_ok=True)
    summary = []
    for index, path in enumerate(docx_files, 1):
        target = output_root / f"doc{index:02d}"
        target.mkdir(parents=True, exist_ok=True)
        sys.argv = [
            "render_docx.py",
            str(path),
            "--output_dir",
            str(target),
            "--width",
            "1000",
            "--height",
            "1400",
        ]
        renderer.main()
        pages = sorted(target.glob("第*.png"), key=lambda item: int(item.stem.split("-")[-1]))
        summary.append({"docx": path.name, "render_pages": len(pages), "render_dir": str(target.relative_to(ROOT))})
        print(f"{index}/{len(docx_files)}: {path.name} — {len(pages)} rendered pages", flush=True)
    (ROOT / "分析" / "外部组织者手册_文档渲染检查.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
