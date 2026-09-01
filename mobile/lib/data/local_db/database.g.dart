// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'database.dart';

// ignore_for_file: type=lint
class $StudiedTopicsTable extends StudiedTopics
    with TableInfo<$StudiedTopicsTable, StudiedTopic> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $StudiedTopicsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _topicIdMeta = const VerificationMeta(
    'topicId',
  );
  @override
  late final GeneratedColumn<String> topicId = GeneratedColumn<String>(
    'topic_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _firstOpenedAtMeta = const VerificationMeta(
    'firstOpenedAt',
  );
  @override
  late final GeneratedColumn<DateTime> firstOpenedAt =
      GeneratedColumn<DateTime>(
        'first_opened_at',
        aliasedName,
        false,
        type: DriftSqlType.dateTime,
        requiredDuringInsert: true,
      );
  @override
  List<GeneratedColumn> get $columns => [topicId, firstOpenedAt];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'studied_topics';
  @override
  VerificationContext validateIntegrity(
    Insertable<StudiedTopic> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('topic_id')) {
      context.handle(
        _topicIdMeta,
        topicId.isAcceptableOrUnknown(data['topic_id']!, _topicIdMeta),
      );
    } else if (isInserting) {
      context.missing(_topicIdMeta);
    }
    if (data.containsKey('first_opened_at')) {
      context.handle(
        _firstOpenedAtMeta,
        firstOpenedAt.isAcceptableOrUnknown(
          data['first_opened_at']!,
          _firstOpenedAtMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_firstOpenedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {topicId};
  @override
  StudiedTopic map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return StudiedTopic(
      topicId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}topic_id'],
      )!,
      firstOpenedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}first_opened_at'],
      )!,
    );
  }

  @override
  $StudiedTopicsTable createAlias(String alias) {
    return $StudiedTopicsTable(attachedDatabase, alias);
  }
}

