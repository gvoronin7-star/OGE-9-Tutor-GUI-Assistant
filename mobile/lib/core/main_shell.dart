import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class MainShell extends StatelessWidget {
  final Widget child;

  const MainShell({super.key, required this.child});

  static const _tabs = ['/topics', '/tests', '/progress', '/settings', '/help'];

  int _indexForLocation(String location) {
    final index = _tabs.indexWhere((tab) => location.startsWith(tab));
    return index == -1 ? 0 : index;
  }

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).uri.toString();
    final currentIndex = _indexForLocation(location);

    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: (index) => context.go(_tabs[index]),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.menu_book_outlined),
            label: 'Темы',
          ),
          NavigationDestination(
            icon: Icon(Icons.quiz_outlined),
            label: 'Тесты',
          ),
          NavigationDestination(
            icon: Icon(Icons.bar_chart_outlined),
            label: 'Прогресс',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            label: 'Настройки',
          ),
          NavigationDestination(
            icon: Icon(Icons.help_outline),
            label: 'Помощь',
          ),
        ],
      ),
    );
  }
}
