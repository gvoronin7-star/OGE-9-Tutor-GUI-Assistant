class Topic {
  final String id;
  final String title;
  final String article;

  const Topic({required this.id, required this.title, required this.article});

  factory Topic.fromJson(Map<String, dynamic> json) => Topic(
    id: json['id'] as String,
    title: json['title'] as String,
    article: json['article'] as String,
  );
}

class Chunk {
  final int id;
  final String text;
  final String? summary;
  final List<String> keywords;
  final int? page;
  final List<double> vector;

  const Chunk({
    required this.id,
    required this.text,
    required this.summary,
    required this.keywords,
    required this.page,
    required this.vector,
  });

  factory Chunk.fromJson(Map<String, dynamic> json) => Chunk(
    id: json['id'] as int,
    text: json['text'] as String,
    summary: json['summary'] as String?,
    keywords: (json['keywords'] as List?)?.cast<String>() ?? const [],
    page: json['page'] as int?,
    vector: (json['vector'] as List).map((v) => (v as num).toDouble()).toList(),
  );
}

class Question {
  final String topicId;
  final String topicTitle;
  final String type;
  final String question;
  final List<String> answers;
  final int correctAnswer;
  final String explanation;

  const Question({
    required this.topicId,
    required this.topicTitle,
    required this.type,
    required this.question,
    required this.answers,
    required this.correctAnswer,
    required this.explanation,
  });

  factory Question.fromJson(Map<String, dynamic> json) => Question(
    topicId: json['topic_id'] as String,
    topicTitle: json['topic_title'] as String,
    type: json['type'] as String,
    question: json['question'] as String,
    answers: (json['answers'] as List).cast<String>(),
    correctAnswer: json['correct_answer'] as int,
    explanation: json['explanation'] as String,
  );
}
