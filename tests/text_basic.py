"""Тесты для analyzer.basic — счётные метрики."""

import pytest

from analyzer.basic import compute


def test_basic_word_count():
    """Простейший подсчёт слов."""
    result = compute("Мама мыла раму.", "ru")
    assert result["basic.words"] == 3


def test_basic_sentence_count():
    """Два предложения — два."""
    result = compute("Первое. Второе.", "ru")
    assert result["basic.sentences"] == 2


def test_basic_unique_words():
    """Повторы уменьшают число уникальных."""
    result = compute("мама мама папа", "ru")
    assert result["basic.words"] == 3
    assert result["basic.unique_words"] == 2


def test_basic_empty_text():
    """Пустой текст — все нули, не падаем."""
    result = compute("", "ru")
    assert result["basic.words"] == 0
    assert result["basic.sentences"] == 0
    assert result["basic.avg_word_len_chars"] == 0.0


def test_basic_invalid_lang():
    """Неподдерживаемый язык — ValueError."""
    with pytest.raises(ValueError):
        compute("text", "de")


def test_basic_avg_word_len():
    """Средняя длина слова — арифметика."""
    # Слова: "ма", "мыла", "раму" → длины 2, 4, 4 → среднее 3.33...
    result = compute("ма мыла раму", "ru")
    assert abs(result["basic.avg_word_len_chars"] - 10/3) < 0.01


def test_basic_all_keys_present():
    """Модуль возвращает все ожидаемые ключи."""
    result = compute("Тест.", "ru")
    expected = [
        "basic.chars_total",
        "basic.words",
        "basic.sentences",
        "basic.paragraphs",
        "basic.syllables",
        "basic.avg_word_len_chars",
        "basic.long_words_ratio",
        "basic.complex_words_ratio",
    ]
    for key in expected:
        assert key in result, f"Отсутствует ключ {key}"