import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../auth/data/auth_api.dart';
import '../widgets/health_page.dart';
part 'calendar_connections_screen_state.dart';

class CalendarConnectionsScreen extends StatefulWidget {
  final AuthApi api;
  const CalendarConnectionsScreen({super.key, required this.api});
  @override
  State<CalendarConnectionsScreen> createState() =>
      _CalendarConnectionsScreenState();
}
