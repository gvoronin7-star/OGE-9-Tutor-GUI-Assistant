import 'package:shared_preferences/shared_preferences.dart';

class SettingsRepository {
  static const _serverUrlKey = 'server_url';
  static const _serverModeKey = 'server_mode_enabled';
  static const defaultServerUrl = 'http://10.0.2.2:8000';

  Future<String> loadServerUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_serverUrlKey) ?? defaultServerUrl;
  }

  Future<void> saveServerUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_serverUrlKey, url);
  }

  Future<bool> loadServerModeEnabled() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_serverModeKey) ?? false;
  }

  Future<void> saveServerModeEnabled(bool enabled) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_serverModeKey, enabled);
  }
}
