import 'dart:math';
import 'dart:typed_data';

import 'package:flutter_onnxruntime/flutter_onnxruntime.dart';

import 'bert_tokenizer.dart';

/// Офлайн-эмбеддинг запроса через ONNX-версию rubert-tiny2.
///
/// Модель отдаёт `last_hidden_state` целиком (Фаза 2 не запекает
/// пулинг в граф, см. scripts/export_mobile_embedding_model.py) - CLS-
/// токен (позиция 0) и L2-нормализация делаются здесь, тем же способом,
/// что sentence-transformers для этой конкретной модели (пулинг по
/// CLS, не усреднение - см. 1_Pooling/config.json в кэше HuggingFace,
/// проверено в scripts/verify_mobile_embedding_model.py).
///
/// Использует `flutter_onnxruntime`, а не `onnxruntime` (изначальный
/// выбор) - тот пакет не обновлялся 2 года, его Android-модуль собран
/// под compileSdk 33, а его собственные транзитивные androidx-зависимости
/// (lifecycle 2.7.0 и др.) требуют 34+ - сборка падала на этом
/// несоответствии независимо от compileSdk самого приложения (это
/// метаданные, зашитые в уже опубликованный .aar, а не настройка,
/// которую можно переопределить со стороны потребителя).
class EmbeddingService {
  static const _modelAsset = 'assets/models/rubert_tiny2.int8.onnx';
  static const _vocabAsset = 'assets/models/vocab.txt';

  final OnnxRuntime _runtime = OnnxRuntime();
  OrtSession? _session;
  BertTokenizer? _tokenizer;

  Future<void> init() async {
    if (_session != null) return;
    _session = await _runtime.createSessionFromAsset(_modelAsset);
    _tokenizer = await BertTokenizer.loadFromAssets(_vocabAsset);
  }

  Future<List<double>> embed(String text) async {
    final session = _session;
    final tokenizer = _tokenizer;
    if (session == null || tokenizer == null) {
      throw StateError('EmbeddingService.init() must be awaited first');
    }

    final encoded = tokenizer.encode(text);
    final seqLen = encoded.inputIds.length;
    final shape = [1, seqLen];

    final inputIdsTensor = await OrtValue.fromList(
      Int64List.fromList(encoded.inputIds),
      shape,
    );
    final attentionMaskTensor = await OrtValue.fromList(
      Int64List.fromList(encoded.attentionMask),
      shape,
    );
    final tokenTypeIdsTensor = await OrtValue.fromList(
      Int64List.fromList(encoded.tokenTypeIds),
      shape,
    );

    Map<String, OrtValue>? outputs;
    try {
      outputs = await session.run({
        'input_ids': inputIdsTensor,
        'attention_mask': attentionMaskTensor,
        'token_type_ids': tokenTypeIdsTensor,
      });

      final hiddenState = await outputs['last_hidden_state']!.asList();
      final flat = _flattenLastHiddenState(hiddenState);
      return _clsPoolAndNormalize(flat, hiddenSize: flat.length ~/ seqLen);
    } finally {
      await inputIdsTensor.dispose();
      await attentionMaskTensor.dispose();
      await tokenTypeIdsTensor.dispose();
      if (outputs != null) {
        for (final value in outputs.values) {
          await value.dispose();
        }
      }
    }
  }

  /// `last_hidden_state` приходит как вложенные List (batch=1, seqLen,
  /// hiddenSize) - разворачивается в плоский список для удобства среза
  /// CLS-токена ниже.
  List<double> _flattenLastHiddenState(List value) {
    final batch = value[0] as List;
    final flat = <double>[];
    for (final tokenVector in batch) {
      for (final v in tokenVector as List) {
        flat.add((v as num).toDouble());
      }
    }
    return flat;
  }

  List<double> _clsPoolAndNormalize(
    List<double> flat, {
    required int hiddenSize,
  }) {
    final cls = flat.sublist(0, hiddenSize);
    var normSquared = 0.0;
    for (final v in cls) {
      normSquared += v * v;
    }
    final norm = normSquared > 0 ? sqrt(normSquared) : 1.0;
    return cls.map((v) => v / norm).toList(growable: false);
  }

  Future<void> dispose() async {
    await _session?.close();
    _session = null;
  }
}
