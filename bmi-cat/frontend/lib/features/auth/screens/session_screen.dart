import '../../home/screens/home_screen.dart';
import '../../avatar/models/avatar_settings.dart';
import '../../avatar/widgets/cat_avatar.dart';
import 'package:flutter/material.dart';
import '../data/auth_api.dart';
import '../widgets/auth_shell.dart';
import '../widgets/form_message.dart';
part 'session_screen_state.dart';

class SessionScreen extends StatefulWidget {
  final AuthApi api;
  const SessionScreen({super.key, required this.api});
  @override
  State<SessionScreen> createState() => _SessionScreenState();
}
