import 'package:flutter/material.dart';
import '../data/auth_api.dart';
import '../data/passkey_webauthn.dart';
import '../validation/validate_email.dart';
import '../widgets/auth_shell.dart';
import '../widgets/password_field.dart';
import '../widgets/form_message.dart';
import '../widgets/submit_button.dart';
import '../widgets/google_login_button.dart';
part 'login_screen_state.dart';

class LoginScreen extends StatefulWidget {
  final AuthApi api;
  const LoginScreen({super.key, required this.api});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}
