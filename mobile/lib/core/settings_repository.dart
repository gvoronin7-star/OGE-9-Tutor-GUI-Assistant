import 'package:shared_preferences/shared_preferences.dart';

class SettingsRepository {
  static const _serverUrlKey = 'server_url';
  static const _serverModeKey = 'server_mode_enabled';
  static const _onboardingSeenKey = 'onboarding_seen';
  // Пусто по умолчанию: 10.0.2.2 - алиас на loopback хоста, работающий
  // только внутри Android-эмулятора, на реальном телефоне такого адреса
  // не существует - см. decisions/2026-09-03_mobile-ui-ux-audit.md.
  static const defaultServerUrl = '';

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

  Future<bool> loadOnboardingSeen() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_onboardingSeenKey) ?? false;
  }

  Future<void> saveOnboardingSeen() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_onboardingSeenKey, true);
  }
}
