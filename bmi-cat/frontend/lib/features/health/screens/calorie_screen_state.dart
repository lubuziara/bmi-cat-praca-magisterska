part of 'calorie_screen.dart';

class _CalorieScreenState extends State<CalorieScreen> {
  final weight = TextEditingController(text: '4');
  double factor = 1.2;
  CalorieGoal goal = CalorieGoal.maintain;
  double? maintenanceCalories;
  double? result;
  bool saving = false;
  String? error;
  @override
  void dispose() {
    weight.dispose();
    super.dispose();
  }

  void calculate() {
    final kg = double.tryParse(weight.text.replaceAll(',', '.'));
    setState(() {
      error = null;
      maintenanceCalories = null;
      result = null;
    });
    if (kg == null || !kg.isFinite || kg < 1 || kg > 20) {
      setState(() => error = 'Podaj masę dorosłego kota od 1 do 20 kg.');
      return;
    }
    final maintenance = 70 * pow(kg, .75) * factor;
    setState(() {
      maintenanceCalories = maintenance;
      result = _adjustedCalories(maintenance);
    });
  }

  double _adjustedCalories(double maintenance) =>
      (maintenance * goal.multiplier).roundToDouble();

  void changeGoal(CalorieGoal value) => setState(() {
        goal = value;
        if (maintenanceCalories != null) {
          result = _adjustedCalories(maintenanceCalories!);
        }
      });

  Future<void> save() async {
    setState(() {
      saving = true;
      error = null;
    });
    try {
      final settings = await widget.api.request('settings', get: true);
      settings.remove('email');
      settings.remove('phone');
      settings['target_kcal'] = result;
      await widget.api.request('settings', body: settings);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Zapisano dzienny cel kalorii.')));
      }
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  @override
  Widget build(BuildContext context) =>
      HealthPage(title: 'Miautatu', children: [
        const Text('Kalorie pod kontrolą',
            style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        FilledButton.icon(
            onPressed: () => Navigator.push(
                context,
                MaterialPageRoute<void>(
                    builder: (_) => DashboardScreen(
                        api: widget.api, profile: widget.profile))),
            icon: const Icon(Icons.restaurant_outlined),
            label: const Text('Otwórz dziennik posiłków')),
        const SizedBox(height: 28),
        const Text('Orientacyjny cel dla dorosłego kota',
            style: TextStyle(fontSize: 21, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        const Text(
            'RER = 70 × masa ciała (kg)^0,75. Cel dzienny to RER pomnożone przez współczynnik. To punkt wyjścia dla zdrowego dorosłego kota o prawidłowej kondycji; dopasuj go z weterynarzem.'),
        const SizedBox(height: 20),
        TextField(
            controller: weight,
            enabled: !saving,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(labelText: 'Masa kota (kg)'),
            onChanged: (_) => setState(() {
                  maintenanceCalories = null;
                  result = null;
                })),
        const SizedBox(height: 20),
        DropdownButtonFormField<double>(
            value: factor,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Dorosły kot'),
            items: const [
              DropdownMenuItem(value: 1.2, child: Text('Po kastracji (×1,2)')),
              DropdownMenuItem(value: 1.4, child: Text('Bez kastracji (×1,4)'))
            ],
            onChanged: saving
                ? null
                : (v) => setState(() {
                      factor = v!;
                      maintenanceCalories = null;
                      result = null;
                    })),
        const SizedBox(height: 20),
        DropdownButtonFormField<CalorieGoal>(
            value: goal,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Cel masy ciała'),
            items: CalorieGoal.values
                .map((value) =>
                    DropdownMenuItem(value: value, child: Text(value.label)))
                .toList(),
            onChanged: saving ? null : (value) => changeGoal(value!)),
        const SizedBox(height: 20),
        OutlinedButton(
            onPressed: saving ? null : calculate,
            child: const Text('Oblicz kalorie')),
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
                    Text('${result!.toInt()} kcal / dzień',
                        style: const TextStyle(
                            fontSize: 27, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Text('Cel: ${goal.label}'),
                    const SizedBox(height: 16),
                    FilledButton(
                        onPressed: saving ? null : save,
                        child: const Text('Ustaw jako dzienny cel'))
                  ]))),
        if (result != null)
          const Padding(
              padding: EdgeInsets.only(top: 12),
              child: Text(
                  'Zmiana masy ciała kota powinna przebiegać stopniowo i pod kontrolą. Przy redukcji bezpieczne tempo to około 0,5–2% masy ciała tygodniowo, a około 1% tygodniowo jest rozsądnym celem. Zbyt szybkie odchudzanie lub zbyt duże ograniczenie kalorii może być dla kota niebezpieczne i zwiększać ryzyko stłuszczenia wątroby. Przybieranie na wadze również powinno być stopniowe i kontrolowane.',
                  style: TextStyle(color: Color(0xFF91769F)))),
        const SizedBox(height: 16),
        const Text(
            'Dla kociąt, ciężarnych kotek, chorych kotów i redukcji masy potrzebny jest indywidualny plan żywienia.',
            style: TextStyle(color: Color(0xFF91769F))),
      ]);
}
