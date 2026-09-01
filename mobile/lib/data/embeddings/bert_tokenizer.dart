import 'package:flutter/services.dart' show rootBundle;

/// WordPiece-токенизатор, повторяющий `transformers.BertTokenizer` для
/// rubert-tiny2 (`do_lower_case=false`, `strip_accents=false`) - на
/// Flutter нет готового пакета, совместимого с HuggingFace-токенизацией
/// этой модели, поэтому реализован вручную и сверен с эталонными
/// token_ids из `mobile/test/fixtures/embedding_reference.json`
/// (сгенерирован `scripts/verify_mobile_embedding_model.py` через
/// настоящий `AutoTokenizer`).
class BertTokenizer {
  static const clsToken = '[CLS]';
  static const sepToken = '[SEP]';
  static const padToken = '[PAD]';
  static const unkToken = '[UNK]';
  static const maxInputCharsPerWord = 200;

  final Map<String, int> _vocab;

  BertTokenizer(this._vocab);

  static Future<BertTokenizer> loadFromAssets(String assetPath) async {
    final raw = await rootBundle.loadString(assetPath);
    final lines = raw.split('\n');
    final vocab = <String, int>{};
    for (var i = 0; i < lines.length; i++) {
      final cleaned = lines[i].replaceAll('\r', '');
      if (cleaned.isEmpty && i == lines.length - 1) continue;
      vocab[cleaned] = i;
    }
    return BertTokenizer(vocab);
  }

  int get clsTokenId => _vocab[clsToken]!;
  int get sepTokenId => _vocab[sepToken]!;
  int get padTokenId => _vocab[padToken]!;
  int get unkTokenId => _vocab[unkToken]!;

  /// Возвращает (input_ids, attention_mask, token_type_ids) уже с
  /// [CLS]/[SEP] и усечением до maxLength.
  ({List<int> inputIds, List<int> attentionMask, List<int> tokenTypeIds})
  encode(String text, {int maxLength = 256}) {
    final wordPieceTokens = _tokenize(text);
    final budget = maxLength - 2; // под [CLS] и [SEP]
    final truncated = wordPieceTokens.length > budget
        ? wordPieceTokens.sublist(0, budget)
        : wordPieceTokens;

    final ids = <int>[
      clsTokenId,
      ...truncated.map((t) => _vocab[t] ?? unkTokenId),
      sepTokenId,
    ];

    return (
      inputIds: ids,
      attentionMask: List.filled(ids.length, 1),
      tokenTypeIds: List.filled(ids.length, 0),
    );
  }

  List<String> _tokenize(String text) {
    final result = <String>[];
    for (final word in _basicTokenize(text)) {
      result.addAll(_wordpieceTokenize(word));
    }
    return result;
  }

  /// Разбивка на "базовые" токены: по пробелам, затем каждый символ
  /// пунктуации - отдельный токен (как BertTokenizer.BasicTokenizer,
  /// без CJK-обработки - в текстах ФИПИ иероглифов не бывает).
  List<String> _basicTokenize(String text) {
    final cleaned = _cleanText(text);
    final tokens = <String>[];
    for (final whitespaceToken in cleaned.trim().split(RegExp(r'\s+'))) {
      if (whitespaceToken.isEmpty) continue;
      tokens.addAll(_splitOnPunctuation(whitespaceToken));
    }
    return tokens;
  }

  String _cleanText(String text) {
    final buffer = StringBuffer();
    for (final rune in text.runes) {
      if (rune == 0 || rune == 0xFFFD || _isControl(rune)) continue;
      buffer.writeCharCode(_isWhitespace(rune) ? 0x20 : rune);
    }
    return buffer.toString();
  }

  bool _isWhitespace(int rune) {
    if (rune == 0x20 || rune == 0x09 || rune == 0x0A || rune == 0x0D) {
      return true;
    }
    return RegExp(r'\s').hasMatch(String.fromCharCode(rune));
  }

  bool _isControl(int rune) {
    if (rune == 0x09 || rune == 0x0A || rune == 0x0D) return false;
    return (rune >= 0x00 && rune <= 0x1F) || (rune >= 0x7F && rune <= 0x9F);
  }

  bool _isPunctuation(int rune) {
    return (rune >= 33 && rune <= 47) ||
        (rune >= 58 && rune <= 64) ||
        (rune >= 91 && rune <= 96) ||
        (rune >= 123 && rune <= 126) ||
        RegExp(r'\p{P}', unicode: true).hasMatch(String.fromCharCode(rune));
  }

  List<String> _splitOnPunctuation(String word) {
    final result = <String>[];
    final current = StringBuffer();
    for (final rune in word.runes) {
      if (_isPunctuation(rune)) {
        if (current.isNotEmpty) {
          result.add(current.toString());
          current.clear();
        }
        result.add(String.fromCharCode(rune));
      } else {
        current.writeCharCode(rune);
      }
    }
    if (current.isNotEmpty) result.add(current.toString());
    return result;
  }

  List<String> _wordpieceTokenize(String word) {
    if (word.runes.length > maxInputCharsPerWord) {
      return [unkToken];
    }

    final outputTokens = <String>[];
    var start = 0;
    final chars = word.runes.toList();
    var isBad = false;

    while (start < chars.length) {
      var end = chars.length;
      String? currentSubstring;
      while (start < end) {
        var substring = String.fromCharCodes(chars.sublist(start, end));
        if (start > 0) substring = '##$substring';
        if (_vocab.containsKey(substring)) {
          currentSubstring = substring;
          break;
        }
        end--;
      }
      if (currentSubstring == null) {
        isBad = true;
        break;
      }
      outputTokens.add(currentSubstring);
      start = end;
    }

    return isBad ? [unkToken] : outputTokens;
  }
}
