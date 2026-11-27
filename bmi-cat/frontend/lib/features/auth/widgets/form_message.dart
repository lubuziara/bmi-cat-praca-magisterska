import 'package:flutter/material.dart';

class FormMessage extends StatelessWidget {
  final String? message;
  final bool success;
  const FormMessage(this.message, {super.key, this.success = false});
  @override
  Widget build(BuildContext context) => message == null
      ? const SizedBox.shrink()
      : Semantics(
          liveRegion: true,
          child: Container(
              margin: const EdgeInsets.only(bottom: 16),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                  color: success
                      ? const Color(0xFFF0F5EE)
                      : const Color(0xFFFFE9ED),
                  borderRadius: BorderRadius.circular(12)),
              child: Text(message!,
                  style: TextStyle(
                      fontSize: 14,
                      height: 1.4,
                      color: success
                          ? const Color(0xFF34582D)
                          : const Color(0xFF922C45)))),
        );
}
