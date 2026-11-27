import 'package:flutter/material.dart';
import '../../auth/data/auth_api.dart';
import '../data/health_date.dart';
import '../widgets/health_page.dart';
import '../widgets/event_tile.dart';
import 'event_editor.dart';
import 'document_detail_screen.dart';
import 'calendar_connections_screen.dart';
part 'calendar_screen_state.dart';

class CalendarScreen extends StatefulWidget {
  final AuthApi api;
  const CalendarScreen({super.key, required this.api});
  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}
