import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../data/auth_api.dart';
import '../widgets/auth_shell.dart';
import '../widgets/form_message.dart';
part 'verification_screen_state.dart';

class VerificationScreen extends StatefulWidget {
  final AuthApi api;
  const VerificationScreen({super.key, required this.api});
  @override
  State<VerificationScreen> createState() => _VerificationScreenState();
}
