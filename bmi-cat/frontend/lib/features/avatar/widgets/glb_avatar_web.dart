// Browser implementation; all assets are bundled and loaded from our own origin.
// ignore_for_file: deprecated_member_use
import 'dart:async';
import 'dart:html' as html;
import 'dart:ui_web' as ui;
import 'package:flutter/material.dart';
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
  static int nextId = 0;
  late final String viewType;
  late final html.IFrameElement frame;
  StreamSubscription<html.MessageEvent>? subscription;
  void send() {
    frame.contentWindow?.postMessage(
        {'type': 'bmi-cat-settings', 'settings': widget.settings.toJson()},
        html.window.location.origin);
    frame.contentWindow?.postMessage(
        {'type': 'bmi-cat-view', 'measurement': widget.measurementMode},
        html.window.location.origin);
  }

  @override
  void initState() {
    super.initState();
    viewType = 'bmi-cat-glb-${nextId++}';
    frame = html.IFrameElement()
      ..src = 'assets/assets/avatar3d/index.html'
      ..title = 'Interaktywny model kota 3D'
      ..style.border = '0'
      ..style.width = '100%'
      ..style.height = '100%';
    subscription = html.window.onMessage.listen((e) {
      if (e.source == frame.contentWindow &&
          e.origin == html.window.location.origin &&
          e.data is Map &&
          e.data['type'] == 'bmi-cat-ready') send();
    });
    ui.platformViewRegistry.registerViewFactory(viewType, (_) => frame);
  }

  @override
  void didUpdateWidget(GlbAvatar old) {
    super.didUpdateWidget(old);
    send();
  }

  @override
  void dispose() {
    subscription?.cancel();
    frame.src = 'about:blank';
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => HtmlElementView(viewType: viewType);
}
