import 'package:flutter/material.dart';

class AppTheme {
  static const purple = Color(0xFF754298);
  static const ink = Color(0xFF382345);
  static ThemeData get light {
    final border = OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: Color(0xFFAA80C2), width: 1.3));
    return ThemeData(
      useMaterial3: true,
      fontFamily: 'BmiRoboto',
      colorScheme: ColorScheme.fromSeed(
          seedColor: purple, primary: purple, surface: const Color(0xFFFFFAFD)),
      scaffoldBackgroundColor: const Color(0xFFFFEEF5),
      textTheme: const TextTheme(
          bodyMedium: TextStyle(fontSize: 16, color: ink),
          bodyLarge: TextStyle(fontSize: 16, color: ink)),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFFFFFCFE),
        border: border,
        enabledBorder: border,
        focusedBorder: border.copyWith(
            borderSide: const BorderSide(color: purple, width: 2)),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 18, vertical: 18),
        errorMaxLines: 3,
      ),
      filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
        minimumSize: const Size.fromHeight(54),
        textStyle: const TextStyle(
            fontSize: 16, fontWeight: FontWeight.w600, fontFamily: 'BmiRoboto'),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      )),
      textButtonTheme: TextButtonThemeData(
          style: TextButton.styleFrom(
        textStyle: const TextStyle(
            fontSize: 14, fontWeight: FontWeight.w600, fontFamily: 'BmiRoboto'),
        minimumSize: const Size(48, 48),
      )),
    );
  }
}
