import 'package:flutter/material.dart';

class HelpScreen extends StatelessWidget {
  const HelpScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Помощь')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: const [
          _HelpSection(
            title: 'Как пользоваться приложением',
            body:
                'Вкладка «Темы» — статьи по всем 6 официальным темам ОГЭ по '
                'обществознанию. Вкладка «Тесты» — проверка знаний по теме, '
                'вопросы разного уровня сложности. Вкладка «Прогресс» — '
                'сколько тем изучено, сколько тестов пройдено и с какой '
                'точностью.',
          ),
          _HelpSection(
            title: 'Работает офлайн',
            body:
                'Все темы и тесты хранятся на устройстве — интернет для '
                'занятий не нужен. Прогресс тоже сохраняется локально.',
          ),
          _HelpSection(
            title: 'О приложении',
            body:
                'OGE-9-Tutor Mobile — версия десктопного помощника для '
                'подготовки к ОГЭ по обществознанию.',
          ),
        ],
      ),
    );
  }
}

class _HelpSection extends StatelessWidget {
  final String title;
  final String body;

  const _HelpSection({required this.title, required this.body});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(body, style: Theme.of(context).textTheme.bodyMedium),
        ],
      ),
    );
  }
}
