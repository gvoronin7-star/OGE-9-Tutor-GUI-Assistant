import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';

class ProgressScreen extends ConsumerWidget {
  const ProgressScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final topicsAsync = ref.watch(topicsProvider);
    final studiedCountAsync = ref.watch(studiedTopicsCountProvider);
    final attemptsAsync = ref.watch(recentAttemptsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Прогресс')),
      body: attemptsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Ошибка: $err')),
        data: (attempts) {
          final totalCorrect = attempts.fold<int>(0, (sum, a) => sum + a.score);
          final totalQuestions = attempts.fold<int>(
            0,
            (sum, a) => sum + a.total,
          );
          final accuracy = totalQuestions == 0
              ? 0
              : ((totalCorrect / totalQuestions) * 100).round();
          final topicsTotal = topicsAsync.valueOrNull?.length ?? 0;
          final studied = studiedCountAsync.valueOrNull ?? 0;

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _StatsRow(
                studied: studied,
                topicsTotal: topicsTotal,
                testsPassed: attempts.length,
                accuracy: accuracy,
              ),
              const SizedBox(height: 24),
              Text(
                'История тестов',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              if (attempts.isEmpty)
                const Text('Вы ещё не прошли ни одного теста'),
              ...attempts.map(
                (a) => Card(
                  child: ListTile(
                    title: Text(a.topicTitle),
                    subtitle: Text(_formatDate(a.completedAt)),
                    trailing: Text('${a.score}/${a.total}'),
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  String _formatDate(DateTime dt) {
    String two(int n) => n.toString().padLeft(2, '0');
    return '${two(dt.day)}.${two(dt.month)}.${dt.year} ${two(dt.hour)}:${two(dt.minute)}';
  }
}

class _StatsRow extends StatelessWidget {
  final int studied;
  final int topicsTotal;
  final int testsPassed;
  final int accuracy;

  const _StatsRow({
    required this.studied,
    required this.topicsTotal,
    required this.testsPassed,
    required this.accuracy,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _StatCard(
            label: 'Темы изучены',
            value: '$studied/$topicsTotal',
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _StatCard(label: 'Тестов пройдено', value: '$testsPassed'),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _StatCard(label: 'Точность', value: '$accuracy%'),
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;

  const _StatCard({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Text(value, style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 4),
            Text(
              label,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}
