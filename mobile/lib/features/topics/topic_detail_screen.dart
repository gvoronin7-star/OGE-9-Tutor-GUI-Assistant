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
  String? _remoteArticle;
  bool _remoteLoading = false;
  String? _remoteError;

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

  Future<void> _loadRemoteArticle(String? topicTitle) async {
    if (topicTitle == null) return;
    setState(() {
      _remoteLoading = true;
      _remoteError = null;
    });
    try {
      final answer = await ref
          .read(apiClientProvider)
          .ask('Расскажи подробно про тему: $topicTitle');
      if (!mounted) return;
      setState(() {
        _remoteArticle = answer;
        _remoteLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _remoteError = 'Сервер недоступен - показана локальная статья.';
        _remoteLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final topicsAsync = ref.watch(topicsProvider);
    final serverModeEnabled = ref.watch(serverModeEnabledProvider);

    return topicsAsync.when(
      loading: () =>
          const Scaffold(body: Center(child: CircularProgressIndicator())),
      error: (err, _) => Scaffold(body: Center(child: Text('Ошибка: $err'))),
      data: (topics) {
        final topic = topics.firstWhere((t) => t.id == widget.topicId);

        if (serverModeEnabled &&
            _remoteArticle == null &&
            !_remoteLoading &&
            _remoteError == null) {
          WidgetsBinding.instance.addPostFrameCallback(
            (_) => _loadRemoteArticle(topic.title),
          );
        }

        final showingRemote = serverModeEnabled && _remoteArticle != null;

        return Scaffold(
          appBar: AppBar(title: Text(topic.title)),
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (serverModeEnabled && _remoteLoading)
                  const Padding(
                    padding: EdgeInsets.only(bottom: 16),
                    child: LinearProgressIndicator(),
                  ),
                if (_remoteError != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: Text(
                      _remoteError!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ),
                if (showingRemote)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Chip(label: const Text('Ответ сервера')),
                  ),
                Text(
                  showingRemote ? _remoteArticle! : topic.article,
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
