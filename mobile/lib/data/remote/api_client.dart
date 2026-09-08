import 'package:dio/dio.dart';

import '../../core/models.dart';

class ApiClient {
  final String baseUrl;
  final Dio _dio;

  /// `BaseOptions.baseUrl=` парсит значение через `Uri.parse` сразу же,
  /// в конструкторе - без схемы («192.168.1.10:8000», ровно то, что
  /// подсказка над полем в `settings_screen.dart` показывает без
  /// примера «http://») текст до первого `:` читается как схема URI,
  /// схема не может начинаться с цифры - `Uri.parse` кидает
  /// `FormatException` синхронно, до того как выполнится хоть одна
  /// строка `checkHealth()`. Раньше это стреляло необработанным
  /// исключением наружу из `_checkConnection()`/`_saveUrl()`
  /// (оборачивающих его не было) и насовсем оставляло экран в
  /// состоянии «проверяю» - выглядело как зависшая сетевая проверка,
  /// хотя сеть тут ни при чём.
  ApiClient(this.baseUrl)
    : _dio = Dio(
        BaseOptions(
          baseUrl: baseUrl.contains('://') ? baseUrl : 'http://$baseUrl',
          connectTimeout: const Duration(seconds: 5),
          receiveTimeout: const Duration(seconds: 30),
        ),
      );

  Future<bool> checkHealth() async {
    try {
      final response = await _dio.get('/health');
      return response.statusCode == 200;
    } on DioException {
      return false;
    }
  }

  Future<AskResult> ask(String question, {int userId = 0}) async {
    final response = await _dio.post(
      '/api/ask',
      data: {'question': question, 'user_id': userId},
    );
    return AskResult.fromJson(response.data as Map<String, dynamic>);
  }

  Future<Map<String, dynamic>> generateTest(
    String topic, {
    String difficulty = 'medium',
    int numQuestions = 5,
  }) async {
    final response = await _dio.post(
      '/api/tests/generate',
      data: {
        'topic': topic,
        'difficulty': difficulty,
        'num_questions': numQuestions,
      },
    );
    return response.data as Map<String, dynamic>;
  }
}
