"""Тесты для analyzer.text_utils — очистка и токенизация."""

from analyzer.text_utils import clean, sentences, words


def test_clean_removes_bom():
    """BOM в начале текста должен исчезнуть."""
    text = "\ufeffПривет мир"
    assert clean(text) == "Привет мир"


def test_clean_removes_zero_width():
    """Zero-width символы (часто приходят из Word) должны исчезнуть."""
    text = "При\u200bвет\u200c мир"  # zero-width space + non-joiner
    assert clean(text) == "Привет мир"


def test_clean_keeps_normal_text():
    """Обычный текст не должен меняться."""
    text = "Мама мыла раму. Папа читал газету."
    assert clean(text) == text


def test_words_extracts_russian():
    """Слова на кириллице выделяются корректно."""
    assert words("Мама мыла раму") == ["Мама", "мыла", "раму"]


def test_words_extracts_english():
    """Слова на латинице выделяются корректно."""
    assert words("Hello world") == ["Hello", "world"]


def test_words_ignores_punctuation():
    """Знаки препинания и цифры не попадают в слова."""
    assert words("Hello, world! 123 test.") == ["Hello", "world", "test"]


def test_words_empty_text():
    """Пустой текст даёт пустой список."""
    assert words("") == []


def test_sentences_simple():
    """Два предложения разделяются корректно."""
    result = sentences("Первое предложение. Второе предложение.")
    assert len(result) == 2
    assert result[0] == "Первое предложение."


def test_sentences_with_question_and_exclamation():
    """Все конечные знаки работают."""
    text = "Что делать? Всё хорошо! Точка."
    assert len(sentences(text)) == 3


def test_sentences_no_punctuation():
    """Текст без знаков препинания — одно предложение."""
    result = sentences("Текст без знаков препинания")
    assert len(result) == 1