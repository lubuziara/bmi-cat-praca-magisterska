part of 'reset_password_screen.dart';

class _ResetPasswordScreenState extends State<ResetPasswordScreen> {
  final form = GlobalKey<FormState>();
  final password = TextEditingController();
  final confirmation = TextEditingController();
  bool busy = false;
  bool success = false;
  String? message;
  @override
  void dispose() {
    password.dispose();
    confirmation.dispose();
    super.dispose();
  }

  Future<void> submit() async {
    if (busy || !form.currentState!.validate()) return;
    setState(() {
      busy = true;
      message = null;
    });
    try {
      await widget.api.resetPassword(widget.token, password.text);
      if (mounted) {
        setState(() {
          success = true;
          message = 'Hasło zostało zmienione. Możesz się zalogować.';
        });
      }
    } catch (e) {
      if (mounted) setState(() => message = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => AuthShell(
        title: 'Ustaw nowe hasło',
        subtitle: 'Wybierz hasło o długości od 12 do 128 znaków.',
        back: true,
        child: Form(
            key: form,
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  FormMessage(message, success: success),
                  if (widget.token.isEmpty) ...[
                    const FormMessage(
                        'Brakuje linku do zmiany hasła. Poproś o nowy.'),
                    TextButton(
                        onPressed: () => Navigator.pushReplacementNamed(
                            context, '/forgot-password'),
                        child: const Text('Poproś o nowy link')),
                  ] else if (success)
                    FilledButton(
                        onPressed: () => Navigator.pushNamedAndRemoveUntil(
                            context, '/', (_) => false),
                        child: const Text('Zaloguj się'))
                  else ...[
                    PasswordField(
                        controller: password,
                        label: 'Nowe hasło',
                        validator: validatePassword,
                        newPassword: true),
                    const SizedBox(height: 18),
                    PasswordField(
                        controller: confirmation,
                        label: 'Powtórz hasło',
                        newPassword: true,
                        validator: (value) => value == password.text
                            ? null
                            : 'Hasła muszą być takie same.',
                        onSubmitted: submit),
                    const SizedBox(height: 24),
                    SubmitButton(
                        busy: busy,
                        label: 'Zapisz nowe hasło',
                        onPressed: submit),
                  ],
                ])),
      );
}
