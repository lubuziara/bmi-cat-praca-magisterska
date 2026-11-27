part of 'dashboard_screen.dart';

class _DashboardScreenState extends State<DashboardScreen> {
  DateTime day = DateUtils.dateOnly(DateTime.now());
  Map<String, dynamic>? diary;
  String? error;
  bool loading = true, busy = false;
  String get dateKey =>
      '${day.year}-${day.month.toString().padLeft(2, '0')}-${day.day.toString().padLeft(2, '0')}';
  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final result = await widget.api.request('diary?day=$dateKey', get: true);
      if (mounted) setState(() => diary = result);
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> add(String period) async {
    await showModalBottomSheet<void>(
        context: context,
        isScrollControlled: true,
        useSafeArea: true,
        builder: (_) => AddMealSheet(
            foods: diary!['foods'],
            period: period == 'morning' ? 'Rano' : 'Wieczór',
            onSave: (food, grams) async {
              final result = await widget.api.request('diary', body: {
                'day': dateKey,
                'period': period,
                'food_id': food,
                'grams': grams
              });
              if (mounted) setState(() => diary = result);
            }));
  }

  Future<void> remove(int id) async {
    setState(() => busy = true);
    try {
      final result = await widget.api.request('diary/$id/remove');
      if (mounted) setState(() => diary = result);
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cat = widget.profile['cat']?['name'] ?? 'Twój kot';
    final today = DateUtils.isSameDay(day, DateTime.now());
    return Scaffold(
      appBar: AppBar(
          backgroundColor: const Color(0xFFFFEEF5),
          title: const Text('BMI Cat',
              style: TextStyle(fontWeight: FontWeight.bold)),
          actions: [
            IconButton(
                tooltip: 'Wyloguj się',
                icon: const Icon(Icons.logout),
                onPressed: () async {
                  await widget.api.logout();
                  if (context.mounted)
                    Navigator.pushNamedAndRemoveUntil(
                        context, '/', (_) => false);
                })
          ]),
      bottomNavigationBar: diary == null || loading || error != null
          ? null
          : NutrientBar(
              totals: diary!['totals'], target: diary!['target_kcal']),
      body: Center(
          child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 980),
              child: ListView(
                  padding: const EdgeInsets.fromLTRB(20, 20, 20, 28),
                  children: [
                    Text('Cześć, ${widget.profile['first_name']}!',
                        style: const TextStyle(
                            fontSize: 28, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 6),
                    Text('Dziennik żywienia · $cat',
                        style: const TextStyle(
                            fontSize: 18, color: Color(0xFF91769F))),
                    const SizedBox(height: 24),
                    Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                            color: const Color(0xFFEEDFF6),
                            borderRadius: BorderRadius.circular(24)),
                        child: Row(children: [
                          const CircleAvatar(
                              radius: 26,
                              backgroundColor: Color(0xFFDDC4EC),
                              child: Icon(Icons.pets,
                                  size: 28, color: Color(0xFF754298))),
                          const SizedBox(width: 16),
                          Expanded(
                              child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                const Text('Małe porcje, dobry dzień',
                                    style: TextStyle(
                                        fontSize: 19,
                                        fontWeight: FontWeight.bold)),
                                Text('Zapisuj to, co zjadł $cat.',
                                    style: const TextStyle(
                                        color: Color(0xFF876D94)))
                              ]))
                        ])),
                    const SizedBox(height: 20),
                    Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                      IconButton(
                          tooltip: 'Poprzedni dzień',
                          onPressed: loading || busy
                              ? null
                              : () {
                                  day = DateTime(
                                      day.year, day.month, day.day - 1);
                                  load();
                                },
                          icon: const Icon(Icons.chevron_left)),
                      Expanded(
                          child: Text(
                              today
                                  ? 'Dzisiaj'
                                  : '${day.day}.${day.month}.${day.year}',
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                  fontSize: 18, fontWeight: FontWeight.w600))),
                      IconButton(
                          tooltip: 'Następny dzień',
                          onPressed: loading || busy
                              ? null
                              : () {
                                  day = DateTime(
                                      day.year, day.month, day.day + 1);
                                  load();
                                },
                          icon: const Icon(Icons.chevron_right))
                    ]),
                    if (loading)
                      const Padding(
                          padding: EdgeInsets.all(40),
                          child: Center(child: CircularProgressIndicator()))
                    else if (error != null) ...[
                      Text(error!),
                      TextButton(
                          onPressed: load,
                          child: const Text('Spróbuj ponownie'))
                    ] else if (diary != null) ...[
                      MealCard(
                          title: 'Rano',
                          period: 'morning',
                          icon: Icons.wb_sunny_outlined,
                          entries: diary!['entries'],
                          onAdd: () => add('morning'),
                          onRemove: remove,
                          busy: busy),
                      const SizedBox(height: 12),
                      MealCard(
                          title: 'Wieczór',
                          period: 'evening',
                          icon: Icons.nightlight_outlined,
                          entries: diary!['entries'],
                          onAdd: () => add('evening'),
                          onRemove: remove,
                          busy: busy),
                      const SizedBox(height: 20),
                      const Text('Cel startowy: 200 kcal / dzień',
                          style: TextStyle(fontWeight: FontWeight.w600)),
                      const SizedBox(height: 6),
                      const Text(
                          'Orientacyjny punkt odniesienia dla zdrowego dorosłego kota ok. 4 kg. Nie jest jeszcze dopasowany do Twojego pupila. Makroskładniki pokazują zjedzoną ilość.',
                          style: TextStyle(
                              fontSize: 12,
                              color: Color(0xFF917D9C),
                              height: 1.5)),
                    ],
                  ]))),
    );
  }
}
