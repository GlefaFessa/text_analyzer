"""
Морфологические метрики: части речи, падежи, время, вид глагола.
Русский: pymorphy3 (быстро, точно для русской морфологии).
Английский: spaCy en_core_web_trf (universal POS).
Все POS-метрики приводятся к единой схеме universal POS:
NOUN, PROPN, VERB, ADJ, ADV, PRON, DET, ADP, CCONJ, SCONJ, NUM,
PART, INTJ, AUX, X.
"""

from collections import Counter
from .text_utils import words

# Маппинг тегов pymorphy3 (русская система AOT) на universal POS.
# Используется для унификации метрик ru и en.
PYMORPHY_TO_UPOS = {
    "NOUN": "NOUN",
    "ADJF": "ADJ",   # полное прилагательное
    "ADJS": "ADJ",   # краткое прилагательное
    "COMP": "ADJ",   # компаратив
    "VERB": "VERB",
    "INFN": "VERB",  # инфинитив
    "PRTF": "VERB",  # причастие действительное
    "PRTS": "VERB",  # причастие страдательное
    "GRND": "VERB",  # деепричастие
    "ADVB": "ADV",
    "PRON": "PRON",
    "NUMR": "NUM",
    "PREP": "ADP",
    "CONJ": "CCONJ",
    "PRCL": "PART",
    "INTJ": "INTJ",
    "NPRO": "PRON",
}
# Список universal POS, которые мы считаем в отчёте.
# Порядок важен: он определяет порядок строк в выводе.
UPOS_LIST = [
    "NOUN", "PROPN", "VERB", "ADJ", "ADV",
    "PRON", "DET", "ADP", "CCONJ", "SCONJ",
    "NUM", "PART", "INTJ",
]
# Знаменательные части речи — используются для content/function ratio.
CONTENT_POS = {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}

_MORPH_RU = None


def _get_morph_ru():
    """
    Ленивая инициализация pymorphy3.MorphAnalyzer.
    Создаётся один раз при первом вызове, потом переиспользуется.
    Если бы мы писали `MorphAnalyzer()` в глобальной области,
    он загружался бы при любом импорте модуля — даже если работаем
    только с английским текстом.
    """
    global _MORPH_RU
    if _MORPH_RU is None:
        import pymorphy3
        _MORPH_RU = pymorphy3.MorphAnalyzer()
    return _MORPH_RU

def _upos_from_pymorphy(tag) -> str:
    """Преобразует тег pymorphy3 в universal POS. 'X' — не распознано."""
    pos = tag.POS  # строка вроде 'NOUN', 'ADJF', или None
    if pos is None:
        return "X"
    return PYMORPHY_TO_UPOS.get(pos, "X")

