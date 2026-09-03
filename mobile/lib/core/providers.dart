import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/assets/content_repository.dart';
import '../data/embeddings/embedding_service.dart';
import '../data/embeddings/local_search.dart';
import '../data/local_db/database.dart';
import '../data/remote/api_client.dart';
import 'models.dart';
import 'settings_repository.dart';

final contentRepositoryProvider = Provider((ref) => const ContentRepository());

final settingsRepositoryProvider = Provider((ref) => SettingsRepository());

/// Seeded from persisted storage via ProviderScope overrides in main().
final serverUrlProvider = StateProvider<String>(
  (ref) => SettingsRepository.defaultServerUrl,
);

/// Seeded from persisted storage via ProviderScope overrides in main().
final serverModeEnabledProvider = StateProvider<bool>((ref) => false);

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(ref.watch(serverUrlProvider));
});

final chunksProvider = FutureProvider<List<Chunk>>((ref) {
  return ref.read(contentRepositoryProvider).loadChunks();
});

final embeddingServiceProvider = Provider<EmbeddingService>((ref) {
  final service = EmbeddingService();
  ref.onDispose(service.dispose);
  return service;
});

final localSearchProvider = FutureProvider<LocalSearch>((ref) async {
  final chunks = await ref.watch(chunksProvider.future);
  return LocalSearch(chunks);
});

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

final studiedTopicIdsProvider = FutureProvider<Set<String>>((ref) {
  ref.watch(progressRevisionProvider);
  return ref.read(databaseProvider).studiedTopicIds();
});

final recentAttemptsProvider = FutureProvider<List<TestAttempt>>((ref) {
  ref.watch(progressRevisionProvider);
  return ref.read(databaseProvider).recentAttempts();
});
