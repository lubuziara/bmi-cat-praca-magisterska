part of 'bmi_screen.dart';

class _BmiScreenState extends State<BmiScreen> {
  final form = GlobalKey<FormState>();
  final chest = TextEditingController();
  final leg = TextEditingController();
  bool saving = false;
  Map<String, dynamic>? result;
  String? error;
  @override
  void dispose() {
    chest.dispose();
    leg.dispose();
    super.dispose();
  }

  String? validate(String? text, double max) {
    final value = double.tryParse((text ?? '').replaceAll(',', '.'));
    return value == null || !value.isFinite || value <= 0 || value > max
        ? 'Podaj wartość większą od 0, do $max cm.'
        : null;
  }

  Future<void> calculate() async {
    if (!form.currentState!.validate()) return;
    setState(() {
      saving = true;
      error = null;
      result = null;
    });
    try {
      final data = await widget.api.request('bmi', body: {
        'chest_cm': double.parse(chest.text.replaceAll(',', '.')),
        'leg_cm': double.parse(leg.text.replaceAll(',', '.')),
        'occurred_at': HealthDate.timestamp(DateTime.now()),
      });
      if (mounted) setState(() => result = data);
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  @override
  Widget build(BuildContext context) =>
      HealthPage(title: 'Kalkulator BMI kota', children: [
        const Text('Zmierz, oblicz i obserwuj zmiany',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        const Text(
            'Zmierz obwód klatki piersiowej na wysokości 9. żebra oraz odcinek tylnej nogi od rzepki do guza piętowego, jak na ilustracji. Wymiary podaj w centymetrach.'),
        const SizedBox(height: 16),
        Image.asset('assets/prototype/wymiary.png',
            height: 220, fit: BoxFit.contain),
        const SizedBox(height: 20),
        Form(
            key: form,
            child: Column(children: [
              TextFormField(
                  controller: chest,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                      labelText: 'Obwód klatki piersiowej (cm)'),
                  validator: (v) => validate(v, 150)),
              const SizedBox(height: 18),
              TextFormField(
                  controller: leg,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                      labelText: 'Odcinek tylnej nogi (cm)'),
                  validator: (v) => validate(v, 60)),
            ])),
        const SizedBox(height: 20),
        FilledButton.icon(
            onPressed: saving ? null : calculate,
            icon: const Icon(Icons.calculate_outlined),
            label: Text(saving ? 'Zapisuję…' : 'Oblicz i zapisz w kalendarzu')),
        if (error != null)
          Padding(
              padding: const EdgeInsets.all(12),
              child: Text(error!,
                  style:
                      TextStyle(color: Theme.of(context).colorScheme.error))),
        if (result != null)
          Card(
              child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(children: [
                    Text('${result!['details']['value']}%',
                        style: const TextStyle(
                            fontSize: 38, fontWeight: FontWeight.bold)),
                    const Text('Szacowany udział tkanki tłuszczowej (FBMI)',
                        textAlign: TextAlign.center),
                    const SizedBox(height: 12),
                    const Text(
                        'Zapisano w kalendarzu. Kolejny pomiar dzisiaj zastąpi ten wynik.',
                        textAlign: TextAlign.center),
                  ]))),
        const SizedBox(height: 16),
        const ExpansionTile(title: Text('Wzór z prototypu'), children: [
          Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                  'FBMI (%) = ((obwód / 0,7062 − noga) / 0,9156) − noga\n\nTo szacunek, a nie diagnoza. Kondycję kota ocenia się także skalą BCS i badaniem u weterynarza.'))
        ]),
      ]);
}
