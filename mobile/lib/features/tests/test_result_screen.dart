import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class TestResultScreen extends StatelessWidget {
  final int score;
  final int total;
  final String topicTitle;

  const TestResultScreen({
    super.key,
    required this.score,
    required this.total,
    required this.topicTitle,
  });

  @override
  Widget build(BuildContext context) {
    final percent = total == 0 ? 0 : ((score / total) * 100).round();

    return Scaffold(
      appBar: AppBar(title: Text('Результат: $topicTitle')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              '$score из $total',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text('$percent%', style: Theme.of(context).textTheme.displaySmall),
            const SizedBox(height: 32),
            FilledButton(
              onPressed: () => context.go('/tests'),
              child: const Text('К списку тестов'),
            ),
            TextButton(
              onPressed: () => context.go('/progress'),
              child: const Text('Посмотреть прогресс'),
            ),
          ],
        ),
      ),
    );
  }
}
