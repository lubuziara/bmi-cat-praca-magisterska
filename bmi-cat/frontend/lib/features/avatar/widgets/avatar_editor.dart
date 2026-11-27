import 'package:flutter/material.dart';
import '../models/avatar_options.dart';
import '../models/avatar_settings.dart';
import 'cat_avatar.dart';

class AvatarEditor extends StatelessWidget {
  final AvatarSettings value;
  final ValueChanged<AvatarSettings> onChanged;
  const AvatarEditor({super.key, required this.value, required this.onChanged});
  Widget select(String label, String selected, Map<String, String> options,
          ValueChanged<String> change) =>
      Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: DropdownButtonFormField<String>(
              value: selected,
              isExpanded: true,
              decoration: InputDecoration(labelText: label),
              items: options.entries
                  .map((e) => DropdownMenuItem(
                      value: e.key,
                      child: Text(e.value, overflow: TextOverflow.ellipsis)))
                  .toList(),
              onChanged: (v) {
                if (v != null) {
                  change(v);
                }
              }));
  @override
  Widget build(BuildContext context) => LayoutBuilder(builder: (context, c) {
        final preview =
            SizedBox(height: 390, child: CatAvatar(settings: value));
        final controls = Column(children: [
          select('Sierść', value.fur, AvatarOptions.fur,
              (v) => onChanged(value.copyWith(fur: v))),
          select('Umaszczenie', value.coat, AvatarOptions.coat,
              (v) => onChanged(value.copyWith(coat: v))),
          select('Kolor oczu', value.eyes, AvatarOptions.eyes,
              (v) => onChanged(value.copyWith(eyes: v))),
          select('Wielkość', value.size, AvatarOptions.size,
              (v) => onChanged(value.copyWith(size: v))),
          select('Sylwetka', value.body, AvatarOptions.body,
              (v) => onChanged(value.copyWith(body: v))),
        ]);
        if (c.maxWidth >= 650) {
          return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Expanded(child: preview),
            const SizedBox(width: 28),
            Expanded(child: controls)
          ]);
        }
        return Column(
            children: [preview, const SizedBox(height: 24), controls]);
      });
}
