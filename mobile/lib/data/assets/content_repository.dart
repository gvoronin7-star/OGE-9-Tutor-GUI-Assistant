import 'dart:convert';

import 'package:flutter/services.dart' show rootBundle;

import '../../core/models.dart';

class ContentRepository {
  const ContentRepository();

  Future<List<Topic>> loadTopics() async {
    final raw = await rootBundle.loadString('assets/data/topics.json');
    final decoded = jsonDecode(raw) as List;
    return decoded
        .map((e) => Topic.fromJson(e as Map<String, dynamic>))
        .toList(growable: false);
  }

  Future<List<Question>> loadQuestions() async {
    final raw = await rootBundle.loadString('assets/data/questions.json');
    final decoded = jsonDecode(raw) as List;
    return decoded
        .map((e) => Question.fromJson(e as Map<String, dynamic>))
        .toList(growable: false);
  }
}
