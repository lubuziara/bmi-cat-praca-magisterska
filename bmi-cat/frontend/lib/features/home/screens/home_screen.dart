import '../../health/screens/calendar_screen.dart';
import '../../health/screens/bmi_screen.dart';
import '../../health/screens/calorie_screen.dart';
import '../../health/screens/documents_screen.dart';
import '../../health/screens/settings_screen.dart';
import '../../health/screens/notifications_screen.dart';
import 'package:flutter/material.dart';
import '../../auth/data/auth_api.dart';
import '../../avatar/models/avatar_settings.dart';
import '../../avatar/widgets/cat_avatar.dart';
import '../../diary/screens/dashboard_screen.dart';
import '../../diary/widgets/nutrient_bar.dart';
part 'home_screen_state.dart';

class HomeScreen extends StatefulWidget {
  final AuthApi api;
  final Map<String, dynamic> profile;
  const HomeScreen({super.key, required this.api, required this.profile});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}
