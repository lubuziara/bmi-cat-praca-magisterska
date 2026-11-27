import 'vector3.dart';

class CatTailPath {
  static List<Vector3> build(double girth, double scale, double fluff) {
    final width = (0.55 * girth + fluff) * scale;
    final depth = (0.43 * girth + fluff) * scale;
    final points = <Vector3>[];
    void curve(Vector3 a, Vector3 b, Vector3 c, Vector3 d) {
      for (var i = points.isEmpty ? 0 : 1; i <= 22; i++) {
        final t = i / 22, u = 1 - t;
        points.add(a * (u * u * u) +
            b * (3 * u * u * t) +
            c * (3 * u * t * t) +
            d * (t * t * t));
      }
    }

    // Root is embedded in the rump, then descends behind the right haunch.
    final root = Vector3(0, -0.12 * scale, -depth * 0.62);
    final side = Vector3(width + 0.12 * scale, -0.60 * scale, 0);
    curve(root, Vector3(0.16 * scale, -0.27 * scale, -depth - 0.20 * scale),
        Vector3(width + 0.20 * scale, -0.58 * scale, -depth * 0.8), side);
    curve(
        side,
        Vector3(width + 0.20 * scale, -0.65 * scale, depth + 0.30 * scale),
        Vector3(0.10 * scale, -0.68 * scale, depth + 0.40 * scale),
        Vector3(-0.35 * scale, -0.64 * scale, depth + 0.18 * scale));
    return points;
  }
}
