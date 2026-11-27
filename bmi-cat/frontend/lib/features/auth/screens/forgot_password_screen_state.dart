part of 'forgot_password_screen.dart';

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final form = GlobalKey<FormState>();
  final email = TextEditingController();
  bool busy = false;
  bool success = false;
  String? message;
  @override
  void dispose() {
    email.dispose();
    super.dispose();
  }

  Future<void> submit() async {
    if (busy || !form.currentState!.validate()) return;
    setState(() {
      busy = true;
      message = null;
      success = false;
    });
    try {
      await widget.api.forgotPassword(email.text);
      if (mounted) {
        setState(() {
          success = true;
          message =
              'Jeśli konto istnieje, otrzymasz wiadomość z linkiem do zmiany hasła. Sprawdź też folder spam.';
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
        title: 'Odzyskaj hasło',
        subtitle: 'Podaj e-mail przypisany do Twojego konta.',
        back: true,
        child: Form(
            key: form,
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  FormMessage(message, success: success),
                  TextFormField(
                      controller: email,
                      validator: validateEmail,
                      keyboardType: TextInputType.emailAddress,
                      autofillHints: const [AutofillHints.email],
                      autocorrect: false,
                      onFieldSubmitted: (_) => submit(),
                      decoration: const InputDecoration(labelText: 'E-mail')),
                  const SizedBox(height: 24),
                  SubmitButton(
                      busy: busy, label: 'Wyślij link', onPressed: submit),
                ])),
      );
}
