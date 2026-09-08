import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/router.dart' as app_router;
import 'package:mobile/main.dart';

/// Роутер принимает любой topicId в пути - раньше несуществующая тема
/// оставляла TestTakingScreen в вечном CircularProgressIndicator без
/// AppBar и без выхода (firstWhere без orElse бросал необработанное
/// исключение внутри _loadQuestions()). Найдено зональным аудитом хаба
/// 2026-09-08 (В-3 отчёта), см. lib/features/tests/test_taking_screen.dart.
void main() {
  testWidgets(
    'Test screen with an unknown topicId shows an error, not an eternal spinner',
    (tester) async {
      await tester.pumpWidget(const ProviderScope(child: OgeTutorApp()));
      await tester.pumpAndSettle();

      app_router.router.go('/tests/this-topic-does-not-exist');
      await tester.pumpAndSettle();

      // Экран должен показать понятную ошибку с AppBar (значит - есть
      // путь назад), а не бесконечный CircularProgressIndicator.
      expect(find.byType(CircularProgressIndicator), findsNothing);
      expect(find.text('Ошибка'), findsOneWidget);
      expect(find.textContaining('this-topic-does-not-exist'), findsOneWidget);
    },
  );
}
