"""
Правила фильтрации метрик по языку.
Некоторые метрики имеют смысл только для одного языка:
- Англоязычные формулы читабельности калиброваны под длину английских слогов
  и дают систематический сдвиг на русском (4-6 классов разницы).
- Русскоязычная библиотека ruts работает только с русским.
- Часть морфологических категорий отсутствует в одном из языков
  (падежи, вид, одушевлённость — в английском; PROPN, DET — в pymorphy3).
Модуль возвращает (visible, hidden) — две части отчёта.
UI показывает visible как обычно, а hidden — в раскрывающемся блоке
«Скрыто для этого языка», чтобы пользователь мог посмотреть, если хочет.
"""


# Паттерны: строка без * — точное совпадение ключа,
# строка с * в конце — префикс (совпадает с любым ключом, начинающимся с неё).
HIDE_FOR_RU = [
    # Англоязычные формулы читабельности.
    # Калиброваны под длину английских слогов, на русском дают
    # систематический сдвиг вниз (текст кажется «легче», чем есть).
    "readability.flesch_reading_ease*",
    "readability.flesch_kincaid_grade*",
    "readability.gunning_fog*",
    "readability.smog*",
    "readability.ari*",
    "readability.coleman_liau*",
    "readability.dale_chall*",

    # pymorphy3 не выделяет имена собственные и детерминативы
    # как отдельные классы — эти метрики всегда 0.
    "morph.pos_propn_ratio",
    "morph.pos_det_ratio",
]


HIDE_FOR_EN = [
    # ruts — русскоязычная библиотека, все её метрики для английского бессмысленны.
    "readability.ruts_*",

    # Категории, отсутствующие в английской морфологии.
    # spaCy для английского их не размечает — значения всегда 0.
    "morph.case_*",
    "morph.aspect_*",
    "morph.animacy_*",
    # Род в английском есть только у местоимений (he/she/it),
    # доля настолько мала, что метрика не несёт информации.
    "morph.gender_*",
]


def _matches(key: str, pattern: str) -> bool:
    """Проверяет, попадает ли ключ под паттерн."""
    if pattern.endswith("*"):
        return key.startswith(pattern[:-1])
    return key == pattern


def _is_hidden(key: str, patterns: list[str]) -> bool:
    """True, если ключ скрыт хотя бы одним из паттернов."""
    return any(_matches(key, p) for p in patterns)


def filter_by_lang(metrics: dict, lang: str) -> tuple[dict, dict]:
    """Разделяет метрики на (видимые, скрытые) для указанного языка.

    lang: 'ru' или 'en'. Для других языков возвращает (metrics, {}).
    """
    if lang == "ru":
        patterns = HIDE_FOR_RU
    elif lang == "en":
        patterns = HIDE_FOR_EN
    else:
        return metrics, {}

    visible = {}
    hidden = {}
    for key, value in metrics.items():
        if _is_hidden(key, patterns):
            hidden[key] = value
        else:
            visible[key] = value
    return visible, hidden


def explain_hidden(key: str, lang: str) -> str:
    """Возвращает короткое пояснение, почему метрика скрыта для языка.

    Используется в UI, чтобы пользователь понимал, почему метрики нет
    в основном отчёте.
    """
    if lang == "ru":
        if key.startswith("readability.") and not key.startswith("readability.ruts_"):
            if key != "readability.oborneva" and key != "readability.lix" and key != "readability.rix":
                return "Англоязычная формула. Калибрована под английские слоги."
        if key in ("morph.pos_propn_ratio", "morph.pos_det_ratio"):
            return "pymorphy3 не различает эту категорию — всегда 0."
    elif lang == "en":
        if key.startswith("readability.ruts_"):
            return "Метрика русскоязычной библиотеки ruts."
        if key.startswith(("morph.case_", "morph.aspect_", "morph.animacy_", "morph.gender_")):
            return "Категория отсутствует в английской морфологии."
    return "Метрика не применяется к этому языку."