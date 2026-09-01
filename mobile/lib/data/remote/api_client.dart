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

  Future<bool> checkHealth() async {
    try {
      final response = await _dio.get('/health');
      return response.statusCode == 200;
    } on DioException {
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
