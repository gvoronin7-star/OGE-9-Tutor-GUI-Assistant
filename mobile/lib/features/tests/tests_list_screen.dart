import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/providers.dart';

class TestsListScreen extends ConsumerWidget {
  const TestsListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final topicsAsync = ref.watch(topicsProvider);

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
            return ListTile(
              leading: const Icon(Icons.quiz_outlined),
              title: Text(topic.title),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/tests/${topic.id}'),
            );
          },
        ),
      ),
    );
  }
}
