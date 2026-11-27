import 'package:flutter/material.dart';

class FormGrid extends StatelessWidget {
  final List<Widget> children;
  const FormGrid({super.key, required this.children});
  @override
  Widget build(BuildContext context) => LayoutBuilder(builder: (context, c) {
        final width = c.maxWidth >= 600 ? (c.maxWidth - 20) / 2 : c.maxWidth;
        return Wrap(
            spacing: 20,
            runSpacing: 20,
            children: children
                .map((child) => SizedBox(width: width, child: child))
                .toList());
      });
}
