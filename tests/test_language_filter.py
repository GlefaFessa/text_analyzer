"""Тесты для analyzer.language_filter."""

from analyzer.language_filter import filter_by_lang


def test_filter_ru_removes_english_readability():
    """Для русского английские формулы читабельности скрыты."""
    metrics = {
        "readability.flesch_reading_ease": 68.0,
        "readability.ruts_flesch_reading_easy": 61.0,
        "basic.words": 100,
    }
    visible, hidden = filter_by_lang(metrics, "ru")
    assert "readability.flesch_reading_ease" in hidden
    assert "readability.ruts_flesch_reading_easy" in visible
    assert "basic.words" in visible


def test_filter_en_removes_ruts():
    """Для английского ruts-метрики скрыты."""
    metrics = {
        "readability.flesch_reading_ease": 68.0,
        "readability.ruts_flesch_reading_easy": 61.0,
    }
    visible, hidden = filter_by_lang(metrics, "en")
    assert "readability.ruts_flesch_reading_easy" in hidden
    assert "readability.flesch_reading_ease" in visible


def test_filter_en_removes_case():
    """Для английского падежи скрыты."""
    metrics = {
        "morph.case_nomn_ratio": 0.3,
        "morph.pos_noun_ratio": 0.3,
    }
    visible, hidden = filter_by_lang(metrics, "en")
    assert "morph.case_nomn_ratio" in hidden
    assert "morph.pos_noun_ratio" in visible


def test_filter_unknown_lang():
    """Неизвестный язык — ничего не фильтруется."""
    metrics = {"a.b": 1, "c.d": 2}
    visible, hidden = filter_by_lang(metrics, "de")
    assert visible == metrics
    assert hidden == {}