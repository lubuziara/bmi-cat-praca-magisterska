import 'package:flutter/material.dart';
import '../../auth/data/auth_api.dart';
import '../widgets/health_page.dart';
import 'calendar_connections_screen.dart';
import '../../auth/screens/account_security_screen.dart';
part 'settings_screen_state.dart';

class SettingsScreen extends StatefulWidget {
  final AuthApi api;
  const SettingsScreen({super.key, required this.api});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}
