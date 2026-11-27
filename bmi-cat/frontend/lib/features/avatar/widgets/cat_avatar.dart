import 'package:flutter/material.dart';
import '../models/avatar_settings.dart';
import 'glb_avatar_native.dart' if (dart.library.html) 'glb_avatar_web.dart';

class CatAvatar extends StatelessWidget {
  final AvatarSettings settings;
  const CatAvatar({super.key, required this.settings});
  @override
  Widget build(BuildContext context) => ClipRRect(
      borderRadius: BorderRadius.circular(24),
      child: GlbAvatar(settings: settings));
}
