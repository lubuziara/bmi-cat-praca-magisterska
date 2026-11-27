import 'package:flutter/material.dart';
import '../data/api_exception.dart';
import '../data/auth_api.dart';
import '../data/passkey_webauthn.dart';
import '../widgets/auth_shell.dart';
import '../widgets/form_message.dart';
import '../widgets/submit_button.dart';

class TwoFactorLoginScreen extends StatefulWidget {
  final AuthApi api;
  const TwoFactorLoginScreen({super.key, required this.api});
  @override State<TwoFactorLoginScreen> createState() => _TwoFactorLoginScreenState();
}

class _TwoFactorLoginScreenState extends State<TwoFactorLoginScreen> {
  final code = TextEditingController();
  bool recovery = false, busy = false;
  String? error;
  @override void dispose() { code.dispose(); super.dispose(); }
  Future<void> verify() async {
    if (busy || code.text.trim().length < 6) return;
    setState(() { busy = true; error = null; });
    try {
      await widget.api.verifyMfa(code.text.trim());
      if (mounted) Navigator.pushNamedAndRemoveUntil(context,
          widget.api.needsVerification ? '/verify-registration' : '/session', (_) => false);
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => error = e.message.toLowerCase().contains('wygas')
          ? 'Sesja weryfikacji wygasła. Zaloguj się ponownie.'
          : 'Kod jest nieprawidłowy lub wygasł.');
    } finally { if (mounted) setState(() => busy = false); }
  }
  Future<void> passkey() async { if (busy) return; setState(() { busy = true; error = null; }); try { await widget.api.verifyStepUpPasskey(createPasskeyWebAuthn()); if (mounted) Navigator.pushNamedAndRemoveUntil(context, widget.api.needsVerification ? '/verify-registration' : '/session', (_) => false); } catch (_) { if (mounted) setState(() => error = 'Nie udało się potwierdzić klucza dostępu.'); } finally { if (mounted) setState(() => busy = false); } }
  @override Widget build(BuildContext context) => WillPopScope(
    onWillPop: () async { widget.api.cancelMfa(); return true; },
    child: AuthShell(title: 'Weryfikacja 2FA', subtitle: 'Potwierdź logowanie', child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        FormMessage(error),
        Text(recovery ? 'Wpisz kod odzyskiwania.' : 'Wpisz 6-cyfrowy kod z aplikacji Authenticator.'),
        const SizedBox(height: 16),
        TextField(controller: code, autofocus: true, obscureText: recovery,
          keyboardType: TextInputType.text, maxLength: recovery ? 128 : 6,
          decoration: InputDecoration(labelText: recovery ? 'Kod odzyskiwania' : 'Kod 2FA')),
        if (widget.api.allowsStepUpMethod('recovery_code') || widget.api.allowsStepUpMethod('recovery'))
        TextButton(onPressed: busy ? null : () => setState(() { recovery = !recovery; code.clear(); }),
          child: Text(recovery ? 'Użyj kodu Authenticatora' : 'Użyj kodu odzyskiwania')),
        if (widget.api.allowsStepUpMethod('passkey'))
        OutlinedButton.icon(onPressed: busy ? null : passkey, icon: const Icon(Icons.key_outlined), label: const Text('Potwierdź kluczem dostępu')),
        SubmitButton(busy: busy, label: 'Zweryfikuj', onPressed: verify),
        TextButton(onPressed: busy ? null : () { widget.api.cancelMfa(); Navigator.pushNamedAndRemoveUntil(context, '/', (_) => false); },
          child: const Text('Anuluj')),
      ])),
  );
}
