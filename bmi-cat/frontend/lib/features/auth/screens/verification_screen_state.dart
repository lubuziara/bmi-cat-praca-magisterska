part of 'verification_screen.dart';

class _VerificationScreenState extends State<VerificationScreen> {
  final emailCode = TextEditingController(),
      phoneCode = TextEditingController();
  bool emailVerified = false, phoneVerified = false, busy = false;
  String? message;
  bool success = false;
  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    emailCode.dispose();
    phoneCode.dispose();
    super.dispose();
  }

  void update(Map<String, dynamic> data) {
    emailVerified = data['email_verified'] == true;
    phoneVerified = data['phone_verified'] == true;
  }

  Future<void> load() async {
    try {
      final data = await widget.api.request('verification', get: true);
      if (mounted) setState(() => update(data));
    } catch (e) {
      if (mounted) setState(() => message = e.toString());
    }
  }

  Future<void> act(String channel, {bool confirm = false}) async {
    if (busy) return;
    final code = (channel == 'email' ? emailCode : phoneCode).text.trim();
    if (confirm && !RegExp(r'^[0-9]{6}$').hasMatch(code)) {
      setState(() {
        success = false;
        message = 'Wpisz sześciocyfrowy kod.';
      });
      return;
    }
    setState(() {
      busy = true;
      message = null;
    });
    try {
      final data = await widget.api.request(
          confirm ? 'verification/confirm' : 'verification/send',
          body: {'channel': channel, if (confirm) 'code': code});
      if (mounted) {
        setState(() {
          update(data);
          success = true;
          message = confirm
              ? 'Potwierdzono ${channel == 'email' ? 'e-mail' : 'telefon'}.'
              : 'Kod został wysłany. Jest ważny przez 10 minut.';
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          success = false;
          message = e.toString();
        });
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Widget channel(String channel, String label, bool verified,
          TextEditingController controller) =>
      Container(
          margin: const EdgeInsets.only(bottom: 20),
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
              border: Border.all(color: const Color(0xFFE5D7EC)),
              borderRadius: BorderRadius.circular(18)),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Text('$label${verified ? ' — potwierdzony' : ''}',
                style:
                    const TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
            if (verified)
              const Padding(
                  padding: EdgeInsets.only(top: 12),
                  child: Icon(Icons.check_circle_outline,
                      color: Color(0xFF51764C)))
            else ...[
              TextButton(
                  onPressed: busy ? null : () => act(channel),
                  child: Text(
                      'Wyślij kod ${channel == 'email' ? 'e-mailem' : 'SMS'}')),
              TextField(
                  controller: controller,
                  keyboardType: TextInputType.number,
                  maxLength: 6,
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  autofillHints: const [AutofillHints.oneTimeCode],
                  decoration: InputDecoration(
                      labelText:
                          'Kod z ${channel == 'email' ? 'e-maila' : 'SMS-a'}',
                      counterText: '')),
              const SizedBox(height: 12),
              OutlinedButton(
                  onPressed: busy ? null : () => act(channel, confirm: true),
                  child: Text(
                      'Potwierdź ${channel == 'email' ? 'e-mail' : 'telefon'}')),
            ],
          ]));
  @override
  Widget build(BuildContext context) => AuthShell(
      title: 'Potwierdź rejestrację',
      subtitle:
          'Konto zostało utworzone. Potwierdź osobno adres e-mail i numer telefonu.',
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        FormMessage(message, success: success),
        channel('email', 'E-mail', emailVerified, emailCode),
        channel('phone', 'Telefon', phoneVerified, phoneCode),
        if (busy) const LinearProgressIndicator(),
        FilledButton(
            onPressed: emailVerified && phoneVerified && !busy
                ? () => Navigator.pushNamedAndRemoveUntil(
                    context, '/session', (_) => false)
                : null,
            child: const Text('Przejdź do konta')),
        TextButton(
            onPressed: busy
                ? null
                : () async {
                    try {
                      await widget.api.logout();
                    } catch (_) {}
                    if (context.mounted) {
                      Navigator.pushNamedAndRemoveUntil(
                          context, '/', (_) => false);
                    }
                  },
            child: const Text('Dokończę później — wyloguj')),
      ]));
}