def _compute_ru(text: str) -> dict:
    """Русская морфология через pymorphy3."""
    morph = _get_morph_ru()
    tokens = [w.lower() for w in words(text)]

    if not tokens:
        return _empty_result()

    upos_counter = Counter()
    case_counter = Counter()
    number_counter = Counter()
    gender_counter = Counter()
    animacy_counter = Counter()
    aspect_counter = Counter()
    tense_counter = Counter()
    person_counter = Counter()
    lemmas = []

    for token in tokens:
        # parse() возвращает список вариантов разбора.
        # Первый — самый вероятный по частотному словарю.
        parses = morph.parse(token)
        if not parses:
            continue
        p = parses[0]

        upos = _upos_from_pymorphy(p.tag)
        upos_counter[upos] += 1
        lemmas.append(p.normal_form)

        # Категории есть не у всех слов: у предлога не бывает падежа,
        # у прилагательного не бывает времени. Поэтому добавляем в счётчик
        # только если категория реально присутствует (не None).
        if p.tag.case:
            case_counter[p.tag.case] += 1
        if p.tag.number:
            number_counter[p.tag.number] += 1
        if p.tag.gender:
            gender_counter[p.tag.gender] += 1
        if p.tag.animacy:
            animacy_counter[p.tag.animacy] += 1
        if p.tag.aspect:
            aspect_counter[p.tag.aspect] += 1
        if p.tag.tense:
            tense_counter[p.tag.tense] += 1
        if p.tag.person:
            person_counter[p.tag.person] += 1
    n = len(tokens)
    total_parsed = sum(upos_counter.values())
    unique_lemmas = set(lemmas)

    result = {
        "morph.tokens_parsed": total_parsed,
        "morph.lemma_count": len(unique_lemmas),
        "morph.lemma_ttr": len(unique_lemmas) / total_parsed if total_parsed else 0.0,
    }

    # Доли POS — от всех разобранных токенов.
    for pos in UPOS_LIST:
        key = f"morph.pos_{pos.lower()}_ratio"
        result[key] = upos_counter[pos] / total_parsed if total_parsed else 0.0

    # Content vs function words.
    content = sum(upos_counter[pos] for pos in CONTENT_POS)
    result["morph.content_words_ratio"] = content / total_parsed if total_parsed else 0.0
    result["morph.function_words_ratio"] = 1.0 - result["morph.content_words_ratio"]

    # Падежи — считаем от слов, у которых вообще есть падеж.
    # Иначе знаменатель включал бы предлоги и союзы, и доли бы занижались.
    n_case = sum(case_counter.values())
    for case_name in ("nomn", "gent", "datv", "accs", "ablt", "loct"):
        key = f"morph.case_{case_name}_ratio"
        result[key] = case_counter[case_name] / n_case if n_case else 0.0

    n_number = sum(number_counter.values())
    result["morph.number_singular_ratio"] = number_counter["sing"] / n_number if n_number else 0.0
    result["morph.number_plural_ratio"] = number_counter["plur"] / n_number if n_number else 0.0

    n_gender = sum(gender_counter.values())
    for g, name in (("masc", "masculine"), ("femn", "feminine"), ("neut", "neuter")):
        result[f"morph.gender_{name}_ratio"] = gender_counter[g] / n_gender if n_gender else 0.0

    n_anim = sum(animacy_counter.values())
    result["morph.animacy_animate_ratio"] = animacy_counter["anim"] / n_anim if n_anim else 0.0
    result["morph.animacy_inanimate_ratio"] = animacy_counter["inan"] / n_anim if n_anim else 0.0

    n_aspect = sum(aspect_counter.values())
    result["morph.aspect_perfective_ratio"] = aspect_counter["perf"] / n_aspect if n_aspect else 0.0
    result["morph.aspect_imperfective_ratio"] = aspect_counter["impf"] / n_aspect if n_aspect else 0.0

    n_tense = sum(tense_counter.values())
    for t, name in (("past", "past"), ("pres", "present"), ("futr", "future")):
        result[f"morph.tense_{name}_ratio"] = tense_counter[t] / n_tense if n_tense else 0.0

    n_person = sum(person_counter.values())
    for p, name in (("1per", "first"), ("2per", "second"), ("3per", "third")):
        result[f"morph.person_{name}_ratio"] = person_counter[p] / n_person if n_person else 0.0

    return result

def _empty_result() -> dict:
    """Возвращает все морфологические метрики со значением 0.

    Нужно для пустого текста — чтобы формат словаря не менялся
    между вызовами. Иначе потребитель (Streamlit, JSON-выгрузка)
    должен уметь обрабатывать 'нет ключа' и 'ключ есть, но 0'.
    Один формат — проще жизнь.
    """
    result = {
        "morph.tokens_parsed": 0,
        "morph.lemma_count": 0,
        "morph.lemma_ttr": 0.0,
        "morph.content_words_ratio": 0.0,
        "morph.function_words_ratio": 0.0,
    }
    for pos in UPOS_LIST:
        result[f"morph.pos_{pos.lower()}_ratio"] = 0.0
    for case_name in ("nomn", "gent", "datv", "accs", "ablt", "loct"):
        result[f"morph.case_{case_name}_ratio"] = 0.0
    for key in ("number_singular", "number_plural",
                "gender_masculine", "gender_feminine", "gender_neuter",
                "animacy_animate", "animacy_inanimate",
                "aspect_perfective", "aspect_imperfective",
                "tense_past", "tense_present", "tense_future",
                "person_first", "person_second", "person_third"):
        result[f"morph.{key}_ratio"] = 0.0
    return result

# spaCy возвращает морфологические признаки в формате Universal Dependencies
# (Case=Nom, Number=Sing, Tense=Past). Приводим их к тем же ключам,
# что использует pymorphy3 (nomn, sing, past). Так метрики ru и en
# называются одинаково — важно для единого отчёта.
SPACY_CASE_MAP = {
    "Nom": "nomn",
    "Gen": "gent",
    "Dat": "datv",
    "Acc": "accs",
    "Ins": "ablt",
    "Loc": "loct",
}
SPACY_NUMBER_MAP = {"Sing": "sing", "Plur": "plur"}
SPACY_GENDER_MAP = {"Masc": "masc", "Femn": "femn", "Neut": "neut"}
SPACY_TENSE_MAP = {"Past": "past", "Pres": "pres", "Fut": "futr"}
SPACY_PERSON_MAP = {"1": "1per", "2": "2per", "3": "3per"}

_NLP_EN = None


def _get_nlp_en():
    """Ленивая инициализация spaCy для английского.

    en_core_web_trf — тяжёлая модель (torch внутри), загружается 5–10 сек.
    Создаём один раз, кэшируем в модульной переменной.
    """
    global _NLP_EN
    if _NLP_EN is None:
        import spacy
        _NLP_EN = spacy.load("en_core_web_trf")
    return _NLP_EN

