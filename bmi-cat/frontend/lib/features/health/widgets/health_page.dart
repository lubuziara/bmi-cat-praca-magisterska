import 'package:flutter/material.dart';

class HealthPage extends StatelessWidget {
  final String title;
  final List<Widget> children;
  final List<Widget>? actions;
  const HealthPage(
      {super.key, required this.title, required this.children, this.actions});
  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: Text(title), actions: actions),
      body: Center(
          child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 840),
              child: ListView(
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 40),
                  children: children))));
}
