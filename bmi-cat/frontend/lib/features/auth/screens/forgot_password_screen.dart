import 'package:flutter/material.dart';
import '../data/auth_api.dart';
import '../validation/validate_email.dart';
import '../widgets/auth_shell.dart';
import '../widgets/form_message.dart';
import '../widgets/submit_button.dart';
part 'forgot_password_screen_state.dart';

class ForgotPasswordScreen extends StatefulWidget {
  final AuthApi api;
  const ForgotPasswordScreen({super.key, required this.api});
  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}