def _compute_en(text: str) -> dict:
    """Английская морфология через spaCy en_core_web_trf.

    В отличие от pymorphy3, spaCy сразу даёт universal POS — маппинг не нужен.
    Морфологические признаки (падеж, число, время) получаем из token.morph.
    Английский — аналитический язык: часть категорий (вид глагола,
    предложный падеж) отсутствует, соответствующие метрики будут нулевыми.
    """
    nlp = _get_nlp_en()
    doc = nlp(text)

    # Оставляем только буквенные токены — отбрасываем пунктуацию,
    # цифры, пробелы. Это согласуется с тем, как работает _compute_ru
    # (там words() тоже берёт только буквы).
    tokens = [t for t in doc if t.is_alpha]

    if not tokens:
        return _empty_result()

    upos_counter = Counter()
    case_counter = Counter()
    number_counter = Counter()
    gender_counter = Counter()
    tense_counter = Counter()
    person_counter = Counter()
    lemmas = []

    for t in tokens:
        upos_counter[t.pos_] += 1
        lemmas.append(t.lemma_.lower())

        # token.morph.get(...) возвращает список значений (обычно 0 или 1).
        # Итерируемся — безопаснее, чем брать [0].
        for v in t.morph.get("Case"):
            case_counter[SPACY_CASE_MAP.get(v, v)] += 1
        for v in t.morph.get("Number"):
            number_counter[SPACY_NUMBER_MAP.get(v, v)] += 1
        for v in t.morph.get("Gender"):
            gender_counter[SPACY_GENDER_MAP.get(v, v)] += 1
        for v in t.morph.get("Tense"):
            tense_counter[SPACY_TENSE_MAP.get(v, v)] += 1
        for v in t.morph.get("Person"):
            person_counter[SPACY_PERSON_MAP.get(v, v)] += 1

    total_parsed = sum(upos_counter.values())
    unique_lemmas = set(lemmas)

    result = {
        "morph.tokens_parsed": total_parsed,
        "morph.lemma_count": len(unique_lemmas),
        "morph.lemma_ttr": len(unique_lemmas) / total_parsed if total_parsed else 0.0,
    }

    for pos in UPOS_LIST:
        result[f"morph.pos_{pos.lower()}_ratio"] = (
            upos_counter[pos] / total_parsed if total_parsed else 0.0
        )

    content = sum(upos_counter[pos] for pos in CONTENT_POS)
    result["morph.content_words_ratio"] = content / total_parsed if total_parsed else 0.0
    result["morph.function_words_ratio"] = 1.0 - result["morph.content_words_ratio"]

    n_case = sum(case_counter.values())
    for case_name in ("nomn", "gent", "datv", "accs", "ablt", "loct"):
        result[f"morph.case_{case_name}_ratio"] = (
            case_counter[case_name] / n_case if n_case else 0.0
        )

    n_number = sum(number_counter.values())
    result["morph.number_singular_ratio"] = number_counter["sing"] / n_number if n_number else 0.0
    result["morph.number_plural_ratio"] = number_counter["plur"] / n_number if n_number else 0.0

    n_gender = sum(gender_counter.values())
    for g, name in (("masc", "masculine"), ("femn", "feminine"), ("neut", "neuter")):
        result[f"morph.gender_{name}_ratio"] = gender_counter[g] / n_gender if n_gender else 0.0

    n_anim = sum((0,))  # у английского нет категории одушевлённости
    result["morph.animacy_animate_ratio"] = 0.0
    result["morph.animacy_inanimate_ratio"] = 0.0

    # Английский не имеет грамматического вида (совершенный/несовершенный).
    # Значения Aspect в UD (Prog, Perf) — это не то же самое, что русский вид.
    result["morph.aspect_perfective_ratio"] = 0.0
    result["morph.aspect_imperfective_ratio"] = 0.0

    n_tense = sum(tense_counter.values())
    for t, name in (("past", "past"), ("pres", "present"), ("futr", "future")):
        result[f"morph.tense_{name}_ratio"] = tense_counter[t] / n_tense if n_tense else 0.0

    n_person = sum(person_counter.values())
    for p, name in (("1per", "first"), ("2per", "second"), ("3per", "third")):
        result[f"morph.person_{name}_ratio"] = person_counter[p] / n_person if n_person else 0.0

    return result

def compute(text: str, lang: str = "ru") -> dict:
    """Морфологические метрики. lang: 'ru' (pymorphy3) или 'en' (spaCy)."""
    if lang == "ru":
        return _compute_ru(text)
    if lang == "en":
        return _compute_en(text)
    raise ValueError(f"Неподдерживаемый язык: {lang}. Ожидается 'ru' или 'en'.")