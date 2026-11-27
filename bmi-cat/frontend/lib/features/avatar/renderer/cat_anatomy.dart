import 'dart:math' as math;
import '../models/avatar_settings.dart';
import 'vector3.dart';

class CatAnatomy {
  final AvatarSettings settings;
  CatAnatomy(this.settings);
  double get bodyScale => settings.size == 'kitten' ? 0.76 : 1;
  double get headY => settings.size == 'kitten' ? 1.10 : 1.40;
  double get furLength => {
        'hairless': 0.0,
        'short': 0.015,
        'long': 0.13,
        'extra_long': 0.22
      }[settings.fur]!;
  Vector3 get headCenter => Vector3(0, headY, 0.18);
  Vector3 get headRadius => Vector3(
      (settings.size == 'kitten' ? 0.56 : 0.54) + furLength * 0.35,
      0.49 + furLength * 0.12,
      0.43 + furLength * 0.16);
  double frontSurface(double x, double y) {
    final r = headRadius;
    return headCenter.z +
        r.z *
            math.sqrt(math.max(
                0,
                1 -
                    x * x / (r.x * r.x) -
                    (y - headY) * (y - headY) / (r.y * r.y)));
  }

  double get eyeY => headY + 0.035;
  double get eyeX => 0.235;
  double get eyeSurface => headCenter.z + headRadius.z + 0.01;
}
