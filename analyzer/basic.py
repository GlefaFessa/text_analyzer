from .text_utils import words, sentences,clean

"""
Базовые счётные метрики.
Всё, что можно посчитать регулярками и арифметикой:
символы, слова, предложения, абзацы, слоги, средние длины.
Не требует spaCy, Natasha или других тяжёлых зависимостей.
"""

import re
from statistics import mean
import pyphen  # слогоделение; уже установлен вместе с textstat

_PYPHEN = {
    "ru": pyphen.Pyphen(lang="ru_RU"),
    "en": pyphen.Pyphen(lang="en_US"),
}

# Слово: последовательность букв (кириллица или латиница).
RE_WORD = re.compile(r"[А-Яа-яЁёA-Za-z]+")
# Предложение: непустой кусок текста, заканчивающийся .!?…
RE_SENTENCE = re.compile(r"[^.!?…]+[.!?…]+|[^.!?…]+$")
# Знаки препинания: всё, что не буква, не цифра и не пробел.
RE_PUNCT = re.compile(r"[^\w\s]")
# Абзац: одна или несколько непустых строк подряд.
RE_PARAGRAPH = re.compile(r"\n\s*\n")

def _words(text: str) -> list[str]:
    """Возвращает список слов (без цифр и пунктуации)."""
    return RE_WORD.findall(text)
def _sentences(text: str) -> list[str]:
    """Возвращает список предложений (грубо, без учёта сокращений)."""
    return [s.strip() for s in RE_SENTENCE.findall(text) if s.strip()]
def _paragraphs(text: str) -> list[str]:
    """Абзацы — блоки, разделённые пустой строкой."""
    return [p.strip() for p in RE_PARAGRAPH.split(text) if p.strip()]
def _count_syllables(words: list[str], lang: str) -> int:
    """Сумма слогов во всех словах через словарь pyphen."""
    dic = _PYPHEN[lang]
    total = 0
    for w in words:
        # insert hyphenation marks: "при-мер" → 2 слога
        hyphenated = dic.inserted(w.lower())
        if hyphenated:
            total += hyphenated.count("-") + 1
        else:
            total += 1  # не смогли разбить — считаем как один
    return total

def compute(text: str, lang: str = "ru") -> dict:
    """Считает базовые счётные метрики. lang: 'ru' или 'en'."""
    if lang not in _PYPHEN:
        raise ValueError(f"Поддерживаются только языки: {list(_PYPHEN)}")

    text = clean(text)              # если добавили clean()
    ws = words(text)                # ← было words = words(text)
    sents = sentences(text)         # ← аналогично
    paragraphs = _paragraphs(text)

    word_lengths = [len(w) for w in ws]
    sentence_lengths = [len(words(s)) for s in sents]

    syllables = _count_syllables(ws, lang)

    long_words = [w for w in ws if len(w) >= 7]
    complex_words = [w for w in ws if _count_syllables([w], lang) >= 3]
    mono_words = [w for w in ws if _count_syllables([w], lang) == 1]

    return {
        "basic.chars_total": len(text),
        "basic.chars_no_spaces": len(re.sub(r"\s", "", text)),
        "basic.letters": sum(c.isalpha() for c in text),
        "basic.digits": sum(c.isdigit() for c in text),
        "basic.punctuation": len(RE_PUNCT.findall(text)),
        "basic.spaces": sum(c.isspace() for c in text),
        "basic.words": len(ws),
        "basic.unique_words": len({w.lower() for w in ws}),
        "basic.sentences": len(sents),
        "basic.paragraphs": len(paragraphs),
        "basic.syllables": syllables,

        "basic.avg_word_len_chars": mean(word_lengths) if word_lengths else 0.0,
        "basic.avg_word_len_syllables": syllables / len(ws) if ws else 0.0,
        "basic.avg_sentence_len_words": mean(sentence_lengths) if sentence_lengths else 0.0,
        "basic.avg_words_per_paragraph": len(ws) / len(paragraphs) if paragraphs else 0.0,

        "basic.long_words_ratio": len(long_words) / len(ws) if ws else 0.0,
        "basic.complex_words_ratio": len(complex_words) / len(ws) if ws else 0.0,
        "basic.monosyllabic_ratio": len(mono_words) / len(ws) if ws else 0.0,
    }

