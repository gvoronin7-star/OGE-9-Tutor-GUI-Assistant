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

  List<SearchResult> search(List<double> queryVector, {int topK = 5}) {
    final scored = chunks.map((c) {
      final rawScore = _cosine(queryVector, c.vector);
      return SearchResult(
        chunk: c,
        score: rawScore * _lengthConfidence(c.text),
      );
    }).toList();
    scored.sort((a, b) => b.score.compareTo(a.score));
    return scored.take(topK).toList(growable: false);
  }

  double _lengthConfidence(String text) {
    if (text.length >= _shortChunkChars) return 1.0;
    return text.length / _shortChunkChars;
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
