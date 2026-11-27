import 'package:flutter/material.dart';
import '../../auth/data/auth_api.dart';
import '../widgets/nutrient_bar.dart';
import '../widgets/meal_card.dart';
import '../widgets/add_meal_sheet.dart';
part 'dashboard_screen_state.dart';

class DashboardScreen extends StatefulWidget {
  final AuthApi api;
  final Map<String, dynamic> profile;
  const DashboardScreen({super.key, required this.api, required this.profile});
  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}
