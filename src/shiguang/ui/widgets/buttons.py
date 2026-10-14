"""按钮规范实现（UI 设计文档 §5.5）。"""

from PySide6.QtWidgets import QPushButton, QWidget

from shiguang.ui.icons import colored_icon
from shiguang.ui.theme import Color, FontSize

_PRIMARY_QSS = f"""
QPushButton {{
    background: {Color.PRIMARY}; color: #FFFFFF; border: none;
    border-radius: 8px; padding: 0 16px; font-size: {FontSize.BODY}px;
}}
QPushButton:hover {{ background: {Color.PRIMARY_HOVER}; }}
QPushButton:disabled {{ background: {Color.BG_TERTIARY}; color: {Color.TEXT_TERTIARY}; }}
"""

_SECONDARY_QSS = f"""
QPushButton {{
    background: {Color.SURFACE}; color: {Color.TEXT_PRIMARY};
    border: 1px solid {Color.BG_SECONDARY};
    border-radius: 8px; padding: 0 16px; font-size: {FontSize.BODY}px;
}}
QPushButton:hover {{ background: {Color.BG_PRIMARY}; }}
"""

_GHOST_QSS = f"""
QPushButton {{
    background: transparent; color: {Color.TEXT_SECONDARY}; border: none;
    border-radius: 8px; padding: 0 12px; font-size: {FontSize.BODY}px;
}}
QPushButton:hover {{ background: {Color.BG_PRIMARY}; }}
"""

_SUCCESS_QSS = f"""
QPushButton {{
    background: {Color.SUCCESS}; color: #FFFFFF; border: none;
    border-radius: 8px; padding: 0 24px; font-size: {FontSize.BODY}px; font-weight: 500;
}}
QPushButton:hover {{ background: #0DA271; }}
QPushButton:disabled {{ background: {Color.BG_TERTIARY}; color: {Color.TEXT_TERTIARY}; }}
"""


def primary_button(
    text: str, icon: str | None = None, parent: QWidget | None = None
) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setStyleSheet(_PRIMARY_QSS)
    btn.setFixedHeight(36)
    if icon:
        btn.setIcon(colored_icon(icon, "#FFFFFF", 16))
    return btn


def secondary_button(
    text: str, icon: str | None = None, parent: QWidget | None = None
) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setStyleSheet(_SECONDARY_QSS)
    btn.setFixedHeight(36)
    if icon:
        btn.setIcon(colored_icon(icon, Color.TEXT_PRIMARY, 16))
    return btn


def ghost_button(text: str, icon: str | None = None, parent: QWidget | None = None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setStyleSheet(_GHOST_QSS)
    btn.setFixedHeight(32)
    if icon:
        btn.setIcon(colored_icon(icon, Color.TEXT_SECONDARY, 16))
    return btn


def success_button(text: str, parent: QWidget | None = None) -> QPushButton:
    """归档确认按钮（§4.4.3：绿色，44px 高）。"""
    btn = QPushButton(text, parent)
    btn.setStyleSheet(_SUCCESS_QSS)
    btn.setFixedHeight(44)
    return btn
