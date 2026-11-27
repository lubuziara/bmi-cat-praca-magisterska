import 'fur_motion.dart';
import 'dart:math' as math;
import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'mesh_face.dart';
import 'vector3.dart';

class CatPainter extends CustomPainter {
  final List<MeshFace> faces;
  final double yaw, pitch;
  final Animation<double>? motion;
  CatPainter(this.faces, this.yaw, this.pitch, {this.motion})
      : super(repaint: motion);
  @override
  void paint(Canvas canvas, Size size) {
    final scale = math.min(size.width / 3.2, size.height / 3.5);
    final center = Offset(size.width / 2, size.height * 0.66);
    canvas.drawOval(
        Rect.fromCenter(
            center: Offset(center.dx, center.dy + scale * 0.78),
            width: scale * 2.1,
            height: scale * 0.25),
        Paint()
          ..color = const Color(0x23754298)
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10));
    final rotated = faces
        .map((f) => MeshFace(
            FurMotion.displace(f.a, f.wa, motion?.value ?? 0)
                .rotate(yaw, pitch),
            FurMotion.displace(f.b, f.wb, motion?.value ?? 0)
                .rotate(yaw, pitch),
            FurMotion.displace(f.c, f.wc, motion?.value ?? 0)
                .rotate(yaw, pitch),
            f.color,
            na: f.na?.rotate(yaw, pitch),
            nb: f.nb?.rotate(yaw, pitch),
            nc: f.nc?.rotate(yaw, pitch),
            ca: f.ca,
            cb: f.cb,
            cc: f.cc,
            part: f.part))
        .toList();
    rotated.sort(
        (a, b) => (a.a.z + a.b.z + a.c.z).compareTo(b.a.z + b.b.z + b.c.z));
    final positions = Float32List(rotated.length * 6),
        colors = Int32List(rotated.length * 3);
    final light = const Vector3(-0.5, 0.8, 1.4).unit;
    var vertex = 0;
    for (final f in rotated) {
      final fallback = (f.b - f.a).cross(f.c - f.a).unit;
      final points = [f.a, f.b, f.c],
          normals = [f.na ?? fallback, f.nb ?? fallback, f.nc ?? fallback];
      for (var i = 0; i < 3; i++) {
        final p = points[i], n = normals[i];
        final perspective = 6 / (6 - p.z);
        positions[vertex * 2] = center.dx + p.x * scale * perspective;
        positions[vertex * 2 + 1] = center.dy - p.y * scale * perspective;
        final color = [f.ca ?? f.color, f.cb ?? f.color, f.cc ?? f.color][i];
        final brightness = 0.55 + 0.45 * math.max(0, n.dot(light));
        colors[vertex] = (255 << 24) |
            ((color.r * 255 * brightness).round() << 16) |
            ((color.g * 255 * brightness).round() << 8) |
            (color.b * 255 * brightness).round();
        vertex++;
      }
    }
    // One vertex batch gives smooth interpolated lighting instead of flat polygon shading.
    final vertices =
        ui.Vertices.raw(ui.VertexMode.triangles, positions, colors: colors);
    canvas.drawVertices(
        vertices,
        BlendMode.srcOver,
        Paint()
          ..color = Colors.white
          ..isAntiAlias = true);
    vertices.dispose();
  }

  @override
  bool shouldRepaint(CatPainter oldDelegate) =>
      oldDelegate.faces != faces ||
      oldDelegate.yaw != yaw ||
      oldDelegate.pitch != pitch;
}
