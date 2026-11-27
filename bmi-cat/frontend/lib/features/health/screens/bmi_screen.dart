import 'package:flutter/material.dart';
import '../../auth/data/auth_api.dart';
import '../data/health_date.dart';
import '../widgets/health_page.dart';
part 'bmi_screen_state.dart';

class BmiScreen extends StatefulWidget {
  final AuthApi api;
  const BmiScreen({super.key, required this.api});
  @override
  State<BmiScreen> createState() => _BmiScreenState();
}
