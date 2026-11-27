import 'package:flutter/material.dart';
import '../../auth/data/auth_api.dart';
import '../data/health_date.dart';
import '../widgets/event_tile.dart';
import '../widgets/health_page.dart';
import 'calendar_screen.dart';
part 'notifications_screen_state.dart';

class NotificationsScreen extends StatefulWidget {
  final AuthApi api;
  const NotificationsScreen({super.key, required this.api});
  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}
