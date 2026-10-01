"""
Метрики читабельности.

Английский: используем textstat (Flesch, Fog, SMOG, ARI, Coleman-Liau...).
Русский: textstat.set_lang('ru') для тех формул, где есть поддержка,
         плюс собственные адаптации (Оборнева).

ВАЖНО: все формулы читабельности калиброваны под среднюю длину
предложения и среднюю длину слова. На текстах короче ~100 слов
результаты ненадёжны — это не баг, а природа метрик.
"""

import textstat

_LANG_MAP = {"ru": "ru_RU", "en": "en_US"}


def _prepare(lang: str) -> None:
    """Переключает textstat на нужный язык (влияет на слогоделение)."""
    textstat.set_lang(_LANG_MAP.get(lang, "en_US"))

def _oborneva(text: str) -> float:
    """Индекс читабельности Оборневой (адаптация Flesch для русского).

    Формула: 206.835 − 1.3×(слова/предложения) − 60.1×(слоги/слова)
    Шкала как у Flesch: чем выше — тем легче.
    """
    words_list = [w for w in text.split() if w]
    if not words_list:
        return 0.0

    sentences = max(1, textstat.sentence_count(text))
    words = len(words_list)
    syllables = textstat.syllable_count(text)

    asl = words / sentences           # average sentence length
    asw = syllables / words           # average syllables per word

    return 206.835 - 1.3 * asl - 60.1 * asw

def _ruts_metrics(text: str) -> dict:
    """Метрики читабельности через ruts (preset='plainrussian').

    Возвращает адаптированные под русский формулы:
    - ruts_* — версии классических формул (Flesch, Fog, SMOG, ARI, LIX...)
    - ruts_matskovsky_index — адаптация Gunning Fog
    - ruts_sis_grade — модель SIS (Солнышкина и др.)
    - ruts_consensus_grade — усреднённая оценка класса
    - ruts_reading_time_sec — время чтения в секундах

    nan и inf отбрасываются — многие формулы не работают на коротких текстах.
    """
    from ruts import ReadabilityStats

    try:
        raw = ReadabilityStats(text).get_stats()
    except Exception:
        return {}

    result = {}
    for key, value in raw.items():
        try:
            v = float(value)
        except (TypeError, ValueError):
            continue
        if v != v or v in (float("inf"), float("-inf")):
            continue
        result[f"readability.ruts_{key}"] = v
    return result

def compute(text: str, lang: str = "ru") -> dict:
    """Метрики читабельности. lang: 'ru' или 'en'."""
    _prepare(lang)

    if not text.strip():
        return {
            "readability.flesch_reading_ease": 0.0,
            "readability.flesch_kincaid_grade": 0.0,
            "readability.gunning_fog": 0.0,
            "readability.smog": 0.0,
            "readability.ari": 0.0,
            "readability.coleman_liau": 0.0,
            "readability.dale_chall": 0.0,
            "readability.lix": 0.0,
            "readability.rix": 0.0,
            "readability.oborneva": 0.0,
        }

    metrics = {
        "readability.flesch_reading_ease": textstat.flesch_reading_ease(text),
        "readability.flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
        "readability.gunning_fog": textstat.gunning_fog(text),
        "readability.smog": textstat.smog_index(text),
        "readability.ari": textstat.automated_readability_index(text),
        "readability.coleman_liau": textstat.coleman_liau_index(text),
        "readability.dale_chall": textstat.dale_chall_readability_score(text),
        "readability.lix": textstat.lix(text),
        "readability.rix": textstat.rix(text),
        "readability.oborneva": _oborneva(text),
    }
    if lang == "en":
        metrics["readability.dale_chall"] = textstat.dale_chall_readability_score(text) 

    # ruts калиброван под русский; для английского пропускаем
    if lang == "ru":
        metrics.update(_ruts_metrics(text))

    return metrics