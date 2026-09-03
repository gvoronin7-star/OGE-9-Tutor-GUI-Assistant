import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/providers.dart';

// Совпадает с началом абзаца вида "Термин — определение" (частый паттерн
// в статьях базы ФИПИ) - термин выделяется полужирным, остальной текст
// абзаца остаётся обычным начертанием.
final _definitionTermPattern = RegExp(r'^([^—\n]{1,50}?\s—\s)');

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

  List<Widget> _buildArticleParagraphs(BuildContext context, String article) {
    final baseStyle = Theme.of(context).textTheme.bodyLarge;
    final termStyle = baseStyle?.copyWith(fontWeight: FontWeight.bold);
    final paragraphs = article.split('\n\n').where((p) => p.trim().isNotEmpty);

    return paragraphs.map((paragraph) {
      final match = _definitionTermPattern.matchAsPrefix(paragraph);
      return Padding(
        padding: const EdgeInsets.only(bottom: 16),
        child: match == null
            ? Text(paragraph, style: baseStyle)
            : Text.rich(
                TextSpan(
                  children: [
                    TextSpan(text: match.group(1), style: termStyle),
                    TextSpan(
                      text: paragraph.substring(match.end),
                      style: baseStyle,
                    ),
                  ],
                ),
              ),
      );
    }).toList(growable: false);
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
                if (showingRemote)
                  Text(
                    _remoteArticle!,
                    style: Theme.of(context).textTheme.bodyLarge,
                  )
                else
                  ..._buildArticleParagraphs(context, topic.article),
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
