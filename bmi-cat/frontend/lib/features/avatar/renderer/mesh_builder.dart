import 'dart:math' as math;
import 'dart:ui';
import 'mesh_face.dart';
import 'vector3.dart';

class MeshBuilder {
  final List<MeshFace> faces = [];
  void ellipsoid(Vector3 center, Vector3 radius, Color color,
      {Color Function(Vector3)? paint,
      int rings = 16,
      int sides = 24,
      String part = 'coat'}) {
    Vector3 point(int i, int j) {
      final lat = math.pi * i / rings, lon = math.pi * 2 * j / sides;
      return center +
          Vector3(
              radius.x * math.sin(lat) * math.cos(lon),
              radius.y * math.cos(lat),
              radius.z * math.sin(lat) * math.sin(lon));
    }

    for (var i = 0; i < rings; i++) {
      for (var j = 0; j < sides; j++) {
        final a = point(i, j),
            b = point(i + 1, j),
            c = point(i + 1, j + 1),
            d = point(i, j + 1);
        final shade = paint?.call((a + b + c + d) * 0.25) ?? color;
        Vector3 normal(Vector3 p) => Vector3(
                (p.x - center.x) / (radius.x * radius.x),
                (p.y - center.y) / (radius.y * radius.y),
                (p.z - center.z) / (radius.z * radius.z))
            .unit;
        faces.add(MeshFace(a, b, c, shade,
            ca: paint?.call(a),
            cb: paint?.call(b),
            cc: paint?.call(c),
            na: normal(a),
            nb: normal(b),
            nc: normal(c),
            part: part));
        faces.add(MeshFace(a, c, d, shade,
            ca: paint?.call(a),
            cb: paint?.call(c),
            cc: paint?.call(d),
            na: normal(a),
            nb: normal(c),
            nc: normal(d),
            part: part));
      }
    }
  }

  void triangle(Vector3 a, Vector3 b, Vector3 c, Color color) =>
      faces.add(MeshFace(a, b, c, color));
  void cone(Vector3 base, Vector3 tip, double radius, Color color,
      {int sides = 7}) {
    final axis = (tip - base).unit;
    final u = axis.cross(const Vector3(0, 0, 1)).unit;
    final v = axis.cross(u).unit;
    for (var i = 0; i < sides; i++) {
      final t = i * math.pi * 2 / sides, next = (i + 1) * math.pi * 2 / sides;
      triangle(base + (u * math.cos(t) + v * math.sin(t)) * radius, tip,
          base + (u * math.cos(next) + v * math.sin(next)) * radius, color);
    }
  }

  void tube(List<Vector3> points, double radius, Color color,
      {Color Function(Vector3)? paint, int sides = 12}) {
    final rings = <List<Vector3>>[];
    for (var i = 0; i < points.length; i++) {
      final tangent = (points[i == points.length - 1 ? i : i + 1] -
              points[i == 0 ? 0 : i - 1])
          .unit;
      final u = tangent.cross(const Vector3(0, 1, 0)).unit;
      final v = tangent.cross(u).unit;
      final r = radius * (1 - 0.6 * i / (points.length - 1));
      rings.add(List.generate(
          sides,
          (j) =>
              points[i] +
              (u * math.cos(j * math.pi * 2 / sides) +
                      v * math.sin(j * math.pi * 2 / sides)) *
                  r));
    }
    for (var i = 0; i < rings.length - 1; i++) {
      for (var j = 0; j < sides; j++) {
        final a = rings[i][j],
            b = rings[i + 1][j],
            c = rings[i + 1][(j + 1) % sides],
            d = rings[i][(j + 1) % sides];
        final shade = paint?.call((a + b + c + d) * 0.25) ?? color;
        faces.add(MeshFace(a, b, c, shade,
            ca: paint?.call(a),
            cb: paint?.call(b),
            cc: paint?.call(c),
            na: (a - points[i]).unit,
            nb: (b - points[i + 1]).unit,
            nc: (c - points[i + 1]).unit,
            part: 'tail'));
        faces.add(MeshFace(a, c, d, shade,
            ca: paint?.call(a),
            cb: paint?.call(c),
            cc: paint?.call(d),
            na: (a - points[i]).unit,
            nb: (c - points[i + 1]).unit,
            nc: (d - points[i]).unit,
            part: 'tail'));
      }
    }
    // Both rims are closed. The distal dome overlaps its rim for a round tip.
    for (var j = 0; j < sides; j++) {
      for (final end in [0, rings.length - 1]) {
        final a = rings[end][j], b = rings[end][(j + 1) % sides];
        faces.add(MeshFace(a, b, points[end], paint?.call(points[end]) ?? color,
            part: 'tail'));
      }
    }
    ellipsoid(points.last,
        Vector3(radius * 0.405, radius * 0.405, radius * 0.405), color,
        paint: paint, rings: 12, sides: sides, part: 'tail_tip');
  }

  void furFlow(Vector3 center, Vector3 radius, Color Function(Vector3) coat,
      double length,
      {int strands = 160}) {
    for (var i = 0; i < strands; i++) {
      final theta = i * 2.39996323;
      final latitude = 0.18 + (i + 0.5) / strands * 2.45;
      Vector3 point(double t, double side) {
        final lat = latitude + t * length;
        final lon = theta + side + 0.045 * math.sin(t * math.pi);
        final lift = 1.008 + 0.13 * math.sin(t * math.pi * 0.85);
        return center +
            Vector3(
                    radius.x * math.sin(lat) * math.cos(lon),
                    radius.y * math.cos(lat),
                    radius.z * math.sin(lat) * math.sin(lon)) *
                lift;
      }

      Color tint(Vector3 p) => Color.lerp(
          coat(p),
          i.isEven ? const Color(0xFFFFFFFF) : const Color(0xFF554B49),
          i.isEven ? 0.065 : 0.03)!;
      Vector3 normal(Vector3 p) => Vector3(
              (p.x - center.x) / (radius.x * radius.x),
              (p.y - center.y) / (radius.y * radius.y),
              (p.z - center.z) / (radius.z * radius.z))
          .unit;
      // Continuous curved locks, with broad roots and fine free ends.
      for (var j = 0; j < 7; j++) {
        final t = j / 7, next = (j + 1) / 7;
        final width = 0.024 * (1 - t), nextWidth = 0.024 * (1 - next);
        final a = point(t, -width),
            b = point(t, width),
            c = point(next, nextWidth),
            d = point(next, -nextWidth);
        faces.add(MeshFace(a, b, c, tint(a),
            ca: tint(a),
            cb: tint(b),
            cc: tint(c),
            na: normal(a),
            nb: normal(b),
            nc: normal(c),
            wa: t * t,
            wb: t * t,
            wc: next * next,
            part: 'fur'));
        faces.add(MeshFace(a, c, d, tint(a),
            ca: tint(a),
            cb: tint(c),
            cc: tint(d),
            na: normal(a),
            nb: normal(c),
            nc: normal(d),
            wa: t * t,
            wb: next * next,
            wc: next * next,
            part: 'fur'));
      }
    }
  }
}
