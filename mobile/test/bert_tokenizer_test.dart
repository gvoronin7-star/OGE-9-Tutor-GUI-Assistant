import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/data/embeddings/bert_tokenizer.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test(
    'matches the real HuggingFace tokenizer on the reference fixture',
    () async {
      final tokenizer = await BertTokenizer.loadFromAssets(
        'assets/models/vocab.txt',
      );

      final fixtureRaw = File(
        'test/fixtures/embedding_reference.json',
      ).readAsStringSync();
      final fixture = jsonDecode(fixtureRaw) as List;

      for (final entry in fixture) {
        final text = entry['text'] as String;
        final expectedIds = (entry['input_ids'] as List).cast<int>();

        final encoded = tokenizer.encode(text);

        expect(
          encoded.inputIds,
          expectedIds,
          reason: 'token ids mismatch for "$text"',
        );
        expect(encoded.attentionMask, List.filled(expectedIds.length, 1));
        expect(encoded.tokenTypeIds, List.filled(expectedIds.length, 0));
      }
    },
  );
}
