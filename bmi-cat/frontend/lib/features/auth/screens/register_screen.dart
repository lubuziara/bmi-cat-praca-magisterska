import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../data/auth_api.dart';
import '../validation/validate_email.dart';
import '../validation/validate_name.dart';
import '../validation/validate_password.dart';
import '../validation/validate_phone.dart';
import '../validation/parse_birth_date.dart';
import '../widgets/auth_shell.dart';
import '../widgets/password_field.dart';
import '../widgets/form_message.dart';
import '../widgets/submit_button.dart';
import '../widgets/birth_date_field.dart';
import '../widgets/form_grid.dart';
import '../../avatar/models/avatar_settings.dart';
import '../../avatar/widgets/avatar_editor.dart';
part 'register_screen_state.dart';

class RegisterScreen extends StatefulWidget {
  final AuthApi api;
  const RegisterScreen({super.key, required this.api});
  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}
