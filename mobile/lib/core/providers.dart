import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/assets/content_repository.dart';
import '../data/local_db/database.dart';
import 'models.dart';

final contentRepositoryProvider = Provider((ref) => const ContentRepository());

final databaseProvider = Provider<AppDatabase>((ref) {
  final db = AppDatabase();
  ref.onDispose(db.close);
  return db;
});

final topicsProvider = FutureProvider<List<Topic>>((ref) {
  return ref.read(contentRepositoryProvider).loadTopics();
});

final questionsProvider = FutureProvider<List<Question>>((ref) {
  return ref.read(contentRepositoryProvider).loadQuestions();
});

final questionsByTopicProvider = FutureProvider.family<List<Question>, String>((
  ref,
  topicId,
) async {
  final all = await ref.watch(questionsProvider.future);
  return all.where((q) => q.topicId == topicId).toList(growable: false);
});

/// Bumped after every write to studied topics / test attempts so screens
/// that read progress can invalidate their cached FutureProviders.
final progressRevisionProvider = StateProvider<int>((ref) => 0);

final studiedTopicsCountProvider = FutureProvider<int>((ref) {
  ref.watch(progressRevisionProvider);
  return ref.read(databaseProvider).studiedTopicsCount();
});

final recentAttemptsProvider = FutureProvider<List<TestAttempt>>((ref) {
  ref.watch(progressRevisionProvider);
  return ref.read(databaseProvider).recentAttempts();
});
