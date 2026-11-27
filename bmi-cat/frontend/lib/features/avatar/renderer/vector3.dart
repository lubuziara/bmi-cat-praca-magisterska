import 'dart:math' as math;

class Vector3 {
  final double x, y, z;
  const Vector3(this.x, this.y, this.z);
  Vector3 operator +(Vector3 v) => Vector3(x + v.x, y + v.y, z + v.z);
  Vector3 operator -(Vector3 v) => Vector3(x - v.x, y - v.y, z - v.z);
  Vector3 operator *(double s) => Vector3(x * s, y * s, z * s);
  Vector3 cross(Vector3 v) =>
      Vector3(y * v.z - z * v.y, z * v.x - x * v.z, x * v.y - y * v.x);
  double dot(Vector3 v) => x * v.x + y * v.y + z * v.z;
  Vector3 get unit {
    final d = math.sqrt(dot(this));
    return d < 0.00001 ? const Vector3(0, 1, 0) : this * (1 / d);
  }

  Vector3 rotate(double yaw, double pitch) {
    final a = x * math.cos(yaw) + z * math.sin(yaw),
        b = z * math.cos(yaw) - x * math.sin(yaw);
    return Vector3(a, y * math.cos(pitch) - b * math.sin(pitch),
        y * math.sin(pitch) + b * math.cos(pitch));
  }
}
