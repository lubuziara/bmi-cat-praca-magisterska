import 'package:flutter/material.dart';
import '../data/health_date.dart';

class EventTile extends StatelessWidget {
  final Map<String, dynamic> event;
  final VoidCallback? onTap;
  final VoidCallback? onDelete;
  const EventTile({super.key, required this.event, this.onTap, this.onDelete});
  @override
  Widget build(BuildContext context) {
    final icon = switch (event['kind']) {
      'vet' => Icons.local_hospital_outlined,
      'medication' => Icons.medication_outlined,
      'document' => Icons.description_outlined,
      'bmi' => Icons.monitor_weight_outlined,
      _ => Icons.restaurant_outlined,
    };
    return Card(
        child: ListTile(
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
            leading: CircleAvatar(
                backgroundColor: const Color(0xFFF0E5F8), child: Icon(icon)),
            title: Text(event['title'] as String),
            subtitle: Text(HealthDate.label(event['occurred_at'] as String?)),
            onTap: onTap,
            trailing: onDelete == null
                ? (onTap == null ? null : const Icon(Icons.chevron_right))
                : IconButton(
                    tooltip: 'Usuń wydarzenie',
                    onPressed: onDelete,
                    icon: const Icon(Icons.delete_outline))));
  }
}
