import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

class AuthShell extends StatelessWidget {
  final String title;
  final String subtitle;
  final Widget child;
  final bool back;
  final double maxWidth;
  const AuthShell(
      {super.key,
      required this.title,
      required this.subtitle,
      required this.child,
      this.back = false,
      this.maxWidth = 460});

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
            child: LayoutBuilder(
                builder: (context, constraints) => SingleChildScrollView(
                      padding: EdgeInsets.symmetric(
                          horizontal: constraints.maxWidth < 400 ? 16 : 24,
                          vertical: 24),
                      child: ConstrainedBox(
                        constraints: BoxConstraints(
                            minHeight: constraints.maxHeight - 48),
                        child: Center(
                            child: ConstrainedBox(
                                constraints: BoxConstraints(maxWidth: maxWidth),
                                child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Image.asset('assets/hanging_cat.png',
                                        height: 108,
                                        semanticLabel:
                                            'Logo BMI Cat — wiszący kot'),
                                    const SizedBox(height: 10),
                                    const Text('BMI Cat',
                                        style: TextStyle(
                                            fontSize: 30,
                                            fontWeight: FontWeight.w800,
                                            color: AppTheme.ink,
                                            letterSpacing: -1)),
                                    const SizedBox(height: 22),
                                    Container(
                                      width: double.infinity,
                                      padding: EdgeInsets.all(
                                          constraints.maxWidth < 400 ? 22 : 32),
                                      decoration: BoxDecoration(
                                          color: const Color(0xFFFFFAFD),
                                          borderRadius:
                                              BorderRadius.circular(28),
                                          border: Border.all(
                                              color: const Color(0xFFE6D3EB)),
                                          boxShadow: const [
                                            BoxShadow(
                                                color: Color(0x0D754298),
                                                blurRadius: 32,
                                                offset: Offset(0, 12))
                                          ]),
                                      child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.stretch,
                                          children: [
                                            if (back)
                                              Align(
                                                  alignment:
                                                      Alignment.centerLeft,
                                                  child: TextButton.icon(
                                                      onPressed: () => Navigator
                                                          .pushNamedAndRemoveUntil(
                                                              context,
                                                              '/',
                                                              (_) => false),
                                                      icon: const Icon(
                                                          Icons
                                                              .arrow_back_rounded,
                                                          size: 18),
                                                      label: const Text(
                                                          'Wróć do logowania'))),
                                            Text(title,
                                                textAlign: TextAlign.center,
                                                style: const TextStyle(
                                                    fontSize: 27,
                                                    fontWeight: FontWeight.w700,
                                                    color: AppTheme.ink)),
                                            const SizedBox(height: 10),
                                            Text(subtitle,
                                                textAlign: TextAlign.center,
                                                style: const TextStyle(
                                                    fontSize: 15,
                                                    height: 1.5,
                                                    color: Color(0xFF725D7C))),
                                            const SizedBox(height: 28),
                                            child,
                                          ]),
                                    ),
                                    const SizedBox(height: 20),
                                  ],
                                ))),
                      ),
                    ))),
      );
}
