part of 'settings_screen.dart';

class _SettingsScreenState extends State<SettingsScreen> {
  final form = GlobalKey<FormState>();
  final firstName = TextEditingController(),
      lastName = TextEditingController(),
      catName = TextEditingController(),
      kcal = TextEditingController();
  Map<String, dynamic>? data;
  bool notifications = true, saving = false;
  String? error;
  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    for (final c in [firstName, lastName, catName, kcal]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> load() async {
    try {
      final result = await widget.api.request('settings', get: true);
      if (!mounted) return;
      setState(() {
        error = null;
        data = result;
        firstName.text = result['first_name'] as String;
        lastName.text = result['last_name'] as String;
        catName.text = result['cat_name'] as String;
        kcal.text = '${result['target_kcal']}';
        notifications = result['notifications'] as bool;
      });
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    }
  }

  Future<void> save() async {
    if (!form.currentState!.validate()) return;
    setState(() {
      saving = true;
      error = null;
    });
    try {
      await widget.api.request('settings', body: {
        'first_name': firstName.text.trim(),
        'last_name': lastName.text.trim(),
        'cat_name': catName.text.trim(),
        'target_kcal': double.parse(kcal.text.replaceAll(',', '.')),
        'notifications': notifications
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Zapisano ustawienia.')));
      }
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  String? nameValidator(String? value) => value == null ||
          value.trim().length < 2 ||
          RegExp(r'[0-9]').hasMatch(value)
      ? 'Wpisz imię lub nazwisko bez cyfr.'
      : null;
  @override
  Widget build(BuildContext context) =>
      HealthPage(title: 'Ustawienia', children: [
        if (error != null)
          Text(error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error)),
        if (data == null)
          TextButton(onPressed: load, child: const Text('Wczytaj ustawienia'))
        else
          Form(
              key: form,
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text('Twój profil',
                        style: TextStyle(
                            fontSize: 24, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 18),
                    TextFormField(
                        controller: firstName,
                        maxLength: 80,
                        decoration: const InputDecoration(labelText: 'Imię'),
                        validator: nameValidator),
                    const SizedBox(height: 12),
                    TextFormField(
                        controller: lastName,
                        maxLength: 80,
                        decoration:
                            const InputDecoration(labelText: 'Nazwisko'),
                        validator: nameValidator),
                    const SizedBox(height: 12),
                    TextFormField(
                        controller: catName,
                        maxLength: 80,
                        decoration:
                            const InputDecoration(labelText: 'Imię kota'),
                        validator: nameValidator),
                    ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.mail_outline),
                        title: Text(data!['email'] as String),
                        subtitle: const Text('Zweryfikowany e-mail')),
                    ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.phone_outlined),
                        title: Text(data!['phone'] as String),
                        subtitle: const Text('Zweryfikowany telefon')),
                    const SizedBox(height: 20),
                    const Text('Aplikacja',
                        style: TextStyle(
                            fontSize: 24, fontWeight: FontWeight.bold)),
                    SwitchListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Powiadomienia w aplikacji'),
                        subtitle:
                            const Text('Nadchodzące wizyty i przyjęcia leków'),
                        value: notifications,
                        onChanged: saving
                            ? null
                            : (v) => setState(() => notifications = v)),
                    const SizedBox(height: 16),
                    TextFormField(
                        controller: kcal,
                        keyboardType: const TextInputType.numberWithOptions(
                            decimal: true),
                        decoration: const InputDecoration(
                            labelText: 'Dzienny cel kalorii (kcal)',
                            helperText: 'Cel stosowany w pasku żywienia.'),
                        validator: (v) {
                          final n =
                              double.tryParse((v ?? '').replaceAll(',', '.'));
                          return n == null || !n.isFinite || n <= 0 || n > 2000
                              ? 'Podaj wartość od 1 do 2000 kcal.'
                              : null;
                        }),
                    const SizedBox(height: 16),
                    const ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(Icons.language),
                        title: Text('Polski'),
                        subtitle: Text('Jednostki: kg, cm, g i kcal')),
                    ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.sync),
                        title: const Text('Połączenia kalendarza'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => Navigator.push(
                            context,
                            MaterialPageRoute<void>(
                                builder: (_) => CalendarConnectionsScreen(
                                    api: widget.api)))),
                    ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.security_outlined),
                        title: const Text('Bezpieczeństwo konta'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => Navigator.push(context,
                            MaterialPageRoute<void>(builder: (_) => AccountSecurityScreen(api: widget.api)))),
                    const SizedBox(height: 20),
                    FilledButton(
                        onPressed: saving ? null : save,
                        child:
                            Text(saving ? 'Zapisuję…' : 'Zapisz ustawienia')),
                  ])),
      ]);
}
