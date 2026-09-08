import 'dart:async';

import 'package:dio/dio.dart';

class ApiClient {
  final String baseUrl;
  final Dio _dio;

  ApiClient(this.baseUrl)
    : _dio = Dio(
        BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: const Duration(seconds: 5),
          receiveTimeout: const Duration(seconds: 30),
        ),
      );

  /// На некоторых устройствах первое обращение к недоступному локальному
  /// адресу (ARP-резолюция несуществующего хоста) блокирует TCP-connect
  /// на уровне ОС дольше, чем заявленный [BaseOptions.connectTimeout] -
  /// Dio его в этом случае не соблюдает. Внешний [Future.timeout] с
  /// отменой запроса через [CancelToken] даёт жёсткую верхнюю границу
  /// независимо от поведения ОС.
  Future<bool> checkHealth() async {
    final cancelToken = CancelToken();
    try {
      final response = await _dio
          .get('/health', cancelToken: cancelToken)
          .timeout(
            const Duration(seconds: 6),
            onTimeout: () {
              cancelToken.cancel('health check timed out');
              throw TimeoutException('health check timed out');
            },
          );
      return response.statusCode == 200;
    } on DioException {
      return false;
    } on TimeoutException {
      return false;
    }
  }

  Future<String> ask(String question, {int userId = 0}) async {
    final response = await _dio.post(
      '/api/ask',
      data: {'question': question, 'user_id': userId},
    );
    return response.data['answer'] as String;
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
