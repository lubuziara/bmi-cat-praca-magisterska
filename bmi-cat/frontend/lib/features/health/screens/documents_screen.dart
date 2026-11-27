import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../auth/data/auth_api.dart';
import '../data/health_date.dart';
import '../widgets/health_page.dart';
import 'document_detail_screen.dart';
part 'documents_screen_state.dart';

class DocumentsScreen extends StatefulWidget {
  final AuthApi api;
  final ImagePicker? picker;
  const DocumentsScreen({super.key, required this.api, this.picker});
  @override
  State<DocumentsScreen> createState() => _DocumentsScreenState();
}
