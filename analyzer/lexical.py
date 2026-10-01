"""
Лексические метрики: разнообразие словаря, частотные характеристики.
Все эти метрики отвечают на вопросы:
- насколько богат словарь текста?
- много ли слов, встретившихся один раз?
- насколько неравномерно распределены частоты?
"""
from functools import lru_cache
from statistics import mean

from wordfreq import top_n_list, zipf_frequency
import math
from collections import Counter
from .text_utils import words

@lru_cache(maxsize=None)
def _top_set(lang: str, n: int) -> frozenset[str]:
    """Топ-n слов языка, упакованные во frozenset для O(1)-проверки.

    lru_cache кэширует результат: топ-1000 для 'ru' считается один раз
    за всё время работы программы, потом берётся из памяти.
    """
    return frozenset(top_n_list(lang, n))

def compute(text: str, lang: str = "ru") -> dict:
    """Лексические метрики. lang не используется, но оставлен для совместимости."""
    # Токены = все слова в нижнем регистре.
    # Почему lower? Потому что «Это» и «это» — это одно слово.
    tokens = [w.lower() for w in words(text)]
    n = len(tokens)
    types = set(tokens)
    v = len(types)

    # === Покрытие топ-N частотных слов языка ===
    # Для каждого N считаем, какая доля токенов входит в топ-N.
    # Чем выше coverage_top1000, тем «проще» лексика.
    coverage = {}
    for top_n in (100, 1000, 5000, 10000):
        top = _top_set(lang, top_n)
        hits = sum(1 for w in tokens if w in top)
        coverage[f"lexical.coverage_top{top_n}"] = hits / n if n else 0.0

    # === Средняя частотность по Zipf ===
    # zipf_frequency(word, lang) возвращает число от 0 до ~8.
    # Чем выше — тем чаще слово в языке.
    zipf_values = [zipf_frequency(w, lang) for w in tokens]
    avg_zipf = mean(zipf_values) if zipf_values else 0.0

    # === Доля редких слов (zipf < 3) ===
    # Классический признак «сложной» лексики:
    # техническая терминология, редкие термины, авторские неологизмы.
    rare = [w for w in tokens if zipf_frequency(w, lang) < 3.0]
    rare_ratio = len(rare) / n if n else 0.0        

    # Пустой текст — отдельный случай. Все метрики = 0.
    if n == 0:
        return {
            "lexical.tokens": 0,
            "lexical.types": 0,
            "lexical.ttr": 0.0,
            "lexical.rttr": 0.0,
            "lexical.cttr": 0.0,
            "lexical.herdan": 0.0,
            "lexical.hapax_count": 0,
            "lexical.hapax_ratio": 0.0,
            "lexical.dis_count": 0,
            "lexical.entropy_bits": 0.0,
            "lexical.simpson_diversity": 0.0,
            "lexical.yule_k": 0.0,
        }

        # Type-Token Ratio: доля уникальных слов среди всех.
    
    # 1.0 = все слова разные; 0.1 = сплошные повторы.
    ttr = v / n

    # Root TTR: сглаживает зависимость TTR от длины текста.
    # Классическая проблема: чем длиннее текст, тем ниже TTR просто потому,
    # что новые слова встречаются всё реже. Корень частично компенсирует.
    rttr = v / math.sqrt(n)

    # Corrected TTR: вариант с дополнительным множителем 2.
    cttr = v / math.sqrt(2 * n)

    # Herdan's C: логарифмическая версия TTR.
    # log(v) / log(n) → стремится к 0.7–0.8 для естественных языков.
    herdan = math.log(v) / math.log(n) if v > 1 and n > 1 else 0.0

    # Частотный словарь: {слово: сколько раз встретилось}.
    freq = Counter(tokens)

    # Hapax legomena — слова, встретившиеся ровно один раз.
    # В лингвистике это индикатор «богатства» словаря: чем больше hapax,
    # тем разнообразнее лексика (при прочих равных).
    hapax = [w for w, c in freq.items() if c == 1]

    # Dis legomena — встретившиеся ровно дважды.
    dis = [w for w, c in freq.items() if c == 2]

    # Энтропия Шеннона: H = -sum(p_i * log2(p_i))
    # где p_i = частота слова / общее число слов.
    # 
    # Если все слова одинаковые (n=100, все 'а'): H = 0 — предсказуемо.
    # Если все слова разные: H максимальна — непредсказуемо.
    entropy = -sum((c / n) * math.log2(c / n) for c in freq.values())

    # Simpson's D = 1 - sum(n_i * (n_i - 1)) / (N * (N - 1))
    # где n_i — частота слова i.
    #
    # Числитель — число упорядоченных пар одинаковых слов.
    # Знаменатель — число всех упорядоченных пар.
    # Их отношение — вероятность «попасть в одно и то же слово дважды».
    # Вычитаем из 1 → получаем вероятность «разных слов».
    sum_same_pairs = sum(c * (c - 1) for c in freq.values())
    total_pairs = n * (n - 1)
    simpson_diversity = 1 - (sum_same_pairs / total_pairs) if total_pairs > 0 else 0.0

    # Yule's K = 10^4 * (sum(f_i^2) - N) / N^2
    # где f_i — частота каждого слова.
    #
    # 10^4 — нормировочный множитель, чтобы получить «человеческие» числа.
    # K = 0 — все слова встретились ровно один раз.
    # K растёт с ростом повторов.
    sum_sq = sum(c * c for c in freq.values())
    yule_k = 1e4 * (sum_sq - n) / (n * n)

    return {
        "lexical.tokens": n,
        "lexical.types": v,
        "lexical.ttr": ttr,
        "lexical.rttr": rttr,
        "lexical.cttr": cttr,
        "lexical.herdan": herdan,
        "lexical.hapax_count": len(hapax),
        "lexical.hapax_ratio": len(hapax) / v if v else 0.0,
        "lexical.dis_count": len(dis),
        "lexical.entropy_bits": entropy,
        "lexical.simpson_diversity": simpson_diversity,
        "lexical.yule_k": yule_k,
                **coverage,
        "lexical.avg_zipf": avg_zipf,
        "lexical.rare_words_ratio": rare_ratio,
    }

def top_words(text: str, n: int = 10) -> list[tuple[str, int]]:
    """Топ-n слов по частоте в самом тексте.

    Возвращает список пар (слово, частота), упорядоченный по убыванию.
    Это не метрика, а структурированный вывод — поэтому вынесено
    из compute, а не впихнуто в плоский словарь.
    """
    tokens = [w.lower() for w in words(text)]
    return Counter(tokens).most_common(n)