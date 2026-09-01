import 'dart:io';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

part 'database.g.dart';

class StudiedTopics extends Table {
  TextColumn get topicId => text()();
  DateTimeColumn get firstOpenedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {topicId};
}

class TestAttempts extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get topicId => text()();
  TextColumn get topicTitle => text()();
  IntColumn get score => integer()();
  IntColumn get total => integer()();
  DateTimeColumn get completedAt => dateTime()();
}

@DriftDatabase(tables: [StudiedTopics, TestAttempts])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  @override
  int get schemaVersion => 1;

  Future<void> markTopicStudied(String topicId) async {
    await into(studiedTopics).insertOnConflictUpdate(
      StudiedTopicsCompanion.insert(
        topicId: topicId,
        firstOpenedAt: DateTime.now(),
      ),
    );
  }

  Future<int> studiedTopicsCount() async {
    final rows = await select(studiedTopics).get();
    return rows.length;
  }

  Future<void> recordTestAttempt({
    required String topicId,
    required String topicTitle,
    required int score,
    required int total,
  }) async {
    await into(testAttempts).insert(
      TestAttemptsCompanion.insert(
        topicId: topicId,
        topicTitle: topicTitle,
        score: score,
        total: total,
        completedAt: DateTime.now(),
      ),
    );
  }

  Future<List<TestAttempt>> recentAttempts({int limit = 50}) {
    return (select(testAttempts)
          ..orderBy([(t) => OrderingTerm.desc(t.completedAt)])
          ..limit(limit))
        .get();
  }
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dbFolder = await getApplicationDocumentsDirectory();
    final file = File(p.join(dbFolder.path, 'oge_tutor.sqlite'));
    return NativeDatabase.createInBackground(file);
  });
}
