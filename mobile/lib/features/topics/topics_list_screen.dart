import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/providers.dart';

class TopicsListScreen extends ConsumerWidget {
  const TopicsListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final topicsAsync = ref.watch(topicsProvider);
    final studiedIds = ref.watch(studiedTopicIdsProvider).valueOrNull ?? const {};

    return Scaffold(
      appBar: AppBar(
        title: const Text('Темы ОГЭ'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            tooltip: 'Поиск по базе ФИПИ',
            onPressed: () => context.push('/search'),
          ),
        ],
      ),
      body: topicsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) =>
            Center(child: Text('Не удалось загрузить темы: $err')),
        data: (topics) => ListView.separated(
          itemCount: topics.length,
          separatorBuilder: (_, _) => const Divider(height: 1),
          itemBuilder: (context, index) {
            final topic = topics[index];
            final studied = studiedIds.contains(topic.id);
            return ListTile(
              leading: Icon(
                studied ? Icons.check_circle : Icons.circle_outlined,
                color: studied
                    ? Theme.of(context).colorScheme.primary
                    : Theme.of(context).colorScheme.outline,
              ),
              title: Text(topic.title),
              subtitle: studied ? const Text('Изучено') : null,
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/topics/${topic.id}'),
            );
          },
        ),
      ),
    );
  }
}
