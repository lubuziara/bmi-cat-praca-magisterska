import 'package:flutter/material.dart';

class SubmitButton extends StatelessWidget {
  final bool busy;
  final String label;
  final VoidCallback onPressed;
  const SubmitButton(
      {super.key,
      required this.busy,
      required this.label,
      required this.onPressed});
  @override
  Widget build(BuildContext context) => FilledButton(
      onPressed: busy ? null : onPressed,
      child: busy
          ? const SizedBox(
              width: 22,
              height: 22,
              child: CircularProgressIndicator(
                  strokeWidth: 2, semanticsLabel: 'Trwa przetwarzanie'))
          : Text(label));
}
