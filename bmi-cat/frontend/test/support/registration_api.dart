import 'package:bmi_cat/features/auth/data/auth_api.dart';

class RegistrationApi extends AuthApi {
  Map<String, dynamic>? payload;
  @override
  Future<void> registerProfile(Map<String, dynamic> profile) async {
    payload = profile;
  }

  @override
  Future<Map<String, dynamic>> request(String path,
          {Map<String, dynamic>? body, bool get = false, bool remove = false}) async =>
      {'email_verified': false, 'phone_verified': false};
}
