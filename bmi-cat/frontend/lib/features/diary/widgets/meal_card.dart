import 'package:flutter/material.dart';

class MealCard extends StatelessWidget {
  final String title, period;
  final IconData icon;
  final List<dynamic> entries;
  final VoidCallback onAdd;
  final void Function(int) onRemove;
  final bool busy;
  const MealCard(
      {super.key,
      required this.title,
      required this.period,
      required this.icon,
      required this.entries,
      required this.onAdd,
      required this.onRemove,
      this.busy = false});
  @override
  Widget build(BuildContext context) {
    final rows = entries.where((e) => e['period'] == period).toList();
    final kcal = rows.fold<num>(0, (v, e) => v + (e['kcal'] as num));
    return Card(
        elevation: 0,
        color: const Color(0xFFFFFAFD),
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
            side: const BorderSide(color: Color(0xFFE6D4EE))),
        child: Padding(
            padding: const EdgeInsets.all(20),
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Icon(icon, color: const Color(0xFF9972B4)),
                const SizedBox(width: 12),
                Expanded(
                    child: Text(title,
                        style: const TextStyle(
                            fontSize: 21, fontWeight: FontWeight.bold))),
                Text('${kcal.round()} kcal',
                    style: const TextStyle(color: Color(0xFF876D94))),
                const SizedBox(width: 12),
                IconButton.filled(
                    tooltip: 'Dodaj posiłek — $title',
                    onPressed: busy ? null : onAdd,
                    icon: const Icon(Icons.add))
              ]),
              if (rows.isEmpty)
                const Padding(
                    padding: EdgeInsets.symmetric(vertical: 22),
                    child: Text(
                        'Jeszcze pusto w miseczce.\nDodaj zjedzoną porcję przyciskiem +.',
                        style:
                            TextStyle(color: Color(0xFF917D9C), height: 1.6))),
              for (final row in rows)
                Padding(
                    padding: const EdgeInsets.only(top: 14),
                    child: Row(children: [
                      const Icon(Icons.restaurant_rounded,
                          color: Color(0xFFBA97C8)),
                      const SizedBox(width: 12),
                      Expanded(
                          child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                            Text(row['name'],
                                style: const TextStyle(
                                    fontWeight: FontWeight.w600)),
                            Text('${row['grams']} g · dane demo',
                                style: const TextStyle(
                                    fontSize: 12, color: Color(0xFF917D9C)))
                          ])),
                      Text('${(row['kcal'] as num).round()} kcal'),
                      IconButton(
                          tooltip: 'Usuń porcję',
                          onPressed:
                              busy ? null : () => onRemove(row['id'] as int),
                          icon: const Icon(Icons.close, size: 18))
                    ])),
            ])));
  }
}
