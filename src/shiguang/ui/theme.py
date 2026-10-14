"""设计令牌（唯一取值来源，对齐 docs/UI设计文档.md §2）。

所有自定义组件禁止硬编码色值/尺寸，一律从本模块取。
"""


class Color:
    """色彩（§2.1）。"""

    # 基础色板
    BG_PRIMARY = "#F3F4F6"
    BG_SECONDARY = "#E5E7EB"
    BG_TERTIARY = "#D1D5DB"
    SURFACE = "#FFFFFF"
    SURFACE_HOVER = "#F9FAFB"
    SURFACE_ELEVATED = "#FFFFFF"

    # 主色系（Teal）
    PRIMARY = "#009FAA"
    PRIMARY_HOVER = "#00B4C0"
    PRIMARY_LIGHT = "#E6F7F8"
    PRIMARY_SUBTLE = "#B3E5E9"

    # 语义色
    TEXT_PRIMARY = "#1F2937"
    TEXT_SECONDARY = "#6B7280"
    TEXT_TERTIARY = "#9CA3AF"
    DANGER = "#EF4444"
    DANGER_LIGHT = "#FEE2E2"
    DANGER_BORDER = "#FECACA"
    WARNING = "#F59E0B"
    SUCCESS = "#10B981"
    SUCCESS_LIGHT = "#D1FAE5"
    STAR = "#FBBF24"
    STAR_EMPTY = "#D1D5DB"


class FontSize:
    """字号阶梯（§2.2），单位 px。"""

    PAGE_TITLE = 24
    PAGE_SUBTITLE = 14
    CARD_TITLE = 15
    BODY = 14
    AUXILIARY = 13
    TINY = 12
    NUMBER = 32


FONT_FAMILY = '"Segoe UI", "Microsoft YaHei UI", system-ui, sans-serif'
FONT_FAMILY_MONO = '"Cascadia Code", Consolas, monospace'


class Space:
    """间距（§2.3，4px 基准），单位 px。"""

    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32
    XXXL = 48


class Radius:
    """圆角（§2.4），单位 px。"""

    SM = 4
    MD = 8
    LG = 12
    XL = 16
    FULL = 9999


class Shadow:
    """阴影（§2.5），供 QSS / QGraphicsDropShadowEffect 使用。"""

    SM = "0 1px 2px rgba(0,0,0,0.04)"
    MD = "0 4px 12px rgba(0,0,0,0.06)"
    LG = "0 8px 24px rgba(0,0,0,0.08)"
    XL = "0 16px 48px rgba(0,0,0,0.12)"


class Duration:
    """动效时长（§2.6），单位 ms。"""

    HOVER = 150
    DIALOG = 200
    PAGE_SWITCH = 250
    PROGRESS = 400
    LIST_ITEM = 200


class Layout:
    """布局常量（§3）。"""

    NAV_WIDTH = 64
    NAV_BUTTON = 48
    TITLE_BAR_HEIGHT = 40
    PAGE_PADDING = 24
    WINDOW_WIDTH = 1100
    WINDOW_HEIGHT = 720
    WINDOW_MIN_WIDTH = 960
    WINDOW_MIN_HEIGHT = 640
