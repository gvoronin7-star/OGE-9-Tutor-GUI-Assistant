import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/models.dart';

class TestResultScreen extends StatelessWidget {
  final String topicId;
  final int score;
  final int total;
  final String topicTitle;
  final List<AnsweredQuestion> answers;

  const TestResultScreen({
    super.key,
    required this.topicId,
    required this.score,
    required this.total,
    required this.topicTitle,
    required this.answers,
  });

  @override
  Widget build(BuildContext context) {
    final percent = total == 0 ? 0 : ((score / total) * 100).round();

    return Scaffold(
      appBar: AppBar(title: Text('Результат: $topicTitle')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Center(
            child: Column(
              children: [
                Text(
                  '$score из $total',
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  '$percent%',
                  style: Theme.of(context).textTheme.displaySmall,
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),
          FilledButton.icon(
            onPressed: () => context.go('/tests/$topicId'),
            icon: const Icon(Icons.replay),
            label: const Text('Пройти ещё раз'),
          ),
          const SizedBox(height: 8),
          OutlinedButton(
            onPressed: () => context.go('/tests'),
            child: const Text('К списку тестов'),
          ),
          const SizedBox(height: 4),
          TextButton(
            onPressed: () => context.go('/progress'),
            child: const Text('Посмотреть прогресс'),
          ),
          if (answers.isNotEmpty) ...[
            const SizedBox(height: 24),
            Text('Разбор ответов', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ...answers.asMap().entries.map(
              (entry) => _ReviewTile(index: entry.key, item: entry.value),
            ),
          ],
        ],
      ),
    );
  }
}

class _ReviewTile extends StatelessWidget {
  final int index;
  final AnsweredQuestion item;

  const _ReviewTile({required this.index, required this.item});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: Icon(
          item.isCorrect ? Icons.check_circle : Icons.cancel,
          color: item.isCorrect ? Colors.green : Colors.red,
        ),
        title: Text('${index + 1}. ${item.question}'),
        subtitle: item.isCorrect
            ? null
            : Text('Правильный ответ: ${item.correctAnswerText}'),
      ),
    );
  }
}