class StudiedTopic extends DataClass implements Insertable<StudiedTopic> {
  final String topicId;
  final DateTime firstOpenedAt;
  const StudiedTopic({required this.topicId, required this.firstOpenedAt});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['topic_id'] = Variable<String>(topicId);
    map['first_opened_at'] = Variable<DateTime>(firstOpenedAt);
    return map;
  }

  StudiedTopicsCompanion toCompanion(bool nullToAbsent) {
    return StudiedTopicsCompanion(
      topicId: Value(topicId),
      firstOpenedAt: Value(firstOpenedAt),
    );
  }

  factory StudiedTopic.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return StudiedTopic(
      topicId: serializer.fromJson<String>(json['topicId']),
      firstOpenedAt: serializer.fromJson<DateTime>(json['firstOpenedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'topicId': serializer.toJson<String>(topicId),
      'firstOpenedAt': serializer.toJson<DateTime>(firstOpenedAt),
    };
  }

  StudiedTopic copyWith({String? topicId, DateTime? firstOpenedAt}) =>
      StudiedTopic(
        topicId: topicId ?? this.topicId,
        firstOpenedAt: firstOpenedAt ?? this.firstOpenedAt,
      );
  StudiedTopic copyWithCompanion(StudiedTopicsCompanion data) {
    return StudiedTopic(
      topicId: data.topicId.present ? data.topicId.value : this.topicId,
      firstOpenedAt: data.firstOpenedAt.present
          ? data.firstOpenedAt.value
          : this.firstOpenedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('StudiedTopic(')
          ..write('topicId: $topicId, ')
          ..write('firstOpenedAt: $firstOpenedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(topicId, firstOpenedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is StudiedTopic &&
          other.topicId == this.topicId &&
          other.firstOpenedAt == this.firstOpenedAt);
}

class StudiedTopicsCompanion extends UpdateCompanion<StudiedTopic> {
  final Value<String> topicId;
  final Value<DateTime> firstOpenedAt;
  final Value<int> rowid;
  const StudiedTopicsCompanion({
    this.topicId = const Value.absent(),
    this.firstOpenedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  StudiedTopicsCompanion.insert({
    required String topicId,
    required DateTime firstOpenedAt,
    this.rowid = const Value.absent(),
  }) : topicId = Value(topicId),
       firstOpenedAt = Value(firstOpenedAt);
  static Insertable<StudiedTopic> custom({
    Expression<String>? topicId,
    Expression<DateTime>? firstOpenedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (topicId != null) 'topic_id': topicId,
      if (firstOpenedAt != null) 'first_opened_at': firstOpenedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  StudiedTopicsCompanion copyWith({
    Value<String>? topicId,
    Value<DateTime>? firstOpenedAt,
    Value<int>? rowid,
  }) {
    return StudiedTopicsCompanion(
      topicId: topicId ?? this.topicId,
      firstOpenedAt: firstOpenedAt ?? this.firstOpenedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (topicId.present) {
      map['topic_id'] = Variable<String>(topicId.value);
    }
    if (firstOpenedAt.present) {
      map['first_opened_at'] = Variable<DateTime>(firstOpenedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('StudiedTopicsCompanion(')
          ..write('topicId: $topicId, ')
          ..write('firstOpenedAt: $firstOpenedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $TestAttemptsTable extends TestAttempts
    with TableInfo<$TestAttemptsTable, TestAttempt> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $TestAttemptsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _topicIdMeta = const VerificationMeta(
    'topicId',
  );
  @override
  late final GeneratedColumn<String> topicId = GeneratedColumn<String>(
    'topic_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _topicTitleMeta = const VerificationMeta(
    'topicTitle',
  );
  @override
  late final GeneratedColumn<String> topicTitle = GeneratedColumn<String>(
    'topic_title',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _scoreMeta = const VerificationMeta('score');
  @override
  late final GeneratedColumn<int> score = GeneratedColumn<int>(
    'score',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _totalMeta = const VerificationMeta('total');
  @override
  late final GeneratedColumn<int> total = GeneratedColumn<int>(
    'total',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _completedAtMeta = const VerificationMeta(
    'completedAt',
  );
  @override
  late final GeneratedColumn<DateTime> completedAt = GeneratedColumn<DateTime>(
    'completed_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    topicId,
    topicTitle,
    score,
    total,
    completedAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'test_attempts';
  @override
  VerificationContext validateIntegrity(
    Insertable<TestAttempt> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('topic_id')) {
      context.handle(
        _topicIdMeta,
        topicId.isAcceptableOrUnknown(data['topic_id']!, _topicIdMeta),
      );
    } else if (isInserting) {
      context.missing(_topicIdMeta);
    }
    if (data.containsKey('topic_title')) {
      context.handle(
        _topicTitleMeta,
        topicTitle.isAcceptableOrUnknown(data['topic_title']!, _topicTitleMeta),
      );
    } else if (isInserting) {
      context.missing(_topicTitleMeta);
    }
    if (data.containsKey('score')) {
      context.handle(
        _scoreMeta,
        score.isAcceptableOrUnknown(data['score']!, _scoreMeta),
      );
    } else if (isInserting) {
      context.missing(_scoreMeta);
    }
    if (data.containsKey('total')) {
      context.handle(
        _totalMeta,
        total.isAcceptableOrUnknown(data['total']!, _totalMeta),
      );
    } else if (isInserting) {
      context.missing(_totalMeta);
    }
    if (data.containsKey('completed_at')) {
      context.handle(
        _completedAtMeta,
        completedAt.isAcceptableOrUnknown(
          data['completed_at']!,
          _completedAtMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_completedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  TestAttempt map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return TestAttempt(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      topicId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}topic_id'],
      )!,
      topicTitle: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}topic_title'],
      )!,
      score: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}score'],
      )!,
      total: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}total'],
      )!,
      completedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}completed_at'],
      )!,
    );
  }

  @override
  $TestAttemptsTable createAlias(String alias) {
    return $TestAttemptsTable(attachedDatabase, alias);
  }
}

class TestAttempt extends DataClass implements Insertable<TestAttempt> {
  final int id;
  final String topicId;
  final String topicTitle;
  final int score;
  final int total;
  final DateTime completedAt;
  const TestAttempt({
    required this.id,
    required this.topicId,
    required this.topicTitle,
    required this.score,
    required this.total,
    required this.completedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['topic_id'] = Variable<String>(topicId);
    map['topic_title'] = Variable<String>(topicTitle);
    map['score'] = Variable<int>(score);
    map['total'] = Variable<int>(total);
    map['completed_at'] = Variable<DateTime>(completedAt);
    return map;
  }

  TestAttemptsCompanion toCompanion(bool nullToAbsent) {
    return TestAttemptsCompanion(
      id: Value(id),
      topicId: Value(topicId),
      topicTitle: Value(topicTitle),
      score: Value(score),
      total: Value(total),
      completedAt: Value(completedAt),
    );
  }

  factory TestAttempt.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return TestAttempt(
      id: serializer.fromJson<int>(json['id']),
      topicId: serializer.fromJson<String>(json['topicId']),
      topicTitle: serializer.fromJson<String>(json['topicTitle']),
      score: serializer.fromJson<int>(json['score']),
      total: serializer.fromJson<int>(json['total']),
      completedAt: serializer.fromJson<DateTime>(json['completedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'topicId': serializer.toJson<String>(topicId),
      'topicTitle': serializer.toJson<String>(topicTitle),
      'score': serializer.toJson<int>(score),
      'total': serializer.toJson<int>(total),
      'completedAt': serializer.toJson<DateTime>(completedAt),
    };
  }

  TestAttempt copyWith({
    int? id,
    String? topicId,
    String? topicTitle,
    int? score,
    int? total,
    DateTime? completedAt,
  }) => TestAttempt(
    id: id ?? this.id,
    topicId: topicId ?? this.topicId,
    topicTitle: topicTitle ?? this.topicTitle,
    score: score ?? this.score,
    total: total ?? this.total,
    completedAt: completedAt ?? this.completedAt,
  );
  TestAttempt copyWithCompanion(TestAttemptsCompanion data) {
    return TestAttempt(
      id: data.id.present ? data.id.value : this.id,
      topicId: data.topicId.present ? data.topicId.value : this.topicId,
      topicTitle: data.topicTitle.present
          ? data.topicTitle.value
          : this.topicTitle,
      score: data.score.present ? data.score.value : this.score,
      total: data.total.present ? data.total.value : this.total,
      completedAt: data.completedAt.present
          ? data.completedAt.value
          : this.completedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('TestAttempt(')
          ..write('id: $id, ')
          ..write('topicId: $topicId, ')
          ..write('topicTitle: $topicTitle, ')
          ..write('score: $score, ')
          ..write('total: $total, ')
          ..write('completedAt: $completedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, topicId, topicTitle, score, total, completedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is TestAttempt &&
          other.id == this.id &&
          other.topicId == this.topicId &&
          other.topicTitle == this.topicTitle &&
          other.score == this.score &&
          other.total == this.total &&
          other.completedAt == this.completedAt);
}

class TestAttemptsCompanion extends UpdateCompanion<TestAttempt> {
  final Value<int> id;
  final Value<String> topicId;
  final Value<String> topicTitle;
  final Value<int> score;
  final Value<int> total;
  final Value<DateTime> completedAt;
  const TestAttemptsCompanion({
    this.id = const Value.absent(),
    this.topicId = const Value.absent(),
    this.topicTitle = const Value.absent(),
    this.score = const Value.absent(),
    this.total = const Value.absent(),
    this.completedAt = const Value.absent(),
  });
  TestAttemptsCompanion.insert({
    this.id = const Value.absent(),
    required String topicId,
    required String topicTitle,
    required int score,
    required int total,
    required DateTime completedAt,
  }) : topicId = Value(topicId),
       topicTitle = Value(topicTitle),
       score = Value(score),
       total = Value(total),
       completedAt = Value(completedAt);
  static Insertable<TestAttempt> custom({
    Expression<int>? id,
    Expression<String>? topicId,
    Expression<String>? topicTitle,
    Expression<int>? score,
    Expression<int>? total,
    Expression<DateTime>? completedAt,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (topicId != null) 'topic_id': topicId,
      if (topicTitle != null) 'topic_title': topicTitle,
      if (score != null) 'score': score,
      if (total != null) 'total': total,
      if (completedAt != null) 'completed_at': completedAt,
    });
  }

  TestAttemptsCompanion copyWith({
    Value<int>? id,
    Value<String>? topicId,
    Value<String>? topicTitle,
    Value<int>? score,
    Value<int>? total,
    Value<DateTime>? completedAt,
  }) {
    return TestAttemptsCompanion(
      id: id ?? this.id,
      topicId: topicId ?? this.topicId,
      topicTitle: topicTitle ?? this.topicTitle,
      score: score ?? this.score,
      total: total ?? this.total,
      completedAt: completedAt ?? this.completedAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (topicId.present) {
      map['topic_id'] = Variable<String>(topicId.value);
    }
    if (topicTitle.present) {
      map['topic_title'] = Variable<String>(topicTitle.value);
    }
    if (score.present) {
      map['score'] = Variable<int>(score.value);
    }
    if (total.present) {
      map['total'] = Variable<int>(total.value);
    }
    if (completedAt.present) {
      map['completed_at'] = Variable<DateTime>(completedAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('TestAttemptsCompanion(')
          ..write('id: $id, ')
          ..write('topicId: $topicId, ')
          ..write('topicTitle: $topicTitle, ')
          ..write('score: $score, ')
          ..write('total: $total, ')
          ..write('completedAt: $completedAt')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $StudiedTopicsTable studiedTopics = $StudiedTopicsTable(this);
  late final $TestAttemptsTable testAttempts = $TestAttemptsTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    studiedTopics,
    testAttempts,
  ];
}

typedef $$StudiedTopicsTableCreateCompanionBuilder =
    StudiedTopicsCompanion Function({
      required String topicId,
      required DateTime firstOpenedAt,
      Value<int> rowid,
    });
typedef $$StudiedTopicsTableUpdateCompanionBuilder =
    StudiedTopicsCompanion Function({
      Value<String> topicId,
      Value<DateTime> firstOpenedAt,
      Value<int> rowid,
    });

class $$StudiedTopicsTableFilterComposer
    extends Composer<_$AppDatabase, $StudiedTopicsTable> {
  $$StudiedTopicsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get topicId => $composableBuilder(
    column: $table.topicId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get firstOpenedAt => $composableBuilder(
    column: $table.firstOpenedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$StudiedTopicsTableOrderingComposer
    extends Composer<_$AppDatabase, $StudiedTopicsTable> {
  $$StudiedTopicsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get topicId => $composableBuilder(
    column: $table.topicId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get firstOpenedAt => $composableBuilder(
    column: $table.firstOpenedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$StudiedTopicsTableAnnotationComposer
    extends Composer<_$AppDatabase, $StudiedTopicsTable> {
  $$StudiedTopicsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get topicId =>
      $composableBuilder(column: $table.topicId, builder: (column) => column);

  GeneratedColumn<DateTime> get firstOpenedAt => $composableBuilder(
    column: $table.firstOpenedAt,
    builder: (column) => column,
  );
}

class $$StudiedTopicsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $StudiedTopicsTable,
          StudiedTopic,
          $$StudiedTopicsTableFilterComposer,
          $$StudiedTopicsTableOrderingComposer,
          $$StudiedTopicsTableAnnotationComposer,
          $$StudiedTopicsTableCreateCompanionBuilder,
          $$StudiedTopicsTableUpdateCompanionBuilder,
          (
            StudiedTopic,
            BaseReferences<_$AppDatabase, $StudiedTopicsTable, StudiedTopic>,
          ),
          StudiedTopic,
          PrefetchHooks Function()
        > {
  $$StudiedTopicsTableTableManager(_$AppDatabase db, $StudiedTopicsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$StudiedTopicsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$StudiedTopicsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$StudiedTopicsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> topicId = const Value.absent(),
                Value<DateTime> firstOpenedAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => StudiedTopicsCompanion(
                topicId: topicId,
                firstOpenedAt: firstOpenedAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String topicId,
                required DateTime firstOpenedAt,
                Value<int> rowid = const Value.absent(),
              }) => StudiedTopicsCompanion.insert(
                topicId: topicId,
                firstOpenedAt: firstOpenedAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$StudiedTopicsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $StudiedTopicsTable,
      StudiedTopic,
      $$StudiedTopicsTableFilterComposer,
      $$StudiedTopicsTableOrderingComposer,
      $$StudiedTopicsTableAnnotationComposer,
      $$StudiedTopicsTableCreateCompanionBuilder,
      $$StudiedTopicsTableUpdateCompanionBuilder,
      (
        StudiedTopic,
        BaseReferences<_$AppDatabase, $StudiedTopicsTable, StudiedTopic>,
      ),
      StudiedTopic,
      PrefetchHooks Function()
    >;
typedef $$TestAttemptsTableCreateCompanionBuilder =
    TestAttemptsCompanion Function({
      Value<int> id,
      required String topicId,
      required String topicTitle,
      required int score,
      required int total,
      required DateTime completedAt,
    });
typedef $$TestAttemptsTableUpdateCompanionBuilder =
    TestAttemptsCompanion Function({
      Value<int> id,
      Value<String> topicId,
      Value<String> topicTitle,
      Value<int> score,
      Value<int> total,
      Value<DateTime> completedAt,
    });

class $$TestAttemptsTableFilterComposer
    extends Composer<_$AppDatabase, $TestAttemptsTable> {
  $$TestAttemptsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get topicId => $composableBuilder(
    column: $table.topicId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get topicTitle => $composableBuilder(
    column: $table.topicTitle,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get score => $composableBuilder(
    column: $table.score,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get total => $composableBuilder(
    column: $table.total,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get completedAt => $composableBuilder(
    column: $table.completedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$TestAttemptsTableOrderingComposer
    extends Composer<_$AppDatabase, $TestAttemptsTable> {
  $$TestAttemptsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get topicId => $composableBuilder(
    column: $table.topicId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get topicTitle => $composableBuilder(
    column: $table.topicTitle,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get score => $composableBuilder(
    column: $table.score,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get total => $composableBuilder(
    column: $table.total,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get completedAt => $composableBuilder(
    column: $table.completedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$TestAttemptsTableAnnotationComposer
    extends Composer<_$AppDatabase, $TestAttemptsTable> {
  $$TestAttemptsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get topicId =>
      $composableBuilder(column: $table.topicId, builder: (column) => column);

  GeneratedColumn<String> get topicTitle => $composableBuilder(
    column: $table.topicTitle,
    builder: (column) => column,
  );

  GeneratedColumn<int> get score =>
      $composableBuilder(column: $table.score, builder: (column) => column);

  GeneratedColumn<int> get total =>
      $composableBuilder(column: $table.total, builder: (column) => column);

  GeneratedColumn<DateTime> get completedAt => $composableBuilder(
    column: $table.completedAt,
    builder: (column) => column,
  );
}

class $$TestAttemptsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $TestAttemptsTable,
          TestAttempt,
          $$TestAttemptsTableFilterComposer,
          $$TestAttemptsTableOrderingComposer,
          $$TestAttemptsTableAnnotationComposer,
          $$TestAttemptsTableCreateCompanionBuilder,
          $$TestAttemptsTableUpdateCompanionBuilder,
          (
            TestAttempt,
            BaseReferences<_$AppDatabase, $TestAttemptsTable, TestAttempt>,
          ),
          TestAttempt,
          PrefetchHooks Function()
        > {
  $$TestAttemptsTableTableManager(_$AppDatabase db, $TestAttemptsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$TestAttemptsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$TestAttemptsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$TestAttemptsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> topicId = const Value.absent(),
                Value<String> topicTitle = const Value.absent(),
                Value<int> score = const Value.absent(),
                Value<int> total = const Value.absent(),
                Value<DateTime> completedAt = const Value.absent(),
              }) => TestAttemptsCompanion(
                id: id,
                topicId: topicId,
                topicTitle: topicTitle,
                score: score,
                total: total,
                completedAt: completedAt,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String topicId,
                required String topicTitle,
                required int score,
                required int total,
                required DateTime completedAt,
              }) => TestAttemptsCompanion.insert(
                id: id,
                topicId: topicId,
                topicTitle: topicTitle,
                score: score,
                total: total,
                completedAt: completedAt,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$TestAttemptsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $TestAttemptsTable,
      TestAttempt,
      $$TestAttemptsTableFilterComposer,
      $$TestAttemptsTableOrderingComposer,
      $$TestAttemptsTableAnnotationComposer,
      $$TestAttemptsTableCreateCompanionBuilder,
      $$TestAttemptsTableUpdateCompanionBuilder,
      (
        TestAttempt,
        BaseReferences<_$AppDatabase, $TestAttemptsTable, TestAttempt>,
      ),
      TestAttempt,
      PrefetchHooks Function()
    >;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$StudiedTopicsTableTableManager get studiedTopics =>
      $$StudiedTopicsTableTableManager(_db, _db.studiedTopics);
  $$TestAttemptsTableTableManager get testAttempts =>
      $$TestAttemptsTableTableManager(_db, _db.testAttempts);
}
