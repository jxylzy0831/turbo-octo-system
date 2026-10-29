"""用项目隔离的文档转换器和 Codex 自带渲染脚本生成逐页质检图。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path.home() / '.cache/codex-runtimes/codex-primary-runtime'
DEPENDENCIES = RUNTIME / 'dependencies'
SKILL = RUNTIME / 'plugins/openai-primary-runtime/plugins/documents/skills/documents'
QA = ROOT / '质检/春日四位玩家个人本-20261014-排版第1版'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('人物', choices=['恩书', '知夏', '多允', '瑞真'])
    args = parser.parse_args()
    entries = json.loads((QA / '正文与来源核对.json').read_text(encoding='utf-8'))
    entry = next(item for item in entries if item['人物'] == args.人物)
    dependency = ROOT / '自动化脚本/文档渲染依赖'
    local_runtime = json.loads((dependency / '本地渲染运行时.json').read_text(encoding='utf-8'))
    soffice = Path(local_runtime['soffice'])
    assert soffice.is_file() and soffice.resolve().is_relative_to(dependency.resolve())
    temporary = QA / args.人物 / '渲染缓存'
    temporary.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(temporary)
    poppler = DEPENDENCIES / 'native/poppler/Library/bin'
    os.environ['PATH'] = str(poppler) + os.pathsep + os.environ.get('PATH', '')
    spec = importlib.util.spec_from_file_location('春日文档渲染器', SKILL / 'render_docx.py')
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    original_temporary_directory = tempfile.TemporaryDirectory

    def bounded_temporary_directory(*positional, **keywords):
        keywords['dir'] = str(temporary)
        keywords['ignore_cleanup_errors'] = True
        directory = original_temporary_directory(*positional, **keywords)
        assert Path(directory.name).resolve().is_relative_to(temporary.resolve())
        return directory

    # Windows 的帮助索引线程可能稍晚释放配置文件；清理失败不撤销已完成的页面。
    renderer.tempfile.TemporaryDirectory = bounded_temporary_directory
    # Windows 的 Codex 运行时不带 LibreOffice。只用校验后的项目隔离副本，
    # 不调用用户桌面安装，不向系统安装或注册应用。
    renderer._resolve_soffice = lambda: str(soffice)
    sys.argv = [
        'render_docx.py', str(ROOT / entry['文档']),
        '--output_dir', str(QA / args.人物 / '逐页预览'),
        '--dpi', '100', '--emit_pdf', '--verbose',
    ]
    renderer.main()


if __name__ == '__main__':
    main()
