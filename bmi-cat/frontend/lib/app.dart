import 'features/auth/screens/verification_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/screens/login_screen.dart';
import 'features/auth/screens/register_screen.dart';
import 'features/auth/screens/forgot_password_screen.dart';
import 'features/auth/screens/reset_password_screen.dart';
import 'features/auth/screens/session_screen.dart';
import 'features/auth/data/auth_api.dart';
import 'features/auth/screens/two_factor_login_screen.dart';

class BmiCatApp extends StatefulWidget {
  final AuthApi? api;
  const BmiCatApp({super.key, this.api});

  @override
  State<BmiCatApp> createState() => _BmiCatAppState();
}

class _BmiCatAppState extends State<BmiCatApp> {
  late final AuthApi client;
  late final Future<bool> restoredSession;

  @override
  void initState() {
    super.initState();
    client = widget.api ?? AuthApi();
    restoredSession = client.restoreSession();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<bool>(
      future: restoredSession,
      builder: (context, snapshot) {
        return _materialApp(snapshot.data == true ? '/session' : '/', client);
      },
    );
  }

  Widget _materialApp(String initialRoute, AuthApi client) {
    return MaterialApp(
      key: ValueKey(initialRoute),
      title: 'BMI Cat',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      locale: const Locale('pl'),
      supportedLocales: const [Locale('pl')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      initialRoute: initialRoute,
      onGenerateRoute: (settings) {
        final uri = Uri.parse(settings.name ?? '/');
        final Widget screen = switch (uri.path) {
          '/verify-registration' => VerificationScreen(api: client),
          '/register' => RegisterScreen(api: client),
          '/forgot-password' => ForgotPasswordScreen(api: client),
          '/reset-password' => ResetPasswordScreen(
              api: client, token: uri.queryParameters['token'] ?? ''),
          '/session' => SessionScreen(api: client),
          '/2fa-login' => TwoFactorLoginScreen(api: client),
          _ => LoginScreen(api: client),
        };
        return MaterialPageRoute(builder: (_) => screen, settings: settings);
      },
    );
  }
}
