"""只读 MSI 数据库并解出文件，不调用安装服务或修改系统注册。"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import subprocess
import time

import _msi


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / '自动化脚本/文档渲染依赖'
PACKAGE = TOOLS / 'LibreOffice_25.8.7_Win_x86-64.msi'
TARGET = TOOLS / 'LibreOffice_25.8.7'
STAGING = TOOLS / '柜文件解包'
EXPECTED = 'ecdb65e76f5e91dc198b8c8dce5b5d6e1eb12fea6023553e52b591afd10b619d'


def read_rows(database, table):
    view = database.OpenView(f'SELECT * FROM `{table}`')
    view.Execute(None)
    while row := view.Fetch():
        yield [row.GetString(index) for index in range(1, row.GetFieldCount() + 1)]


def extract_cabinet(stream_name, destination):
    msi = ctypes.WinDLL('msi.dll')
    signatures = {
        'MsiOpenDatabaseW': [wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.POINTER(wintypes.UINT)],
        'MsiDatabaseOpenViewW': [wintypes.UINT, wintypes.LPCWSTR, ctypes.POINTER(wintypes.UINT)],
        'MsiViewExecute': [wintypes.UINT, wintypes.UINT],
        'MsiViewFetch': [wintypes.UINT, ctypes.POINTER(wintypes.UINT)],
        'MsiRecordReadStream': [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)],
        'MsiCloseHandle': [wintypes.UINT],
    }
    for name, argtypes in signatures.items():
        function = getattr(msi, name)
        function.argtypes = argtypes
        function.restype = wintypes.UINT

    def require_success(code):
        if code:
            raise OSError(code, '只读MSI查询失败')

    handles = []
    try:
        database, view, row = wintypes.UINT(), wintypes.UINT(), wintypes.UINT()
        require_success(msi.MsiOpenDatabaseW(str(PACKAGE), None, ctypes.byref(database)))
        handles.append(database)
        query = f"SELECT `Data` FROM `_Streams` WHERE `Name`='{stream_name}'"
        require_success(msi.MsiDatabaseOpenViewW(database, query, ctypes.byref(view)))
        handles.append(view)
        require_success(msi.MsiViewExecute(view, 0))
        require_success(msi.MsiViewFetch(view, ctypes.byref(row)))
        handles.append(row)
        buffer = ctypes.create_string_buffer(4 * 1024 * 1024)
        with destination.open('wb') as output:
            while True:
                size = wintypes.DWORD(len(buffer))
                require_success(msi.MsiRecordReadStream(row, 1, buffer, ctypes.byref(size)))
                if not size.value:
                    break
                output.write(buffer.raw[:size.value])
    finally:
        for handle in reversed(handles):
            msi.MsiCloseHandle(handle)


def main():
    start = time.monotonic()
    with PACKAGE.open('rb') as handle:
        assert hashlib.file_digest(handle, 'sha256').hexdigest() == EXPECTED
    database = _msi.OpenDatabase(str(PACKAGE), _msi.MSIDBOPEN_READONLY)
    directories = {row[0]: (row[1], row[2]) for row in read_rows(database, 'Directory')}
    components = {row[0]: row[2] for row in read_rows(database, 'Component')}
    files = list(read_rows(database, 'File'))
    cabinets = [row[3] for row in read_rows(database, 'Media')]
    STAGING.mkdir(parents=True, exist_ok=True)
    for cabinet in cabinets:
        assert cabinet.startswith('#')
        path = TOOLS / cabinet[1:]
        extract_cabinet(cabinet[1:], path)
        print('柜文件已读出', path.stat().st_size, flush=True)
        result = subprocess.run(
            ['C:/Windows/System32/expand.exe', '-F:*', str(path), str(STAGING)],
            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        (TOOLS / '柜文件解包日志.log').write_bytes(result.stdout + result.stderr)
        assert result.returncode == 0, result.returncode

    cache = {'INSTALLLOCATION': Path()}

    def directory_path(identifier):
        if identifier in cache:
            return cache[identifier]
        parent, name = directories[identifier]
        if not parent:
            return None
        parent_path = directory_path(parent)
        if parent_path is None:
            return None
        name = name.split(':')[0].split('|')[-1]
        result = parent_path if name in ['', '.'] else parent_path / name
        cache[identifier] = result
        return result

    count = 0
    for file_id, component, name, *_ in files:
        relative = directory_path(components[component])
        if relative is None:
            continue
        source = STAGING / file_id
        destination = TARGET / relative / name.split('|')[-1]
        assert source.resolve().is_relative_to(TOOLS.resolve())
        assert destination.resolve().is_relative_to(TARGET.resolve())
        assert source.is_file() and not destination.exists(), (source, destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
        count += 1
    soffice = TARGET / 'program/soffice.exe'
    assert soffice.is_file()
    (TOOLS / '本地渲染运行时.json').write_text(json.dumps({
        'soffice': str(soffice),
        '来源': '核对官方SHA256后的MSI，只读数据库与CAB文件解包',
        '是否安装系统应用': False,
        '解包文件数': count,
        '耗时秒': round(time.monotonic() - start, 1),
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('项目隔离渲染依赖就绪', count, '文件', round(time.monotonic() - start, 1), '秒', flush=True)


if __name__ == '__main__':
    main()
