import 'package:flutter/material.dart';
import '../validation/parse_birth_date.dart';

class BirthDateField extends StatelessWidget {
  final TextEditingController controller;
  final int maxYears;
  const BirthDateField(
      {super.key, required this.controller, this.maxYears = 120});
  @override
  Widget build(BuildContext context) => TextFormField(
      controller: controller,
      keyboardType: TextInputType.datetime,
      decoration: InputDecoration(
          labelText: 'Data urodzenia',
          hintText: 'DD.MM.RRRR',
          suffixIcon: IconButton(
              tooltip: 'Wybierz datę',
              icon: const Icon(Icons.calendar_month_outlined),
              onPressed: () async {
                final now = DateTime.now();
                final parsed = parseBirthDate(controller.text);
                final initial = parsed != null &&
                        !parsed.isAfter(now) &&
                        !parsed.isBefore(DateTime(now.year - maxYears))
                    ? parsed
                    : now;
                final selected = await showDatePicker(
                    context: context,
                    initialDate: initial,
                    firstDate: DateTime(now.year - maxYears),
                    lastDate: now);
                if (selected != null) {
                  controller.text =
                      '${selected.day.toString().padLeft(2, '0')}.${selected.month.toString().padLeft(2, '0')}.${selected.year}';
                }
              })),
      validator: (value) {
        final date = parseBirthDate(value ?? ''), now = DateTime.now();
        if (date == null ||
            date.isAfter(now) ||
            date.isBefore(DateTime(now.year - maxYears))) {
          return 'Podaj poprawną datę DD.MM.RRRR, nie późniejszą niż dziś.';
        }
        return null;
      });
}
