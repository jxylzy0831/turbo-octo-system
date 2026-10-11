from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path(r'C:\Users\Yu\.codex\plugins\cache\openai-primary-runtime\documents\26.1007.11041\skills\documents')
RUNTIME = Path(r'C:\Users\Yu\.cache\codex-runtimes\codex-primary-runtime\dependencies')
QA = ROOT / '质检/春日点名-第9版Word排版'
DOCX = QA / '春日点名-完整故事脉络-第9版-对外阅读版.docx'


def main():
    spec = importlib.util.spec_from_file_location('docx_renderer', SKILL / 'render_docx.py')
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    # Packaged renderer explicitly selects a native executable on Windows,
    # where the runtime has no LibreOffice bundle. Keep the resolver explicit.
    renderer._resolve_soffice = lambda: r'D:\Software\LibreOffice\program\soffice.exe'
    os.environ['PATH'] = str(RUNTIME / 'native/poppler/Library/bin') + os.pathsep + os.environ.get('PATH', '')
    sys.argv = ['render_docx.py', str(DOCX), '--output_dir', str(QA / '逐页预览'), '--dpi', '150', '--emit_pdf', '--verbose']
    renderer.main()


if __name__ == '__main__':
    main()
