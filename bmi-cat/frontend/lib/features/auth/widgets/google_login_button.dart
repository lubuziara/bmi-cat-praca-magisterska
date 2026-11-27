import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../data/auth_api.dart';
import 'google_web_button_stub.dart'
    if (dart.library.html) 'google_web_button.dart';
part 'google_login_button_state.dart';

class GoogleLoginButton extends StatefulWidget {
  final AuthApi api;
  final bool enabled;
  final VoidCallback onSuccess;
  final ValueChanged<String> onError;
  const GoogleLoginButton(
      {super.key,
      required this.api,
      required this.enabled,
      required this.onSuccess,
      required this.onError});
  @override
  State<GoogleLoginButton> createState() => _GoogleLoginButtonState();
}
