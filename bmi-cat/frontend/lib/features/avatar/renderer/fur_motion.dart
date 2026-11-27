import 'dart:math' as math;
import 'vector3.dart';

class FurMotion {
  static Vector3 displace(Vector3 point, double weight, double phase) {
    final wave = phase * math.pi * 2 + point.y * 3 + point.x * 2;
    return point +
        Vector3(math.sin(wave) * 0.038, math.cos(wave + 0.7) * 0.012,
                math.sin(wave + 1.1) * 0.025) *
            weight;
  }
}
