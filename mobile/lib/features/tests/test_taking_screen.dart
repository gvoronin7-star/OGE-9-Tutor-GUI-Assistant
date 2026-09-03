import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models.dart';
import '../../core/providers.dart';

class TestTakingScreen extends ConsumerStatefulWidget {
  final String topicId;

  const TestTakingScreen({super.key, required this.topicId});

  @override
  ConsumerState<TestTakingScreen> createState() => _TestTakingScreenState();
}

class _TestTakingScreenState extends ConsumerState<TestTakingScreen> {
  int _currentIndex = 0;
  int _score = 0;
  int? _selectedAnswer;
  bool _answered = false;
  final List<AnsweredQuestion> _reviewLog = [];
  final Stopwatch _stopwatch = Stopwatch()..start();
  Timer? _ticker;
  Duration _elapsed = Duration.zero;

  List<Question>? _questions;
  String? _loadError;

  @override
  void initState() {
    super.initState();
    _ticker = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() => _elapsed = _stopwatch.elapsed);
    });
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadQuestions());
  }

  Future<void> _loadQuestions() async {
    final topics = await ref.read(topicsProvider.future);
    final topic = topics.firstWhere((t) => t.id == widget.topicId);

    if (ref.read(serverModeEnabledProvider)) {
      try {
        final testData = await ref
            .read(apiClientProvider)
            .generateTest(topic.title);
        final questions = _parseServerQuestions(
          testData,
          topic.id,
          topic.title,
        );
        if (!mounted) return;
        setState(() => _questions = questions);
        return;
      } catch (_) {
        if (!mounted) return;
        setState(
          () => _loadError =
              'Сервер недоступен - используется локальный банк вопросов.',
        );
      }
    }

    final local = await ref.read(
      questionsByTopicProvider(widget.topicId).future,
    );
    if (!mounted) return;
    setState(() => _questions = local);
  }

  List<Question> _parseServerQuestions(
    Map<String, dynamic> testData,
    String topicId,
    String topicTitle,
  ) {
    final questionsMap = testData['questions'] as Map<String, dynamic>? ?? {};
    return questionsMap.values
        .map((raw) {
          final q = raw as Map<String, dynamic>;
          return Question(
            topicId: topicId,
            topicTitle: topicTitle,
            type: q['type'] as String? ?? 'server',
            question: q['question'] as String,
            answers: (q['answers'] as List).cast<String>(),
            correctAnswer: q['correct_answer'] as int,
            explanation: q['explanation'] as String? ?? '',
          );
        })
        .toList(growable: false);
  }

  @override
  void dispose() {
    _ticker?.cancel();
    _stopwatch.stop();
    super.dispose();
  }

  String _formatElapsed() {
    final minutes = _elapsed.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = _elapsed.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  @override
  Widget build(BuildContext context) {
    final questions = _questions;
    if (questions == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (questions.isEmpty) {
      return const Scaffold(
        body: Center(child: Text('Для этой темы пока нет вопросов')),
      );
    }

    final question = questions[_currentIndex];
    final topicTitle = question.topicTitle;

    return Scaffold(
      appBar: AppBar(
        title: Text(topicTitle),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Center(child: Text(_formatElapsed())),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_loadError != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  _loadError!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ),
            LinearProgressIndicator(
              value: (_currentIndex + 1) / questions.length,
            ),
            const SizedBox(height: 8),
            Text(
              'Вопрос ${_currentIndex + 1} из ${questions.length}',
              style: Theme.of(context).textTheme.labelLarge,
            ),
            const SizedBox(height: 16),
            Text(
              question.question,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            ...List.generate(question.answers.length, (i) {
              final isCorrect = i == question.correctAnswer;
              final isSelected = i == _selectedAnswer;
              Color? tileColor;
              Widget? trailing;
              if (_answered) {
                if (isCorrect) {
                  tileColor = Colors.green.withValues(alpha: 0.2);
                  trailing = const Icon(Icons.check_circle, color: Colors.green);
                } else if (isSelected) {
                  tileColor = Colors.red.withValues(alpha: 0.2);
                  trailing = const Icon(Icons.cancel, color: Colors.red);
                }
              }
              return Card(
                color: tileColor,
                child: ListTile(
                  title: Text(question.answers[i]),
                  trailing: trailing,
                  onTap: _answered
                      ? null
                      : () {
                          setState(() {
                            _selectedAnswer = i;
                            _answered = true;
                            if (isCorrect) _score++;
                            _reviewLog.add(
                              AnsweredQuestion(
                                question: question.question,
                                isCorrect: isCorrect,
                                correctAnswerText:
                                    question.answers[question.correctAnswer],
                              ),
                            );
                          });
                        },
                ),
              );
            }),
            if (_answered && question.explanation.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                question.explanation,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
            const Spacer(),
            if (_answered)
              FilledButton(
                onPressed: () => _goToNext(questions, topicTitle),
                child: Text(
                  _currentIndex + 1 < questions.length
                      ? 'Следующий вопрос'
                      : 'Завершить тест',
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _goToNext(List<Question> questions, String topicTitle) async {
    if (_currentIndex + 1 < questions.length) {
      setState(() {
        _currentIndex++;
        _selectedAnswer = null;
        _answered = false;
      });
      return;
    }

    await ref
        .read(databaseProvider)
        .recordTestAttempt(
          topicId: widget.topicId,
          topicTitle: topicTitle,
          score: _score,
          total: questions.length,
        );
    ref.read(progressRevisionProvider.notifier).state++;

    if (!mounted) return;
    context.pushReplacement(
      '/tests/${widget.topicId}/result',
      extra: {
        'score': _score,
        'total': questions.length,
        'topicTitle': topicTitle,
        'answers': _reviewLog,
      },
    );
  }
}
