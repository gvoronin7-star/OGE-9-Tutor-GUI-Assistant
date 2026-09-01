import 'dart:math';
import 'dart:typed_data';

import 'package:flutter/services.dart' show rootBundle;
import 'package:onnxruntime/onnxruntime.dart';

import 'bert_tokenizer.dart';

/// Офлайн-эмбеддинг запроса через ONNX-версию rubert-tiny2.
///
/// Модель отдаёт `last_hidden_state` целиком (Фаза 2 не запекает
/// пулинг в граф, см. scripts/export_mobile_embedding_model.py) - CLS-
/// токен (позиция 0) и L2-нормализация делаются здесь, тем же способом,
/// что sentence-transformers для этой конкретной модели (пулинг по
/// CLS, не усреднение - см. 1_Pooling/config.json в кэше HuggingFace,
/// проверено в scripts/verify_mobile_embedding_model.py).
class EmbeddingService {
  static const _modelAsset = 'assets/models/rubert_tiny2.int8.onnx';
  static const _vocabAsset = 'assets/models/vocab.txt';

  OrtSession? _session;
  BertTokenizer? _tokenizer;

  Future<void> init() async {
    if (_session != null) return;

    OrtEnv.instance.init();

    final modelBytes = (await rootBundle.load(
      _modelAsset,
    )).buffer.asUint8List();
    _session = OrtSession.fromBuffer(modelBytes, OrtSessionOptions());
    _tokenizer = await BertTokenizer.loadFromAssets(_vocabAsset);
  }

  Future<List<double>> embed(String text) async {
    if (_session == null || _tokenizer == null) {
      throw StateError('EmbeddingService.init() must be awaited first');
    }

    final encoded = _tokenizer!.encode(text);
    final seqLen = encoded.inputIds.length;
    final shape = [1, seqLen];

    final inputIdsTensor = OrtValueTensor.createTensorWithDataList(
      Int64List.fromList(encoded.inputIds),
      shape,
    );
    final attentionMaskTensor = OrtValueTensor.createTensorWithDataList(
      Int64List.fromList(encoded.attentionMask),
      shape,
    );
    final tokenTypeIdsTensor = OrtValueTensor.createTensorWithDataList(
      Int64List.fromList(encoded.tokenTypeIds),
      shape,
    );

    try {
      final outputs = await _session!.runAsync(OrtRunOptions(), {
        'input_ids': inputIdsTensor,
        'attention_mask': attentionMaskTensor,
        'token_type_ids': tokenTypeIdsTensor,
      });

      final hiddenState = outputs?.first?.value;
      final flat = _flattenLastHiddenState(hiddenState, seqLen);
      for (final output in outputs ?? <OrtValue?>[]) {
        output?.release();
      }
      return _clsPoolAndNormalize(flat, hiddenSize: flat.length ~/ seqLen);
    } finally {
      inputIdsTensor.release();
      attentionMaskTensor.release();
      tokenTypeIdsTensor.release();
    }
  }

  /// `last_hidden_state` приходит как вложенные List (batch=1, seqLen,
  /// hiddenSize) - разворачивается в плоский список для удобства среза
  /// CLS-токена ниже.
  List<double> _flattenLastHiddenState(dynamic value, int seqLen) {
    final batch = value as List;
    final sequence = batch[0] as List;
    final flat = <double>[];
    for (final tokenVector in sequence) {
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

  void dispose() {
    _session?.release();
    _session = null;
  }
}
