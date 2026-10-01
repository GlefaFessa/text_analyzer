"""Тесты для analyzer.lang_detect."""

from analyzer.lang_detect import confidence, detect


def test_detect_russian():
    assert detect("Привет мир, как дела?") == "ru"


def test_detect_english():
    assert detect("Hello world, how are you?") == "en"


def test_detect_empty():
    assert detect("") == "unknown"


def test_detect_no_letters():
    """Только цифры и пунктуация — не определить."""
    assert detect("123 ... 456!") == "unknown"


def test_detect_mixed_russian_wins():
    """Кириллицы больше — ru."""
    assert detect("Привет мир hello") == "ru"


def test_confidence_full_russian():
    """Только кириллица — уверенность 1.0."""
    assert confidence("Привет мир") == 1.0


def test_confidence_mixed():
    """Равное количество букв — 0.5."""
    # 3 кириллицы, 3 латиницы (примерно)
    c = confidence("абв abc")
    assert 0.4 < c < 0.6