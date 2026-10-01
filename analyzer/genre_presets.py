"""Пресеты по жанрам текста.

Каждый жанр описывает, какие метрики важны для текстов этого типа,
и даёт краткую подсказку «на что смотреть».

Модуль не делает классификацию текста — он только показывает
пользователю релевантный набор метрик, если он уже знает жанр.
"""

GENRE_PRESETS = {
    "fiction": {
        "name": "🎨 Художественная проза",
        "description": (
            "Романы, рассказы, повести. Высокое лексическое разнообразие, "
            "описательность, разнообразие времён и синтаксиса."
        ),
        "key_metrics": [
            "lexical.ttr",
            "lexical.hapax_ratio",
            "morph.pos_adj_ratio",
            "morph.pos_adv_ratio",
            "morph.tense_past_ratio",
            "basic.avg_sentence_len_words",
            "syntax.avg_tree_depth",
            "morph.animacy_animate_ratio",
        ],
        "hints": [
            "TTR > 0.5 — богатая лексика, текст разнообразен.",
            "Доля прилагательных и наречий 15%+ — описательный стиль.",
            "Прошедшее время преобладает — повествование о событиях.",
            "Глубина дерева 2.5+ — сложный синтаксис, длинные периоды.",
        ],
    },
    "academic": {
        "name": "🎓 Научная статья",
        "description": (
            "Академические тексты, диссертации, монографии. "
            "Номинативный стиль, длинные предложения, терминология."
        ),
        "key_metrics": [
            "morph.pos_noun_ratio",
            "morph.case_gent_ratio",
            "morph.content_words_ratio",
            "basic.avg_sentence_len_words",
            "syntax.avg_tree_depth",
            "syntax.subordination_ratio",
            "lexical.rare_words_ratio",
            "lexical.coverage_top1000",
        ],
        "hints": [
            "Существительных 35%+ — номинативный стиль.",
            "Родительный падеж 25%+ — термины-связки («анализ данных»).",
            "Покрытие топ-1000 ниже 60% — узкоспециальная лексика.",
            "Подчинение 10%+ — иерархический синтаксис с придаточными.",
        ],
    },
    "news": {
        "name": "📰 Новость / журналистика",
        "description": (
            "Новостные заметки, репортажи. Простая лексика, короткие "
            "предложения, прошедшее время."
        ),
        "key_metrics": [
            "basic.avg_sentence_len_words",
            "basic.complex_words_ratio",
            "lexical.coverage_top1000",
            "morph.tense_past_ratio",
            "morph.pos_noun_ratio",
            "morph.pos_verb_ratio",
            "syntax.clauses_per_sentence",
            "lexical.avg_zipf",
        ],
        "hints": [
            "Средняя длина предложения 10-15 слов — стандарт для новостей.",
            "Покрытие топ-1000 выше 70% — текст на общеупотребительной лексике.",
            "Прошедшее время преобладает — событие уже произошло.",
            "Средняя частотность Zipf 4.5+ — простые слова.",
        ],
    },
    "legal": {
        "name": "⚖️ Юридический / деловой",
        "description": (
            "Договоры, законы, регламенты, корпоративная документация. "
            "Длинные предложения, канцеляризмы, пассив."
        ),
        "key_metrics": [
            "basic.avg_sentence_len_words",
            "basic.long_words_ratio",
            "syntax.subordination_ratio",
            "syntax.coordination_ratio",
            "morph.case_gent_ratio",
            "morph.pos_noun_ratio",
            "lexical.rare_words_ratio",
            "readability.ruts_sis_grade",
        ],
        "hints": [
            "Средняя длина предложения 25+ слов — типично для документов.",
            "Длинных слов 30%+ — тяжёлая лексика.",
            "Родительный падеж 30%+ — цепочки определений.",
            "SIS Grade 10+ — высокая сложность.",
        ],
    },
    "colloquial": {
        "name": "💬 Разговорный / соцсети",
        "description": (
            "Посты, твиты, комментарии, диалоги. Короткие предложения, "
            "местоимения, частицы, простая лексика."
        ),
        "key_metrics": [
            "basic.avg_sentence_len_words",
            "basic.monosyllabic_ratio",
            "lexical.coverage_top100",
            "morph.pos_pron_ratio",
            "morph.pos_part_ratio",
            "morph.tense_present_ratio",
            "syntax.coordination_ratio",
            "lexical.avg_zipf",
        ],
        "hints": [
            "Средняя длина предложения < 12 слов — короткие фразы.",
            "Местоимений 10%+ — личный стиль изложения.",
            "Настоящее время преобладает — о текущем моменте.",
            "Сочинение >> подчинение — «плоский» синтаксис.",
        ],
    },
    "technical": {
        "name": "🔧 Техническая документация",
        "description": (
            "Инструкции, руководства, API-документация. "
            "Императив, короткие предложения, специальная лексика."
        ),
        "key_metrics": [
            "basic.avg_sentence_len_words",
            "morph.pos_verb_ratio",
            "morph.pos_noun_ratio",
            "lexical.coverage_top1000",
            "lexical.rare_words_ratio",
            "syntax.coordination_ratio",
            "morph.tense_present_ratio",
            "readability.ruts_sis_grade",
        ],
        "hints": [
            "Глаголов 15%+ — активные инструкции.",
            "Настоящее время — «нажмите», «откройте».",
            "Средняя длина предложения 8-12 слов — короткие команды.",
            "Редких слов 15%+ — терминология.",
        ],
    },
}


def get_genre(genre_key: str) -> dict | None:
    """Возвращает описание жанра по ключу или None."""
    return GENRE_PRESETS.get(genre_key)