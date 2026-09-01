import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:mobile/data/embeddings/embedding_service.dart';

/// Реальный прогон ONNX-инференса (не mock) - integration_test запускает
/// это на настоящей платформе (здесь - Windows desktop, т.к. в этом
/// окружении нет Android-эмулятора), поэтому нативный биндинг
/// onnxruntime действительно исполняется, в отличие от `flutter test`.
/// Сверяет итоговый вектор с эталоном из
/// scripts/verify_mobile_embedding_model.py (sentence_transformers
/// напрямую) - допуск на расхождение от int8-квантизации.
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('on-device embedding matches the Python reference', (tester) async {
    final fixtureRaw = File(
      'test/fixtures/embedding_reference.json',
    ).readAsStringSync();
    final fixture = jsonDecode(fixtureRaw) as List;

    final service = EmbeddingService();
    await service.init();

    for (final entry in fixture) {
      final text = entry['text'] as String;
      final expected = (entry['expected_vector'] as List).cast<num>();

      final actual = await service.embed(text);

      expect(actual.length, expected.length, reason: 'dim mismatch for "$text"');
      final cosine = _cosine(actual, expected.map((v) => v.toDouble()).toList());
      expect(
        cosine,
        greaterThan(0.99),
        reason: 'cosine too low for "$text": $cosine',
      );
    }

    service.dispose();
  });
}

double _cosine(List<double> a, List<double> b) {
  var dot = 0.0, normA = 0.0, normB = 0.0;
  for (var i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  return dot / (sqrt(normA) * sqrt(normB));
}
