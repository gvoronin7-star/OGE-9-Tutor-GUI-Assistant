import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/providers.dart';

class TopicDetailScreen extends ConsumerStatefulWidget {
  final String topicId;

  const TopicDetailScreen({super.key, required this.topicId});

  @override
  ConsumerState<TopicDetailScreen> createState() => _TopicDetailScreenState();
}

class _TopicDetailScreenState extends ConsumerState<TopicDetailScreen> {
  @override
  void initState() {
    super.initState();
    // Открытие статьи засчитывается как "тема изучена" для прогресса -
    // не дожидаемся первого пройденного теста по теме.
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await ref.read(databaseProvider).markTopicStudied(widget.topicId);
      ref.read(progressRevisionProvider.notifier).state++;
    });
  }

  @override
  Widget build(BuildContext context) {
    final topicsAsync = ref.watch(topicsProvider);

    return topicsAsync.when(
      loading: () =>
          const Scaffold(body: Center(child: CircularProgressIndicator())),
      error: (err, _) => Scaffold(body: Center(child: Text('Ошибка: $err'))),
      data: (topics) {
        final topic = topics.firstWhere((t) => t.id == widget.topicId);
        return Scaffold(
          appBar: AppBar(title: Text(topic.title)),
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  topic.article,
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed: () => context.push('/tests/${topic.id}'),
                  icon: const Icon(Icons.quiz_outlined),
                  label: const Text('Пройти тест по теме'),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
