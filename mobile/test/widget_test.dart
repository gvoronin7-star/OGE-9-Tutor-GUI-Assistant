import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/main.dart';

void main() {
  testWidgets('App boots to the topics list with bottom nav', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: OgeTutorApp()));
    await tester.pumpAndSettle();

    expect(find.text('Темы ОГЭ'), findsOneWidget);
    expect(find.text('Человек и общество'), findsOneWidget);
    expect(find.text('Темы'), findsOneWidget);
    expect(find.text('Тесты'), findsOneWidget);
    expect(find.text('Прогресс'), findsOneWidget);
    expect(find.text('Настройки'), findsOneWidget);
    expect(find.text('Помощь'), findsOneWidget);
  });

  testWidgets('Settings tab shows the server-mode switch', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: OgeTutorApp()));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));

    await tester.tap(find.text('Настройки'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));

    expect(find.text('Серверный режим'), findsOneWidget);
    expect(find.byType(SwitchListTile), findsOneWidget);
  });
}
