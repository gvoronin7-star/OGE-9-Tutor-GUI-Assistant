import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

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
  final Stopwatch _stopwatch = Stopwatch()..start();
  Timer? _ticker;
  Duration _elapsed = Duration.zero;

  @override
  void initState() {
    super.initState();
    _ticker = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() => _elapsed = _stopwatch.elapsed);
    });
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
    final questionsAsync = ref.watch(questionsByTopicProvider(widget.topicId));

    return questionsAsync.when(
      loading: () =>
          const Scaffold(body: Center(child: CircularProgressIndicator())),
      error: (err, _) => Scaffold(body: Center(child: Text('Ошибка: $err'))),
      data: (questions) {
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
                  if (_answered) {
                    if (isCorrect) {
                      tileColor = Colors.green.withValues(alpha: 0.2);
                    } else if (isSelected) {
                      tileColor = Colors.red.withValues(alpha: 0.2);
                    }
                  }
                  return Card(
                    color: tileColor,
                    child: ListTile(
                      title: Text(question.answers[i]),
                      onTap: _answered
                          ? null
                          : () {
                              setState(() {
                                _selectedAnswer = i;
                                _answered = true;
                                if (isCorrect) _score++;
                              });
                            },
                    ),
                  );
                }),
                if (_answered) ...[
                  const SizedBox(height: 8),
                  Text(
                    question.explanation,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
                const Spacer(),
                if (_answered)
                  FilledButton(
                    onPressed: () => _goToNext(questions.length, topicTitle),
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
      },
    );
  }

  Future<void> _goToNext(int totalQuestions, String topicTitle) async {
    if (_currentIndex + 1 < totalQuestions) {
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
          total: totalQuestions,
        );
    ref.read(progressRevisionProvider.notifier).state++;

    if (!mounted) return;
    context.pushReplacement(
      '/tests/${widget.topicId}/result',
      extra: {
        'score': _score,
        'total': totalQuestions,
        'topicTitle': topicTitle,
      },
    );
  }
}
