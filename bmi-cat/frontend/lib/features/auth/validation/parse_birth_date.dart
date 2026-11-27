DateTime? parseBirthDate(String value) {
  final parts = value.trim().split('.');
  if (parts.length != 3) return null;
  final day = int.tryParse(parts[0]),
      month = int.tryParse(parts[1]),
      year = int.tryParse(parts[2]);
  if (day == null || month == null || year == null) return null;
  final date = DateTime(year, month, day);
  return date.day == day && date.month == month && date.year == year
      ? date
      : null;
}
