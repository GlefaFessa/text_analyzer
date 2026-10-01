"""Общие утилиты для работы с текстом.

Токенизация — это то, что понадобится всем модулям метрик.
Собрать её в одном месте — значит избежать расхождений:
сегодня слово «не» одно, завтра — другое.
"""

import re

# Слово: последовательность букв (кириллица или латиница).
RE_WORD = re.compile(r"[А-Яа-яЁёA-Za-z]+")

# Предложение: непустой кусок, заканчивающийся .!?…
RE_SENTENCE = re.compile(r"[^.!?…]+[.!?…]+|[^.!?…]+$")

INVISIBLE = re.compile(r"[\ufeff\u200b-\u200d\u2060]")


def words(text: str) -> list[str]:
    """Список слов в порядке появления (с сохранением регистра)."""
    return RE_WORD.findall(text)


def sentences(text: str) -> list[str]:
    """Список предложений."""
    return [s.strip() for s in RE_SENTENCE.findall(text) if s.strip()]

def clean(text: str) -> str:
    """Убирает BOM и zero-width символы — мусор из Word/веба/копипаста."""
    return INVISIBLE.sub("", text)