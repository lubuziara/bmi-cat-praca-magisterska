import 'dart:ui';
import 'vector3.dart';

class MeshFace {
  final Vector3 a, b, c;
  final Color color;
  final Color? ca, cb, cc;
  final Vector3? na, nb, nc;
  final String part;
  final double wa, wb, wc;
  const MeshFace(this.a, this.b, this.c, this.color,
      {this.ca,
      this.cb,
      this.cc,
      this.na,
      this.nb,
      this.nc,
      this.part = 'coat',
      this.wa = 0,
      this.wb = 0,
      this.wc = 0});
}
