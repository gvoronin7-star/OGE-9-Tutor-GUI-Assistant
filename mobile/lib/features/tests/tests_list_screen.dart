import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/providers.dart';

String _pluralQuestions(int n) {
  final mod100 = n % 100;
  final mod10 = n % 10;
  if (mod100 >= 11 && mod100 <= 14) return '$n вопросов';
  if (mod10 == 1) return '$n вопрос';
  if (mod10 >= 2 && mod10 <= 4) return '$n вопроса';
  return '$n вопросов';
}

class TestsListScreen extends ConsumerWidget {
  const TestsListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final topicsAsync = ref.watch(topicsProvider);
    final questions = ref.watch(questionsProvider).valueOrNull ?? const [];
    final attempts = ref.watch(recentAttemptsProvider).valueOrNull ?? const [];

    return Scaffold(
      appBar: AppBar(title: const Text('Тесты')),
      body: topicsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) =>
            Center(child: Text('Не удалось загрузить темы: $err')),
        data: (topics) => ListView.separated(
          itemCount: topics.length,
          separatorBuilder: (_, _) => const Divider(height: 1),
          itemBuilder: (context, index) {
            final topic = topics[index];
            final questionCount = questions
                .where((q) => q.topicId == topic.id)
                .length;
            final topicAttempts = attempts.where(
              (a) => a.topicId == topic.id,
            );
            int? bestPercent;
            for (final a in topicAttempts) {
              if (a.total == 0) continue;
              final percent = (a.score / a.total * 100).round();
              if (bestPercent == null || percent > bestPercent) {
                bestPercent = percent;
              }
            }
            final subtitleParts = <String>[
              if (questionCount > 0) _pluralQuestions(questionCount),
              if (bestPercent != null) 'лучший результат $bestPercent%',
            ];
            return ListTile(
              leading: const Icon(Icons.quiz_outlined),
              title: Text(topic.title),
              subtitle: subtitleParts.isEmpty
                  ? null
                  : Text(subtitleParts.join(' · ')),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/tests/${topic.id}'),
            );
          },
        ),
      ),
    );
  }
}
