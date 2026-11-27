import 'package:flutter/material.dart';
import '../../auth/data/auth_api.dart';
import '../data/health_date.dart';
import '../widgets/health_page.dart';
part 'event_editor_state.dart';

class EventEditor extends StatefulWidget {
  final AuthApi api;
  final DateTime day;
  const EventEditor({super.key, required this.api, required this.day});
  @override
  State<EventEditor> createState() => _EventEditorState();
}
