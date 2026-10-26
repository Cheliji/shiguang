"""矢量图标加载工具（UI 制作要求 #1：一律使用 Feather/Lucide SVG，禁止手画）。

SVG 默认是黑色线条，通过 QPainter 渲染后按指定颜色着色，以适配选中/普通等状态。
"""

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from shiguang.config import package_root

ICON_DIR = package_root() / "resources" / "icons"


def icon_path(name: str) -> Path:
    """返回图标文件路径，name 不含扩展名（如 "home"）。"""
    return ICON_DIR / f"{name}.svg"


@lru_cache(maxsize=128)
def _render_svg(path_str: str, color_hex: str, size: int) -> QPixmap:
    """把 SVG 渲染成指定颜色、指定边长（逻辑像素）的 QPixmap。"""
    renderer = QSvgRenderer(path_str)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, size, size))
    # SourceIn：仅保留 SVG 已绘制区域，填充目标颜色
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color_hex))
    painter.end()
    return pixmap


def colored_icon(name: str, color_hex: str, size: int = 24) -> QIcon:
    """加载图标并着色，返回 QIcon。"""
    return QIcon(_render_svg(str(icon_path(name)), color_hex, size))


def colored_pixmap(name: str, color_hex: str, size: int = 24) -> QPixmap:
    """加载图标并着色，返回 QPixmap（用于 QLabel 等场景）。"""
    return _render_svg(str(icon_path(name)), color_hex, size)
