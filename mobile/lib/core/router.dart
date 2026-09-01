import 'package:go_router/go_router.dart';

import '../features/help/help_screen.dart';
import '../features/progress/progress_screen.dart';
import '../features/search/search_screen.dart';
import '../features/settings/settings_screen.dart';
import '../features/tests/test_result_screen.dart';
import '../features/tests/test_taking_screen.dart';
import '../features/tests/tests_list_screen.dart';
import '../features/topics/topic_detail_screen.dart';
import '../features/topics/topics_list_screen.dart';
import 'main_shell.dart';

final router = GoRouter(
  initialLocation: '/topics',
  routes: [
    ShellRoute(
      builder: (context, state, child) => MainShell(child: child),
      routes: [
        GoRoute(
          path: '/topics',
          builder: (context, state) => const TopicsListScreen(),
          routes: [
            GoRoute(
              path: ':topicId',
              builder: (context, state) =>
                  TopicDetailScreen(topicId: state.pathParameters['topicId']!),
            ),
          ],
        ),
        GoRoute(
          path: '/search',
          builder: (context, state) => const SearchScreen(),
        ),
        GoRoute(
          path: '/tests',
          builder: (context, state) => const TestsListScreen(),
          routes: [
            GoRoute(
              path: ':topicId',
              builder: (context, state) =>
                  TestTakingScreen(topicId: state.pathParameters['topicId']!),
              routes: [
                GoRoute(
                  path: 'result',
                  builder: (context, state) {
                    final extra = state.extra as Map<String, Object?>;
                    return TestResultScreen(
                      score: extra['score']! as int,
                      total: extra['total']! as int,
                      topicTitle: extra['topicTitle']! as String,
                    );
                  },
                ),
              ],
            ),
          ],
        ),
        GoRoute(
          path: '/progress',
          builder: (context, state) => const ProgressScreen(),
        ),
        GoRoute(
          path: '/settings',
          builder: (context, state) => const SettingsScreen(),
        ),
        GoRoute(path: '/help', builder: (context, state) => const HelpScreen()),
      ],
    ),
  ],
);
