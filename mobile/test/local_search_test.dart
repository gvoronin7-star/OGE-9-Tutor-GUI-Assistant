import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/models.dart';
import 'package:mobile/data/embeddings/local_search.dart';

Chunk _chunk(String text, List<double> vector) => Chunk(
  id: text,
  text: text,
  summary: null,
  keywords: const [],
  page: null,
  vector: vector,
);

void main() {
  group('LocalSearch length damping', () {
    test('a long chunk outranks a short chunk with an identical raw cosine', () {
      // Both chunks use the exact same vector, so their raw cosine
      // similarity to the query is identical - only text length differs.
      // Without damping they'd tie; with it, the short one should rank lower.
      final query = [1.0, 0.0];
      final shortChunk = _chunk('а б в г д', [1.0, 0.02]); // 9 chars
      final longChunk = _chunk(
        'Общество — это совокупность людей, объединённых общими интересами, культурой и социальными связями.',
        [1.0, 0.02],
      ); // well over 80 chars

      final results = LocalSearch([
        shortChunk,
        longChunk,
      ]).search(query, topK: 2);

      expect(results.first.chunk.text, longChunk.text);
      expect(results.last.chunk.text, shortChunk.text);
      expect(results.first.score, greaterThan(results.last.score));
    });

    test('chunks at or above the length threshold are not damped', () {
      final query = [1.0, 0.0];
      final chunk = _chunk('x' * 80, [1.0, 0.0]); // exactly at the threshold

      final result = LocalSearch([chunk]).search(query, topK: 1).single;

      expect(result.score, closeTo(1.0, 1e-9));
    });

    test('a very short chunk is scaled down proportionally to its length', () {
      final query = [1.0, 0.0];
      // Raw cosine is 1.0 (identical direction); text is 8 chars, so the
      // damped score should be 8/80 = 0.1 of the raw cosine.
      final chunk = _chunk('задания:', [1.0, 0.0]);

      final result = LocalSearch([chunk]).search(query, topK: 1).single;

      expect(result.score, closeTo(0.1, 1e-9));
    });
  });
}
