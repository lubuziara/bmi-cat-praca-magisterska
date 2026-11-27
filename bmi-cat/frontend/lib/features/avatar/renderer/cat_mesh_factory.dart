import 'cat_tail_path.dart';
import 'cat_anatomy.dart';
import 'dart:math' as math;
import 'dart:ui';
import '../models/avatar_settings.dart';
import 'mesh_builder.dart';
import 'mesh_face.dart';
import 'vector3.dart';

class CatMeshFactory {
  static List<MeshFace> build(AvatarSettings settings) {
    final mesh = MeshBuilder();
    final anatomy = CatAnatomy(settings);
    final girth = {
      'emaciated': 0.65,
      'slim': 0.82,
      'medium': 1.0,
      'large': 1.28,
      'xxl': 1.52
    }[settings.body]!;
    final kitten = settings.size == 'kitten';
    final bodyScale = kitten ? 0.76 : 1.0;
    final fluff = anatomy.furLength;
    final base = {
      'white': const Color(0xFFF5F2EE),
      'black': const Color(0xFF34313D),
      'ginger': const Color(0xFFD9893E),
      'tabby': const Color(0xFF8E8074),
      'tricolor': const Color(0xFFF5F2EE),
      'ginger_white': const Color(0xFFF5F2EE),
      'ginger_black_white': const Color(0xFFF5F2EE),
      'purple': const Color(0xFFA081CE),
      'yellow': const Color(0xFFF2CD48),
      'red': const Color(0xFFE06964)
    }[settings.coat]!;
    Color coat(Vector3 p) {
      final ginger = const Color(0xFFD88A43), dark = const Color(0xFF49414A);
      if (settings.coat == 'tabby' && math.sin(p.y * 19 + p.x * 10) > 0.63) {
        return dark;
      }
      if (settings.coat == 'ginger_white' && (p.x < -0.18 || p.y > 1.78)) {
        return ginger;
      }
      if (settings.coat == 'ginger_black_white') {
        if (p.x < -0.12 && p.y > 0.45) {
          return ginger;
        }
        if (p.x > 0.2 && p.y > 0.7) {
          return dark;
        }
      }
      if (settings.coat == 'tricolor') {
        final spot = math.sin(p.x * 4.3 + p.y * 1.4 + 0.8) *
                math.cos(p.z * 3.2 - p.y * 2.1) +
            0.12 * math.sin(p.x * 9 + p.y * 3);
        if (spot > 0.15)
          return Color.lerp(base, ginger, ((spot - 0.15) * 5).clamp(0, 1))!;
        if (spot < -0.18)
          return Color.lerp(base, dark, ((-spot - 0.18) * 5).clamp(0, 1))!;
      }
      if (settings.fur == 'hairless') {
        return Color.lerp(base, const Color(0xFFE8B9B3), 0.2)!;
      }
      return base;
    }

    final center = Vector3(0, 0.32 * bodyScale, 0);
    final radius = Vector3((0.55 * girth + fluff) * bodyScale, 0.90 * bodyScale,
        (0.43 * girth + fluff) * bodyScale);
    mesh.ellipsoid(center, radius, base,
        paint: coat, rings: 26, sides: 42, part: 'body');
    // Haunches and front paws form a seated feline silhouette.
    for (final side in [-1.0, 1.0]) {
      mesh.ellipsoid(
          Vector3(side * 0.43 * girth * bodyScale, -0.25 * bodyScale, -0.02),
          Vector3(0.35 * girth * bodyScale, 0.4 * bodyScale, 0.4 * bodyScale),
          base,
          paint: coat);
      mesh.ellipsoid(
          Vector3(side * 0.23 * bodyScale, -0.23 * bodyScale, 0.37 * bodyScale),
          Vector3(0.17 * bodyScale, 0.5 * bodyScale, 0.19 * bodyScale),
          base,
          paint: coat);
      mesh.ellipsoid(
          Vector3(side * 0.23 * bodyScale, -0.62 * bodyScale, 0.5 * bodyScale),
          Vector3(0.2 * bodyScale, 0.13 * bodyScale, 0.26 * bodyScale),
          base,
          paint: coat);
    }
    // Curved 3D tail sits behind and curls around the body.
    final tail = CatTailPath.build(girth, bodyScale, fluff);
    mesh.tube(tail, (0.14 + fluff * 0.5) * bodyScale, base,
        paint: coat, sides: 20);
    final headY = anatomy.headY;
    final headR = anatomy.headRadius.x;
    final faceZ = anatomy.eyeSurface;
    mesh.ellipsoid(anatomy.headCenter, anatomy.headRadius, base,
        paint: coat, rings: 28, sides: 44, part: 'head');
    for (final side in [-1.0, 1.0]) {
      final tip = Vector3(side * 0.44, headY + 0.75, 0.08);
      final a = Vector3(side * 0.20, headY + 0.37, 0.22),
          b = Vector3(side * 0.57, headY + 0.3, 0.15),
          c = Vector3(side * 0.4, headY + 0.36, -0.13);
      mesh.triangle(a, tip, b, coat(tip));
      mesh.triangle(b, tip, c, base);
      mesh.triangle(c, tip, a, base);
      mesh.triangle(
          Vector3(side * 0.28, headY + 0.4, 0.245),
          Vector3(side * 0.435, headY + 0.63, 0.15),
          Vector3(side * 0.51, headY + 0.37, 0.205),
          const Color(0xFFE6A6B6));
      final eyeColor = {
        'green': const Color(0xFF8BAB63),
        'amber': const Color(0xFFE1AB3C),
        'blue': const Color(0xFF68A9DD),
        'brown': const Color(0xFF996539),
        'gray': const Color(0xFF9AA6B4),
        'heterochromia':
            side < 0 ? const Color(0xFF68A9DD) : const Color(0xFFE1AB3C),
        'purple': const Color(0xFFA465D5),
        'pink': const Color(0xFFE279BE),
        'turquoise': const Color(0xFF4ACCBF),
        'red': const Color(0xFFDB4D57)
      }[settings.eyes]!;
      mesh.ellipsoid(
          Vector3(side * anatomy.eyeX, anatomy.eyeY, faceZ),
          Vector3(0.155, kitten ? 0.137 : 0.116, 0.056),
          const Color(0xFF4A3F48),
          rings: 16,
          sides: 28,
          part: 'eye_socket');
      mesh.ellipsoid(Vector3(side * anatomy.eyeX, anatomy.eyeY, faceZ + 0.028),
          Vector3(0.129, kitten ? 0.116 : 0.095, 0.037), eyeColor,
          rings: 16, sides: 28, part: side < 0 ? 'left_iris' : 'right_iris');
      mesh.ellipsoid(
          Vector3(side * anatomy.eyeX, anatomy.eyeY, faceZ + 0.060),
          Vector3(0.030, kitten ? 0.096 : 0.078, 0.011),
          const Color(0xFF24212E),
          rings: 12,
          sides: 18,
          part: 'pupil');
      mesh.ellipsoid(
          Vector3(
              side * anatomy.eyeX - 0.029, anatomy.eyeY + 0.045, faceZ + 0.074),
          const Vector3(0.023, 0.026, 0.007),
          const Color(0xFFFFFEFA),
          rings: 6,
          sides: 8);
      mesh.ellipsoid(
          Vector3(side * 0.105, headY - 0.16, faceZ - 0.003),
          const Vector3(0.155, 0.114, 0.099),
          Color.lerp(base, const Color(0xFFFFF8EE), 0.45)!,
          rings: 16,
          sides: 24);
      for (var w = 0; w < 3; w++) {
        mesh.cone(
            Vector3(side * 0.17, headY - 0.15 - w * 0.025, faceZ + 0.10),
            Vector3(side * (0.69 + w * 0.03), headY - 0.13 + (w - 1) * 0.08,
                faceZ + 0.025),
            0.0035,
            const Color(0xFF756974),
            sides: 4);
      }
    }
    mesh.triangle(
        Vector3(-0.065, headY - 0.105, faceZ + 0.101),
        Vector3(0.065, headY - 0.105, faceZ + 0.101),
        Vector3(0, headY - 0.16, faceZ + 0.115),
        const Color(0xFFD4829B));
    mesh.cone(
        Vector3(0, headY - 0.16, faceZ + 0.103),
        Vector3(0, headY - 0.215, faceZ + 0.098),
        0.005,
        const Color(0xFF745363),
        sides: 4);
    // Soft volumes form the ruff and cheek furnishings. Fur follows the surface,
    // with no outward-pointing cones or geometry over the eyes.
    if (fluff > 0.05) {
      final ruffCenter = Vector3(0, headY - 0.48, 0.04);
      final ruffRadius =
          Vector3(0.48 + fluff, 0.30 + fluff * 0.75, 0.35 + fluff * 0.3);
      mesh.ellipsoid(ruffCenter, ruffRadius, base,
          paint: coat, rings: 22, sides: 36, part: 'ruff');
      mesh.furFlow(ruffCenter, ruffRadius, coat, 0.4, strands: 180);
      for (final side in [-1.0, 1.0]) {
        final cheek = Vector3(side * (headR - 0.09), headY - 0.19, 0.13);
        final cheekRadius =
            Vector3(0.12 + fluff * 0.45, 0.21 + fluff * 0.35, 0.27);
        mesh.ellipsoid(cheek, cheekRadius, base,
            paint: coat, rings: 18, sides: 26, part: 'cheek_fur');
        mesh.furFlow(cheek, cheekRadius, coat, 0.35, strands: 55);
      }
      mesh.furFlow(
          center, radius, coat, settings.fur == 'extra_long' ? 0.48 : 0.28,
          strands: 330);
    }
    return mesh.faces;
  }
}
