import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models.dart';
import '../../core/providers.dart';

// Совпадает с началом абзаца вида "Термин — определение" (частый паттерн
// в статьях базы ФИПИ) - термин выделяется полужирным, остальной текст
// абзаца остаётся обычным начертанием.
final _definitionTermPattern = RegExp(r'^([^—\n]{1,50}?\s—\s)');

class _TopicIllustration extends StatelessWidget {
  final String assetPath;
  final String caption;

  const _TopicIllustration({required this.assetPath, required this.caption});

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Image.asset(assetPath),
            const SizedBox(height: 8),
            Text(
              caption,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}

class TopicDetailScreen extends ConsumerStatefulWidget {
  final String topicId;

  const TopicDetailScreen({super.key, required this.topicId});

  @override
  ConsumerState<TopicDetailScreen> createState() => _TopicDetailScreenState();
}

class _TopicDetailScreenState extends ConsumerState<TopicDetailScreen> {
  String? _remoteArticle;
  bool _remoteIsFallback = false;
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
      final result = await ref
          .read(apiClientProvider)
          .ask('Расскажи подробно про тему: $topicTitle');
      if (!mounted) return;
      setState(() {
        _remoteArticle = result.answer;
        _remoteIsFallback = result.isFallback;
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
        // Роутер принимает любой topicId в пути - firstWhere без orElse
        // раньше бросал StateError прямо во время build() на несуществующей
        // теме (не async-путь, но всё равно необработанное исключение,
        // не понятное пользователю сообщение). Найдено зональным аудитом
        // хаба 2026-09-08 (В-3 отчёта).
        final matches = topics.where((t) => t.id == widget.topicId);
        if (matches.isEmpty) {
          return Scaffold(
            appBar: AppBar(title: const Text('Тема не найдена')),
            body: Center(
              child: Text('Тема "${widget.topicId}" не найдена'),
            ),
          );
        }
        // final (не var) - иначе анализатор не продвигает тип сквозь
        // замыкание addPostFrameCallback ниже, которое захватывает
        // переменную, а не её значение в момент вызова.
        final Topic topic = matches.first;

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
                    // is_fallback значит, что LLM на сервере была
                    // недоступна и это демо-заглушка по ключевым словам,
                    // а не настоящий ответ модели - показывать как
                    // обычный "Ответ сервера" вводит в заблуждение.
                    // Найдено зональным аудитом хаба 2026-09-08 (К-4).
                    child: Chip(
                      label: Text(
                        _remoteIsFallback
                            ? 'Демо-ответ (LLM недоступна)'
                            : 'Ответ сервера',
                      ),
                    ),
                  ),
                if (showingRemote)
                  Text(
                    _remoteArticle!,
                    style: Theme.of(context).textTheme.bodyLarge,
                  )
                else
                  ..._buildArticleParagraphs(context, topic.article),
                if (!showingRemote && topic.id == 'society') ...[
                  const SizedBox(height: 8),
                  _TopicIllustration(
                    assetPath: 'assets/images/social_institutions.png',
                    caption: 'Общество как система социальных институтов',
                  ),
                ],
                if (!showingRemote && topic.id == 'economy') ...[
                  const SizedBox(height: 8),
                  _TopicIllustration(
                    assetPath: 'assets/images/economic_cycle.png',
                    caption: 'Экономический цикл: производство, распределение, потребление',
                  ),
                ],
                if (!showingRemote && topic.id == 'law') ...[
                  const SizedBox(height: 8),
                  _TopicIllustration(
                    assetPath: 'assets/images/human_rights_groups.png',
                    caption: 'Основные группы прав человека',
                  ),
                ],
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
