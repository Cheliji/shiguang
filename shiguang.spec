# -*- mode: python ; coding: utf-8 -*-
"""拾光 PyInstaller 打包配置（onedir，无控制台窗口）。

用法：
    .venv/Scripts/python.exe -m PyInstaller shiguang.spec --noconfirm

产物：dist/拾光/拾光.exe

数据与 exe 解耦：数据库位于 %APPDATA%/Shiguang/shiguang.db，
更新 exe 不影响用户数据；新版本携带的 alembic 迁移脚本会在
首次启动时自动对现有数据库做增量升级（新增表/列，数据保留）。
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

# qfluentwidgets 的 qss/资源文件必须完整收集
qfw_datas, qfw_binaries, qfw_hidden = collect_all("qfluentwidgets")


def _tree(src: str, dest: str, exclude_suffixes: tuple[str, ...] = (".pyc",)) -> list[tuple[str, str]]:
    """把目录收集为 datas，跳过 __pycache__ 等无用文件。"""
    entries: list[tuple[str, str]] = []
    for p in Path(src).rglob("*"):
        if p.is_dir() or "__pycache__" in p.parts or p.suffix in exclude_suffixes:
            continue
        rel_dir = p.parent.relative_to(src)
        entries.append((str(p), str(Path(dest) / rel_dir)))
    return entries


datas = [
    *qfw_datas,
    # 应用资源（图标、样式表）
    *_tree("src/shiguang/resources", "shiguang/resources"),
    # alembic 迁移脚本目录（versions/*.py 由 alembic 按文件路径加载，必须以数据形式随包）
    *_tree("src/shiguang/db/migrations", "shiguang/db/migrations"),
    # alembic.ini（migration_runner 构造 Config 需要真实文件）
    ("alembic.ini", "."),
]

binaries = [*qfw_binaries]
hiddenimports = [*qfw_hidden, "logging.config", "logging.handlers"]

a = Analysis(
    ["src/shiguang/main.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "pytest-qt", "ruff"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="拾光",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI 应用，不弹控制台（调试打包问题时临时改为 True）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="拾光",
)
