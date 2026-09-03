import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/providers.dart';

class TopicsListScreen extends ConsumerStatefulWidget {
  const TopicsListScreen({super.key});

  @override
  ConsumerState<TopicsListScreen> createState() => _TopicsListScreenState();
}

class _TopicsListScreenState extends ConsumerState<TopicsListScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _maybeShowOnboarding());
  }

  Future<void> _maybeShowOnboarding() async {
    final settings = ref.read(settingsRepositoryProvider);
    final seen = await settings.loadOnboardingSeen();
    if (seen || !mounted) return;
    await showDialog<void>(
      context: context,
      builder: (context) => const _OnboardingDialog(),
    );
    await settings.saveOnboardingSeen();
  }

  @override
  Widget build(BuildContext context) {
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

class _OnboardingDialog extends StatelessWidget {
  const _OnboardingDialog();

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Добро пожаловать!'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: const [
          _OnboardingPoint(
            icon: Icons.cloud_off_outlined,
            text:
                'Работает офлайн — все темы и тесты уже на устройстве, '
                'интернет для занятий не нужен.',
          ),
          SizedBox(height: 16),
          _OnboardingPoint(
            icon: Icons.search,
            text:
                'Поиск понимает смысл вопроса, а не только точные слова — '
                'ищет по всей базе ФИПИ прямо на телефоне.',
          ),
          SizedBox(height: 16),
          _OnboardingPoint(
            icon: Icons.dns_outlined,
            text:
                'В настройках можно подключить тот же сервер, что '
                'использует десктопное приложение, вместо локального банка.',
          ),
        ],
      ),
      actions: [
        FilledButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Понятно'),
        ),
      ],
    );
  }
}

class _OnboardingPoint extends StatelessWidget {
  final IconData icon;
  final String text;

  const _OnboardingPoint({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, color: Theme.of(context).colorScheme.primary),
        const SizedBox(width: 12),
        Expanded(child: Text(text)),
      ],
    );
  }
}
