import 'dart:math';
import 'package:flutter/material.dart';
import '../../auth/data/auth_api.dart';
import '../../diary/screens/dashboard_screen.dart';
import '../widgets/health_page.dart';
part 'calorie_screen_state.dart';

enum CalorieGoal {
  lose('Schudnąć', .8),
  maintain('Utrzymać wagę', 1),
  gain('Przytyć', 1.2);

  final String label;
  final double multiplier;
  const CalorieGoal(this.label, this.multiplier);
}

class CalorieScreen extends StatefulWidget {
  final AuthApi api;
  final Map<String, dynamic> profile;
  const CalorieScreen({super.key, required this.api, required this.profile});
  @override
  State<CalorieScreen> createState() => _CalorieScreenState();
}
