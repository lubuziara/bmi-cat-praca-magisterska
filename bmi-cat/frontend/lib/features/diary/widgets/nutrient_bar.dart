import 'package:flutter/material.dart';

class NutrientBar extends StatelessWidget {
  final Map<String, dynamic> totals;
  final num target;
  final VoidCallback? onOpenDiary;
  const NutrientBar(
      {super.key,
      required this.totals,
      required this.target,
      this.onOpenDiary});
  @override
  Widget build(BuildContext context) => SafeArea(
      top: false,
      child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: const BoxDecoration(
              color: Color(0xFFFFFAFD),
              border: Border(top: BorderSide(color: Color(0xFFE5D5ED)))),
          child: Center(
              heightFactor: 1,
              child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 960),
                  child: Row(children: [
                    for (final item in [
                      ('kcal', 'Kalorie', const Color(0xFF9C77C7)),
                      ('protein', 'Białko', const Color(0xFF6AB5C9)),
                      ('fat', 'Tłuszcze', const Color(0xFFD3AD61)),
                      ('carbs', 'Węgle', const Color(0xFFBF87B4))
                    ])
                      Expanded(
                          child: Padding(
                              padding:
                                  const EdgeInsets.symmetric(horizontal: 4),
                              child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    ClipRRect(
                                        borderRadius: BorderRadius.circular(6),
                                        child: LinearProgressIndicator(
                                            value: item.$1 == 'kcal'
                                                ? ((totals['kcal'] as num) /
                                                        target)
                                                    .clamp(0, 1)
                                                    .toDouble()
                                                : 1,
                                            color: item.$3,
                                            backgroundColor:
                                                const Color(0xFFEDE4F0),
                                            minHeight: 5)),
                                    const SizedBox(height: 8),
                                    Text(item.$2,
                                        style: const TextStyle(fontSize: 12)),
                                    Text(
                                        '${(totals[item.$1] as num).toStringAsFixed(item.$1 == 'kcal' ? 0 : 1).replaceAll('.', ',')}${item.$1 == 'kcal' ? '' : ' g'}',
                                        style: const TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.bold)),
                                    Text(
                                        item.$1 == 'kcal'
                                            ? '/ $target kcal'
                                            : 'zjedzone',
                                        style: const TextStyle(
                                            fontSize: 11,
                                            color: Color(0xFF856D91))),
                                  ]))),
                    if (onOpenDiary != null) ...[
                      const SizedBox(width: 8),
                      IconButton.filled(
                          tooltip: 'Przejdź do dziennika posiłków',
                          onPressed: onOpenDiary,
                          icon: const Icon(Icons.add))
                    ],
                  ])))));
}
