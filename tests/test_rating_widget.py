"""RatingWidget 组件测试（T08）。"""

from shiguang.ui.widgets.rating_widget import RatingWidget


def test_set_score(qtbot):
    rating = RatingWidget()
    qtbot.addWidget(rating)
    rating.set_score(4)
    assert rating.score() == 4


def test_score_clamped(qtbot):
    rating = RatingWidget()
    qtbot.addWidget(rating)
    rating.set_score(9)
    assert rating.score() == 5


def test_click_sets_score_and_emits(qtbot):
    rating = RatingWidget(size=28)
    qtbot.addWidget(rating)
    fired = []
    rating.score_changed.connect(fired.append)
    # 第 3 颗星中心 x ≈ (28+8)*2 + 14
    rating._on_click((28 + 8) * 2 + 14)
    assert rating.score() == 3
    assert fired == [3]


def test_read_only_ignores_click(qtbot):
    rating = RatingWidget(read_only=True)
    qtbot.addWidget(rating)
    rating.set_score(4)
    rating._on_click(10)
    assert rating.score() == 4  # 未被点击改变


def test_score_label(qtbot):
    rating = RatingWidget(show_label=True)
    qtbot.addWidget(rating)
    rating.set_score(5)
    assert "完美达成" in rating.label.text()
    rating.set_score(1)
    assert "还需努力" in rating.label.text()


def test_hover_preview(qtbot):
    rating = RatingWidget(size=28)
    qtbot.addWidget(rating)
    rating._on_hover(5)  # 第一颗星
    assert rating._display_count() == 1
    rating._on_leave()
    assert rating._display_count() == 0
