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
