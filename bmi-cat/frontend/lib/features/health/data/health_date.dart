class HealthDate {
  static String day(DateTime value) =>
      '${value.year}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';
  static String timestamp(DateTime value) {
    final local = value.toLocal();
    final offset = local.timeZoneOffset;
    final sign = offset.isNegative ? '-' : '+';
    return '${local.toIso8601String()}$sign${offset.inHours.abs().toString().padLeft(2, '0')}:${(offset.inMinutes.abs() % 60).toString().padLeft(2, '0')}';
  }

  static String label(String? value) {
    if (value == null) return 'Cały dzień';
    final date = DateTime.parse(value).toLocal();
    return '${date.day}.${date.month.toString().padLeft(2, '0')}.${date.year} • ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
  }
}
