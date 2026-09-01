import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/providers.dart';
import 'core/router.dart';
import 'core/settings_repository.dart';
import 'core/theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final settingsRepository = SettingsRepository();
  final serverUrl = await settingsRepository.loadServerUrl();
  final serverModeEnabled = await settingsRepository.loadServerModeEnabled();

  runApp(
    ProviderScope(
      overrides: [
        serverUrlProvider.overrideWith((ref) => serverUrl),
        serverModeEnabledProvider.overrideWith((ref) => serverModeEnabled),
      ],
      child: const OgeTutorApp(),
    ),
  );
}

class OgeTutorApp extends StatelessWidget {
  const OgeTutorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'ОГЭ-Тьютор',
      theme: buildLightTheme(),
      darkTheme: buildDarkTheme(),
      routerConfig: router,
    );
  }
}
