part of 'register_screen.dart';

class _RegisterScreenState extends State<RegisterScreen> {
  final forms = List.generate(3, (_) => GlobalKey<FormState>());
  final name = TextEditingController(),
      surname = TextEditingController(),
      birthday = TextEditingController();
  final phone = TextEditingController(),
      email = TextEditingController(),
      password = TextEditingController(),
      confirmation = TextEditingController();
  final catName = TextEditingController(),
      catBirthday = TextEditingController(),
      years = TextEditingController(text: '0'),
      months = TextEditingController(text: '0');
  String? gender, catGender;
  bool estimated = false, busy = false;
  int step = 0;
  String? error;
  AvatarSettings avatar = const AvatarSettings();
  @override
  void dispose() {
    for (final c in [
      name,
      surname,
      birthday,
      phone,
      email,
      password,
      confirmation,
      catName,
      catBirthday,
      years,
      months
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  String iso(TextEditingController c) =>
      parseBirthDate(c.text)!.toIso8601String().substring(0, 10);
  Future<void> submit() async {
    if (busy || !forms[step].currentState!.validate()) return;
    if (step < 2) {
      setState(() {
        step++;
        error = null;
      });
      return;
    }
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await widget.api.registerProfile({
        'first_name': name.text.trim(),
        'last_name': surname.text.trim(),
        'gender': gender,
        'birth_date': iso(birthday),
        'phone': phone.text.trim(),
        'email': email.text.trim(),
        'password': password.text,
        'cat': {
          'name': catName.text.trim(),
          'gender': catGender,
          if (estimated)
            'estimated_age_months':
                int.parse(years.text) * 12 + int.parse(months.text)
          else
            'birth_date': iso(catBirthday),
          'avatar': avatar.toJson()
        },
      });
      if (mounted) {
        Navigator.pushNamedAndRemoveUntil(
            context, '/verify-registration', (_) => false);
      }
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Widget genderField({bool cat = false}) => DropdownButtonFormField<String>(
      value: cat ? catGender : gender,
      isExpanded: true,
      decoration: InputDecoration(labelText: cat ? 'Płeć kota' : 'Płeć'),
      items: (cat
              ? {'female': 'Kotka', 'male': 'Kocur', 'unknown': 'Nie wiem'}
              : {
                  'female': 'Kobieta',
                  'male': 'Mężczyzna',
                  'other': 'Inna',
                  'undisclosed': 'Wolę nie podawać'
                })
          .entries
          .map((e) => DropdownMenuItem(value: e.key, child: Text(e.value)))
          .toList(),
      validator: (v) => v == null ? 'Wybierz opcję.' : null,
      onChanged: (v) => setState(() {
            if (cat) {
              catGender = v;
            } else {
              gender = v;
            }
          }));
  Widget ownerForm() => AutofillGroup(
          child: FormGrid(children: [
        TextFormField(
            controller: name,
            validator: validateName,
            autofillHints: const [AutofillHints.givenName],
            textCapitalization: TextCapitalization.words,
            decoration: const InputDecoration(labelText: 'Imię')),
        TextFormField(
            controller: surname,
            validator: validateName,
            autofillHints: const [AutofillHints.familyName],
            textCapitalization: TextCapitalization.words,
            decoration: const InputDecoration(labelText: 'Nazwisko')),
        genderField(),
        BirthDateField(controller: birthday),
        TextFormField(
            controller: phone,
            validator: validatePhone,
            keyboardType: TextInputType.phone,
            autofillHints: const [AutofillHints.telephoneNumber],
            decoration: const InputDecoration(
                labelText: 'Numer telefonu', hintText: '+48 123 456 789')),
        TextFormField(
            controller: email,
            validator: validateEmail,
            keyboardType: TextInputType.emailAddress,
            autofillHints: const [AutofillHints.email],
            decoration: const InputDecoration(labelText: 'E-mail')),
        PasswordField(
            controller: password,
            validator: validatePassword,
            newPassword: true),
        PasswordField(
            controller: confirmation,
            label: 'Powtórz hasło',
            newPassword: true,
            validator: (v) => v == password.text && v!.isNotEmpty
                ? null
                : 'Hasła muszą być takie same.'),
      ]));
  Widget catForm() =>
      Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        FormGrid(children: [
          TextFormField(
              controller: catName,
              validator: validateName,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(labelText: 'Imię kota')),
          genderField(cat: true),
        ]),
        const SizedBox(height: 18),
        SwitchListTile.adaptive(
            contentPadding: EdgeInsets.zero,
            title: const Text('Nie znam daty urodzenia'),
            subtitle: const Text(
                'Podam przybliżony wiek, np. dla znalezionego kota.'),
            value: estimated,
            onChanged: (v) => setState(() => estimated = v)),
        const SizedBox(height: 18),
        if (!estimated)
          BirthDateField(controller: catBirthday, maxYears: 40)
        else ...[
          const Padding(
            padding: EdgeInsets.only(bottom: 18),
            child: Text(
                'Podaj, ile lat i miesięcy ma kot.\nNa przykład: 10 lat i 2 miesiące → wpisz 10 i 2.',
                style: TextStyle(fontSize: 14, height: 1.5)),
          ),
          FormGrid(children: [
            TextFormField(
                controller: years,
                autovalidateMode: AutovalidateMode.onUserInteraction,
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                decoration: const InputDecoration(
                    labelText: 'Ile ma lat?',
                    helperText:
                        'Liczba pełnych lat, np. 10. Poniżej roku wpisz 0.',
                    helperMaxLines: 2),
                validator: (v) {
                  final n = int.tryParse(v ?? '');
                  return n == null || n < 0 || n > 40
                      ? 'Wpisz liczbę lat od 0 do 40, np. 10.'
                      : null;
                }),
            TextFormField(
                controller: months,
                autovalidateMode: AutovalidateMode.onUserInteraction,
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                decoration: const InputDecoration(
                    labelText: 'Ile ma miesięcy?',
                    helperText: 'Dodatkowe miesiące ponad pełne lata: 0–11.',
                    helperMaxLines: 2),
                validator: (v) {
                  final n = int.tryParse(v ?? '');
                  return n == null ||
                          n < 0 ||
                          n > 11 ||
                          (int.tryParse(years.text) ?? 0) * 12 + n > 480
                      ? 'Podaj 0–11 miesięcy (łącznie do 40 lat).'
                      : null;
                }),
          ]),
        ],
      ]);
  @override
  Widget build(BuildContext context) => AuthShell(
      title: 'Utwórz konto',
      subtitle: const [
        'Opowiedz nam o sobie.',
        'Poznajmy Twojego kota.',
        'Stwórz swojego wirtualnego pupila.'
      ][step],
      back: true,
      maxWidth: 940,
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Row(
            children: List.generate(
                3,
                (index) => Expanded(
                    child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 3),
                        child: Column(children: [
                          Container(
                              height: 5,
                              decoration: BoxDecoration(
                                  color: index <= step
                                      ? const Color(0xFF754298)
                                      : const Color(0xFFE5D7EC),
                                  borderRadius: BorderRadius.circular(3))),
                          const SizedBox(height: 8),
                          Text(
                              '${index + 1}. ${const [
                                'Właściciel',
                                'Kot',
                                'Avatar'
                              ][index]}',
                              style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: index == step
                                      ? FontWeight.bold
                                      : FontWeight.normal)),
                        ]))))),
        const SizedBox(height: 28),
        FormMessage(error),
        Form(
            key: forms[step],
            child: switch (step) {
              0 => ownerForm(),
              1 => catForm(),
              _ => AvatarEditor(
                  value: avatar, onChanged: (v) => setState(() => avatar = v))
            }),
        const SizedBox(height: 24),
        if (step == 2)
          const Padding(
              padding: EdgeInsets.only(bottom: 18),
              child: Text(
                  'Wygląd pupila możesz później zmienić. W następnym kroku potwierdzisz e-mail i telefon.',
                  style: TextStyle(fontSize: 14, height: 1.5))),
        SubmitButton(
            busy: busy,
            label: step == 2 ? 'Zarejestruj konto' : 'Dalej',
            onPressed: submit),
        if (step > 0)
          TextButton(
              onPressed: busy ? null : () => setState(() => step--),
              child: const Text('Wstecz')),
      ]));
}
