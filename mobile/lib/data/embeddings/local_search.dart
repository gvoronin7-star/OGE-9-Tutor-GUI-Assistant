import 'dart:math';

import '../../core/models.dart';

class SearchResult {
  final Chunk chunk;
  final double score;

  const SearchResult({required this.chunk, required this.score});
}

/// Косинусный поиск полным перебором - на 197 чанках x 312 измерений
/// (см. decisions/2026-09-01_flutter-mobile-app-concept-plan.md, Фаза 2)
/// ANN-индекс не нужен, полный перебор укладывается в единицы
/// миллисекунд на любом современном устройстве.
class LocalSearch {
  final List<Chunk> chunks;

  const LocalSearch(this.chunks);

  /// Чанки короче [_shortChunkChars] символов (заголовки страниц,
  /// пункты инструкций вида «задания 1, 15, 19...», «© ФГБНУ ФИПИ...»)
  /// систематически получают завышенный косинус почти на любой запрос
  /// — особенность CLS-пулинга на очень коротких текстах, а не
  /// признак релевантности (найдено вручную на реальном устройстве:
  /// «а б в г д» — 9 символов — стабильно входит в топ-5 результатов
  /// с cosine 0.72–0.83 независимо от темы запроса). Такие чанки не
  /// убираются из поиска целиком — иногда именно они самые релевантные
  /// («трудоустройство несовершеннолетних», 34 символа, тоже короткий,
  /// но по существу) — вместо этого их итоговый score линейно
  /// приглушается пропорционально длине текста, чтобы длинные
  /// содержательные чанки с сопоставимым сырым косинусом ранжировались
  /// выше.
  static const _shortChunkChars = 80;

  /// Методические/процедурные шаблоны из исходного PDF ФИПИ (списки
  /// номеров заданий вида «задания 1, 15, 19...», инструкции по подготовке
  /// «после изучения темы Х прорешать...», копирайт-плашки) - не короче
  /// порога длины выше, поэтому демпфирование по длине их не касается, но
  /// они не отвечают на содержательный вопрос по теме. Регулярка проверена
  /// на всём датасете из 157 чанков (см. decisions/decision-log.md,
  /// запись про качество офлайн-поиска) - размечает ~44% чанков, что на
  /// глаз соответствует реальной доле методического текста в источнике
  /// (методичка ФИПИ, не только предметный материал).
  static final _proceduralPattern = RegExp(
    r'©|фипи|фгбну|задани[а-яё]*\s*\d|тема\s*\d|после изучения темы|'
    r'прорешать в каждом варианте|бланке\s*№|советуем при подготовке|'
    r'легенде диаграммы',
  );

  List<SearchResult> search(List<double> queryVector, {int topK = 5}) {
    final scored = chunks.map((c) {
      final rawScore = _cosine(queryVector, c.vector);
      return SearchResult(
        chunk: c,
        score: rawScore * _lengthConfidence(c.text) * _proceduralConfidence(c.text),
      );
    }).toList();
    scored.sort((a, b) => b.score.compareTo(a.score));
    return scored.take(topK).toList(growable: false);
  }

  double _lengthConfidence(String text) {
    if (text.length >= _shortChunkChars) return 1.0;
    return text.length / _shortChunkChars;
  }

  /// Умеренный, не полный штраф - методический фрагмент всё ещё может
  /// всплыть, если по запросу реально нет ничего более содержательного,
  /// но проигрывает конкуренцию обычному предметному тексту сопоставимой
  /// сырой похожести.
  double _proceduralConfidence(String text) {
    return _proceduralPattern.hasMatch(text) ? 0.5 : 1.0;
  }

  double _cosine(List<double> a, List<double> b) {
    var dot = 0.0, normA = 0.0, normB = 0.0;
    for (var i = 0; i < a.length; i++) {
      dot += a[i] * b[i];
      normA += a[i] * a[i];
      normB += b[i] * b[i];
    }
    if (normA == 0 || normB == 0) return 0;
    return dot / (sqrt(normA) * sqrt(normB));
  }
}
