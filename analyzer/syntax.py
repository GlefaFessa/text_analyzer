"""
Синтаксические метрики на основе дерева зависимостей spaCy.
Один код для русского и английского — spaCy даёт универсальную
разметку зависимостей (Universal Dependencies) для обоих языков.
Метрики:
- глубина дерева (вложенность);
- расстояние между зависимыми словами (когнитивная нагрузка);
- число клауз на предложение;
- доли подчинительных и сочинительных связей;
- доля непроективных зависимостей.
Модуль НЕ использует pymorphy3 — только spaCy.
"""

from statistics import mean

# Спаци-модели для двух языков.
# Импортируются лениво внутри функций — чтобы не тянуть torch,
# если работаем только с русским.
_NLP = {}


def _get_nlp(lang: str):
    """Ленивая загрузка spaCy-модели для указанного языка."""
    if lang not in ("ru", "en"):
        raise ValueError(f"Неподдерживаемый язык: {lang}")
    if lang not in _NLP:
        import spacy
        model_name = "ru_core_news_lg" if lang == "ru" else "en_core_web_trf"
        _NLP[lang] = spacy.load(model_name)
    return _NLP[lang]

# Типы зависимостей, которые начинают новую клаузу.
# Это упрощённое определение, но на практике работает хорошо.
CLAUSE_DEPS = {"ROOT", "advcl", "ccomp", "xcomp", "acl", "relcl"}

# Сочинительные связи — «плоские», равноправные.
COORD_DEPS = {"cc", "conj"}

# Подчинительные связи — иерархические, зависимые.
SUBORD_DEPS = {"mark", "advcl", "ccomp", "xcomp", "acl", "relcl"}



def _tree_depth(token, max_depth: int = 100) -> int:
    """Глубина токена в дереве: число шагов до ROOT.

    Идём от токена вверх по .head, пока не дойдём до корня
    (у которого head — он сам).
    """
    depth = 0
    current = token
    while current.head != current and depth < max_depth:
        depth += 1
        current = current.head
    return depth

def compute(text: str, lang: str = "ru") -> dict:
    """Синтаксические метрики. lang: 'ru' или 'en'."""
    nlp = _get_nlp(lang)
    doc = nlp(text)

    if not doc.has_annotation("DEP"):
        return _empty_result()

    sentences = list(doc.sents)
    n_sentences = len(sentences)
    tokens = [t for t in doc if t.is_alpha or t.is_punct]

    if n_sentences == 0 or not tokens:
        return _empty_result()

    # === Глубина дерева ===
    depths = [_tree_depth(t) for t in tokens]
    avg_depth = mean(depths)
    max_depth = max(depths)

    # === Расстояние до head ===
    distances = [abs(t.i - t.head.i) for t in tokens if t.head != t]
    avg_distance = mean(distances) if distances else 0.0
    max_distance = max(distances) if distances else 0

    # === Длина предложения в токенах ===
    sent_lengths = [len([t for t in s if t.is_alpha or t.is_punct]) for s in sentences]
    avg_sent_len = mean(sent_lengths) if sent_lengths else 0.0

    # === Клаузы ===
    clause_counts = []
    for s in sentences:
        n_clauses = sum(1 for t in s if t.dep_ in CLAUSE_DEPS)
        clause_counts.append(max(1, n_clauses))  # хотя бы одна клауза на предложение
    clauses_per_sent = mean(clause_counts) if clause_counts else 0.0

    # === Сочинение и подчинение ===
    n_tokens = len(tokens)
    n_coord = sum(1 for t in tokens if t.dep_ in COORD_DEPS)
    n_subord = sum(1 for t in tokens if t.dep_ in SUBORD_DEPS)

    # === Непроективные зависимости ===
    n_nonproj = sum(1 for t in tokens if _is_nonprojective(t))

    return {
        "syntax.sentences": n_sentences,
        "syntax.tokens": n_tokens,
        "syntax.avg_tree_depth": avg_depth,
        "syntax.max_tree_depth": max_depth,
        "syntax.avg_dependency_distance": avg_distance,
        "syntax.max_dependency_distance": max_distance,
        "syntax.avg_sentence_length": avg_sent_len,
        "syntax.clauses_per_sentence": clauses_per_sent,
        "syntax.subordination_ratio": n_subord / n_tokens if n_tokens else 0.0,
        "syntax.coordination_ratio": n_coord / n_tokens if n_tokens else 0.0,
        "syntax.nonprojective_ratio": n_nonproj / n_tokens if n_tokens else 0.0,
    }

def _is_nonprojective(token) -> bool:
    """Проверяет, является ли ребро token—head непроективным.

    Ребро (a, b) проективно, если все токены между a и b позиционно
    находятся в поддереве a или b. Если хотя бы один промежуточный токен
    имеет head за пределами отрезка [min(a.i, b.i), max(a.i, b.i)],
    ребро непроективно.
    """
    head = token.head
    if head == token:
        return False  # корень всегда проективен

    lo, hi = sorted((token.i, head.i))
    if hi - lo <= 1:
        return False  # соседние токены всегда проективны

    # Проверяем каждый токен между lo и hi
    for i in range(lo + 1, hi):
        t = token.doc[i]
        # Если head этого токена вне отрезка [lo, hi] — непроективность
        if not (lo <= t.head.i <= hi):
            return True
    return False


def _empty_result() -> dict:
    """Возвращает все синтаксические метрики со значением 0."""
    return {
        "syntax.sentences": 0,
        "syntax.tokens": 0,
        "syntax.avg_tree_depth": 0.0,
        "syntax.max_tree_depth": 0,
        "syntax.avg_dependency_distance": 0.0,
        "syntax.max_dependency_distance": 0,
        "syntax.avg_sentence_length": 0.0,
        "syntax.clauses_per_sentence": 0.0,
        "syntax.subordination_ratio": 0.0,
        "syntax.coordination_ratio": 0.0,
        "syntax.nonprojective_ratio": 0.0,
    }
