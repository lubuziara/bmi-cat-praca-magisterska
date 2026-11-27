part of 'login_screen.dart';

class _LoginScreenState extends State<LoginScreen> {
  final form = GlobalKey<FormState>();
  final email = TextEditingController();
  final password = TextEditingController();
  bool busy = false;
  String? error;
  @override
  void dispose() {
    email.dispose();
    password.dispose();
    super.dispose();
  }

  Future<void> submit() async {
    if (busy || !form.currentState!.validate()) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await widget.api.login(email.text, password.text);
      if (mounted) {
        Navigator.pushNamedAndRemoveUntil(
            context,
            widget.api.mfaRequired ? '/2fa-login' : widget.api.needsVerification ? '/verify-registration' : '/session',
            (_) => false);
      }
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }
  Future<void> passkeyLogin() async { if (busy) return; setState(() { busy = true; error = null; }); try { await widget.api.loginPasskey(createPasskeyWebAuthn()); if (mounted) Navigator.pushNamedAndRemoveUntil(context, widget.api.mfaRequired ? '/2fa-login' : widget.api.needsVerification ? '/verify-registration' : '/session', (_) => false); } on UnsupportedError { if (mounted) setState(() => error = 'Ta przeglądarka lub urządzenie nie obsługuje kluczy dostępu.'); } catch (_) { if (mounted) setState(() => error = 'Nie udało się potwierdzić klucza dostępu. Spróbuj ponownie.'); } finally { if (mounted) setState(() => busy = false); } }

  @override
  Widget build(BuildContext context) => AuthShell(
        title: 'Zaloguj się',
        subtitle: 'Miło Cię znowu widzieć!',
        child: AutofillGroup(
            child: Form(
                key: form,
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      FormMessage(error),
                      TextFormField(
                          controller: email,
                          validator: validateEmail,
                          keyboardType: TextInputType.emailAddress,
                          autofillHints: const [AutofillHints.email],
                          autocorrect: false,
                          textInputAction: TextInputAction.next,
                          decoration: const InputDecoration(
                              labelText: 'E-mail',
                              prefixIcon:
                                  Icon(Icons.mail_outline_rounded, size: 20))),
                      const SizedBox(height: 18),
                      PasswordField(
                          controller: password,
                          onSubmitted: submit,
                          validator: (value) => value == null || value.isEmpty
                              ? 'Podaj hasło.'
                              : null),
                      Align(
                          alignment: Alignment.centerRight,
                          child: TextButton(
                              onPressed: busy
                                  ? null
                                  : () => Navigator.pushNamed(
                                      context, '/forgot-password'),
                              child: const Text('Nie pamiętasz hasła?'))),
                      const SizedBox(height: 4),
                      SubmitButton(
                          busy: busy, label: 'Zaloguj się', onPressed: submit),
                      const SizedBox(height: 24),
                      const Row(children: [
                        Expanded(child: Divider()),
                        Padding(
                            padding: EdgeInsets.symmetric(horizontal: 14),
                            child: Text('lub', style: TextStyle(fontSize: 14))),
                        Expanded(child: Divider())
                      ]),
                      const SizedBox(height: 20),
                      GoogleLoginButton(
                          api: widget.api,
                          enabled: !busy,
                          onError: (message) => setState(() => error = message),
                          onSuccess: () => Navigator.pushNamedAndRemoveUntil(
                              context,
                              widget.api.mfaRequired
                                  ? '/2fa-login'
                                  : widget.api.needsVerification
                                  ? '/verify-registration'
                                  : '/session',
                              (_) => false)),
                      const SizedBox(height: 10),
                      OutlinedButton.icon(onPressed: busy ? null : passkeyLogin, icon: const Icon(Icons.key_outlined), label: const Text('Zaloguj kluczem dostępu')),
                      const SizedBox(height: 22),
                      Wrap(
                          alignment: WrapAlignment.center,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                            const Text('Nie masz jeszcze konta?',
                                style: TextStyle(fontSize: 14)),
                            TextButton(
                                onPressed: busy
                                    ? null
                                    : () => Navigator.pushNamed(
                                        context, '/register'),
                                child: const Text('Zarejestruj się')),
                          ]),
                    ]))),
      );
}
