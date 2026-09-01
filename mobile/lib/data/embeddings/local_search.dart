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

  List<SearchResult> search(List<double> queryVector, {int topK = 5}) {
    final scored = chunks
        .map(
          (c) => SearchResult(chunk: c, score: _cosine(queryVector, c.vector)),
        )
        .toList();
    scored.sort((a, b) => b.score.compareTo(a.score));
    return scored.take(topK).toList(growable: false);
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
