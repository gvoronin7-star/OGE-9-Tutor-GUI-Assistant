import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../../data/remote/api_client.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

enum _ConnectionState { unknown, checking, ok, failed }

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  late final TextEditingController _urlController;
  _ConnectionState _connection = _ConnectionState.unknown;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(text: ref.read(serverUrlProvider));
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _checkConnection() async {
    setState(() => _connection = _ConnectionState.checking);
    final ok = await ApiClient(_urlController.text.trim()).checkHealth();
    if (!mounted) return;
    setState(
      () => _connection = ok ? _ConnectionState.ok : _ConnectionState.failed,
    );
  }

  Future<void> _saveUrl() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Введите адрес сервера')),
      );
      return;
    }
    ref.read(serverUrlProvider.notifier).state = url;
    await ref.read(settingsRepositoryProvider).saveServerUrl(url);
    await _checkConnection();
  }

  @override
  Widget build(BuildContext context) {
    final serverModeEnabled = ref.watch(serverModeEnabledProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Настройки')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          SwitchListTile(
            title: const Text('Серверный режим'),
            subtitle: const Text(
              'Темы и тесты приходят с того же сервера, что использует '
              'десктопное приложение, вместо локального банка на устройстве.',
            ),
            value: serverModeEnabled,
            onChanged: (value) async {
              ref.read(serverModeEnabledProvider.notifier).state = value;
              await ref
                  .read(settingsRepositoryProvider)
                  .saveServerModeEnabled(value);
            },
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _urlController,
            decoration: const InputDecoration(
              labelText: 'Адрес сервера',
              hintText: 'например, http://192.168.1.10:8000',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Это адрес компьютера с десктопным приложением в вашей локальной '
            'сети (не адрес самого телефона). Узнать его: на компьютере '
            'выполнить ipconfig (Windows) или ifconfig (macOS/Linux) и '
            'найти строку вида IPv4-адрес / inet.',
            style: TextStyle(fontSize: 12.5, color: Colors.grey),
          ),
          const SizedBox(height: 8),
          Wrap(
            crossAxisAlignment: WrapCrossAlignment.center,
            spacing: 16,
            runSpacing: 8,
            children: [
              FilledButton(
                onPressed: _saveUrl,
                child: const Text('Сохранить и проверить'),
              ),
              _ConnectionIndicator(state: _connection),
            ],
          ),
          const SizedBox(height: 24),
          const Text(
            'Если сервер недоступен, приложение автоматически использует '
            'локальный автономный режим.',
            style: TextStyle(fontStyle: FontStyle.italic),
          ),
        ],
      ),
    );
  }
}

class _ConnectionIndicator extends StatelessWidget {
  final _ConnectionState state;

  const _ConnectionIndicator({required this.state});

  @override
  Widget build(BuildContext context) {
    switch (state) {
      case _ConnectionState.unknown:
        return const SizedBox.shrink();
      case _ConnectionState.checking:
        return const SizedBox(
          width: 20,
          height: 20,
          child: CircularProgressIndicator(strokeWidth: 2),
        );
      case _ConnectionState.ok:
        return const Row(
          children: [
            Icon(Icons.check_circle, color: Colors.green),
            SizedBox(width: 4),
            Text('Сервер доступен'),
          ],
        );
      case _ConnectionState.failed:
        return const Row(
          children: [
            Icon(Icons.error, color: Colors.red),
            SizedBox(width: 4),
            Text('Сервер недоступен'),
          ],
        );
    }
  }
}
