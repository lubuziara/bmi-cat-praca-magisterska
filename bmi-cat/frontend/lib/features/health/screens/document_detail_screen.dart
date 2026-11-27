import 'dart:convert';
import 'package:flutter/material.dart';
import '../../auth/data/auth_api.dart';
import '../data/health_date.dart';
import '../data/document_export.dart';
import '../widgets/health_page.dart';
part 'document_detail_screen_state.dart';

class DocumentDetailScreen extends StatefulWidget {
  final AuthApi api;
  final int id;
  const DocumentDetailScreen({super.key, required this.api, required this.id});
  @override
  State<DocumentDetailScreen> createState() => _DocumentDetailScreenState();
}
