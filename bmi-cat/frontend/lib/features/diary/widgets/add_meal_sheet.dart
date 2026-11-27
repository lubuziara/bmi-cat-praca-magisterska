import 'package:flutter/material.dart';

class AddMealSheet extends StatefulWidget {
  final List<dynamic> foods;
  final String period;
  final Future<void> Function(String, double) onSave;
  const AddMealSheet(
      {super.key,
      required this.foods,
      required this.period,
      required this.onSave});
  @override
  State<AddMealSheet> createState() => _AddMealSheetState();
}

class _AddMealSheetState extends State<AddMealSheet> {
  final quantity = TextEditingController(text: '100');
  final search = TextEditingController();
  bool saving = false;
  String? error;
  double? get grams =>
      double.tryParse(quantity.text.trim().replaceAll(',', '.'));
  @override
  void dispose() {
    quantity.dispose();
    search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final food = widget.foods.first as Map<String, dynamic>;
    final visible = (food['name'] as String)
        .toLowerCase()
        .contains(search.text.toLowerCase().trim());
    final valid =
        grams != null && grams!.isFinite && grams! > 0 && grams! <= 1000;
    return Padding(
        padding: EdgeInsets.fromLTRB(
            24, 20, 24, 24 + MediaQuery.viewInsetsOf(context).bottom),
        child: SingleChildScrollView(
            child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
              Text('Dodaj posiłek · ${widget.period}',
                  style: const TextStyle(
                      fontSize: 23, fontWeight: FontWeight.bold)),
              const SizedBox(height: 20),
              TextField(
                  controller: search,
                  onChanged: (_) => setState(() {}),
                  decoration: const InputDecoration(
                      labelText: 'Szukaj karmy',
                      prefixIcon: Icon(Icons.search))),
              const SizedBox(height: 16),
              if (!visible)
                const Text('Brak pasujących produktów.')
              else ...[
                ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const CircleAvatar(child: Icon(Icons.restaurant)),
                    title: Text(food['name']),
                    subtitle: Text(food['description'])),
                Text(
                    'W 100 g: ${food['kcal']} kcal · B ${food['protein']} g · T ${food['fat']} g · W ${food['carbs']} g',
                    style: const TextStyle(fontSize: 12)),
                const SizedBox(height: 20),
                TextField(
                    controller: quantity,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    onChanged: (_) => setState(() {}),
                    decoration: InputDecoration(
                        labelText: 'Ile zjadł kot?',
                        suffixText: 'g',
                        helperText: 'Wpisz porcję większą od 0, maks. 1000 g.',
                        errorText:
                            valid ? null : 'Podaj poprawną liczbę gramów.')),
                Wrap(spacing: 8, children: [
                  for (final portion in [50, 100, 200])
                    ActionChip(
                        label: Text(portion == 200
                            ? 'Cała puszka · 200 g'
                            : '$portion g'),
                        onPressed: saving
                            ? null
                            : () => setState(() => quantity.text = '$portion'))
                ]),
                const SizedBox(height: 12),
                Text(
                    'Porcja: ${valid ? ((food['kcal'] as num) * grams! / 100).toStringAsFixed(1) : '—'} kcal',
                    style: const TextStyle(
                        fontSize: 20, fontWeight: FontWeight.bold)),
                if (error != null)
                  Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      child: Text(error!,
                          style: const TextStyle(color: Colors.red))),
                const SizedBox(height: 16),
                FilledButton(
                    onPressed: !valid || saving
                        ? null
                        : () async {
                            setState(() {
                              saving = true;
                              error = null;
                            });
                            try {
                              await widget.onSave(food['id'], grams!);
                              if (context.mounted) Navigator.pop(context);
                            } catch (e) {
                              if (mounted)
                                setState(() {
                                  error = e.toString();
                                  saving = false;
                                });
                            }
                          },
                    child: Text(saving ? 'Zapisuję…' : 'Dodaj porcję')),
              ],
            ])));
  }
}
