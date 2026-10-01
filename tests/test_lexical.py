"""Тесты для analyzer.lexical."""

from analyzer.lexical import compute, top_words


def test_ttr_all_unique():
    """Все слова разные — TTR = 1.0."""
    result = compute("мама папа баба деда", "ru")
    assert result["lexical.ttr"] == 1.0


def test_ttr_all_same():
    """Все слова одинаковые — TTR низкий."""
    result = compute("мама мама мама мама", "ru")
    # 1 уникальное из 4 токенов
    assert result["lexical.ttr"] == 0.25


def test_hapax_all_unique():
    """Все слова встретились один раз — все hapax."""
    result = compute("мама папа баба деда", "ru")
    assert result["lexical.hapax_count"] == 4
    assert result["lexical.hapax_ratio"] == 1.0


def test_hapax_no_unique():
    """Все слова повторились — hapax = 0."""
    result = compute("мама мама папа папа", "ru")
    assert result["lexical.hapax_count"] == 0


def test_entropy_empty():
    """Пустой текст — нули, не падаем."""
    result = compute("", "ru")
    assert result["lexical.entropy_bits"] == 0.0


def test_top_words_returns_sorted():
    """top_words возвращает слова по убыванию частоты."""
    result = top_words("мама папа мама баба мама", n=3)
    assert result[0] == ("мама", 3)
    # Следующие два — папа и баба, порядок не важен (по 1 разу)
    assert len(result) == 3


def test_top_words_limit():
    """top_words соблюдает лимит n."""
    result = top_words("а б в г д е ж з", n=3)
    assert len(result) == 3