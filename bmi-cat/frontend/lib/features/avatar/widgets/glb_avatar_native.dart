import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/avatar_settings.dart';

class GlbAvatar extends StatefulWidget {
  final AvatarSettings settings;
  final bool measurementMode;
  const GlbAvatar(
      {super.key, required this.settings, this.measurementMode = false});
  @override
  State<GlbAvatar> createState() => _GlbAvatarState();
}

class _GlbAvatarState extends State<GlbAvatar> {
  MethodChannel? channel;
  @override
  void didUpdateWidget(GlbAvatar old) {
    super.didUpdateWidget(old);
    channel?.invokeMethod<void>('settings', widget.settings.toJson());
    channel?.invokeMethod<void>('view', widget.measurementMode);
  }

  @override
  Widget build(BuildContext context) {
    if (defaultTargetPlatform != TargetPlatform.android) {
      return const ColoredBox(
          color: Color(0xFFF1E8F7),
          child: Center(
              child:
                  Text('Model 3D dostępny w wersji webowej i na Androidzie.')));
    }
    return AndroidView(
        viewType: 'bmi-cat/glb',
        creationParams: widget.settings.toJson(),
        creationParamsCodec: const StandardMessageCodec(),
        onPlatformViewCreated: (id) {
          channel = MethodChannel('bmi-cat/glb/$id');
          channel?.invokeMethod<void>('view', widget.measurementMode);
        });
  }
}
