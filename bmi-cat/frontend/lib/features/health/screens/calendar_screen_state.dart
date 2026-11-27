part of 'calendar_screen.dart';

class _CalendarScreenState extends State<CalendarScreen> {
  DateTime selected = DateUtils.dateOnly(DateTime.now());
  late DateTime month = DateTime(selected.year, selected.month);
  List<dynamic> events = [];
  bool loading = true;
  String? error;
  int requestId = 0;
  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    final id = ++requestId;
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final data = await widget.api.request(
          'calendar?start=${HealthDate.day(month)}&end=${HealthDate.day(DateTime(month.year, month.month + 1, 0))}',
          get: true);
      if (mounted && id == requestId) {
        setState(() => events = data['events'] as List);
      }
    } catch (e) {
      if (mounted && id == requestId) setState(() => error = e.toString());
    } finally {
      if (mounted && id == requestId) setState(() => loading = false);
    }
  }

  Future<void> details(Map<String, dynamic> event) async {
    if (event['kind'] == 'document') {
      await Navigator.push(
          context,
          MaterialPageRoute<void>(
              builder: (_) => DocumentDetailScreen(
                  api: widget.api,
                  id: event['details']['document_id'] as int)));
      if (mounted) await load();
      return;
    }
    final data = event['details'] as Map;
    final text = switch (event['kind']) {
      'nutrition' =>
        'Kalorie: ${data['kcal']} kcal\nBiałko: ${data['protein']} g\nTłuszcze: ${data['fat']} g\nWęglowodany: ${data['carbs']} g',
      'bmi' =>
        'FBMI: ${data['value']}%\nKlatka: ${data['chest_cm']} cm\nNoga: ${data['leg_cm']} cm\nOstatni pomiar tego dnia.',
      _ => (data['note'] as String?)?.isNotEmpty == true
          ? data['note'] as String
          : 'Brak dodatkowych notatek.',
    };
    await showDialog<void>(
        context: context,
        builder: (ctx) => AlertDialog(
                title: Text(event['title'] as String),
                content: Text(text),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx),
                      child: const Text('Zamknij'))
                ]));
  }

  Future<void> remove(Map<String, dynamic> event) async {
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
                title: const Text('Usunąć wydarzenie?'),
                content: Text(event['title'] as String),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text('Anuluj')),
                  FilledButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      child: const Text('Usuń'))
                ]));
    if (ok != true) return;
    try {
      await widget.api.request('calendar/${event['id']}/remove');
      if (mounted) await load();
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final start = DateTime(month.year, month.month, 1).weekday - 1;
    final days = DateTime(month.year, month.month + 1, 0).day;
    final todayEvents =
        events.where((e) => e['day'] == HealthDate.day(selected)).toList();
    return HealthPage(title: 'Kalendarz', actions: [
      IconButton(
          tooltip: 'Połącz kalendarz',
          icon: const Icon(Icons.sync),
          onPressed: () => Navigator.push(
              context,
              MaterialPageRoute<void>(
                  builder: (_) => CalendarConnectionsScreen(api: widget.api))))
    ], children: [
      Row(children: [
        IconButton(
            tooltip: 'Poprzedni miesiąc',
            icon: const Icon(Icons.chevron_left),
            onPressed: () {
              setState(() {
                month = DateTime(month.year, month.month - 1);
                selected = month;
              });
              load();
            }),
        Expanded(
            child: Text(
                MaterialLocalizations.of(context).formatMonthYear(month),
                textAlign: TextAlign.center,
                style: const TextStyle(
                    fontSize: 22, fontWeight: FontWeight.bold))),
        IconButton(
            tooltip: 'Następny miesiąc',
            icon: const Icon(Icons.chevron_right),
            onPressed: () {
              setState(() {
                month = DateTime(month.year, month.month + 1);
                selected = month;
              });
              load();
            }),
      ]),
      const SizedBox(height: 12),
      Row(
          children: ['Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'So', 'Nd']
              .map((s) => Expanded(child: Center(child: Text(s))))
              .toList()),
      const SizedBox(height: 8),
      GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: ((start + days + 6) ~/ 7) * 7,
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 7,
              mainAxisSpacing: 4,
              crossAxisSpacing: 4,
              mainAxisExtent: 48),
          itemBuilder: (context, index) {
            final day = index - start + 1;
            if (day < 1 || day > days) return const SizedBox.shrink();
            final date = DateTime(month.year, month.month, day);
            final active = DateUtils.isSameDay(date, selected);
            final hasEvents =
                events.any((e) => e['day'] == HealthDate.day(date));
            return Semantics(
                label:
                    '$day ${MaterialLocalizations.of(context).formatMonthYear(month)}${hasEvents ? ', są wydarzenia' : ''}',
                button: true,
                selected: active,
                child: InkWell(
                    borderRadius: BorderRadius.circular(14),
                    onTap: () => setState(() => selected = date),
                    child: Container(
                        decoration: BoxDecoration(
                            color: active
                                ? const Color(0xFF77429C)
                                : const Color(0xFFF4EAF8),
                            borderRadius: BorderRadius.circular(14)),
                        child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text('$day',
                                  style: TextStyle(
                                      color: active ? Colors.white : null,
                                      fontWeight: FontWeight.w600)),
                              if (hasEvents)
                                Container(
                                    margin: const EdgeInsets.only(top: 3),
                                    width: 5,
                                    height: 5,
                                    decoration: BoxDecoration(
                                        shape: BoxShape.circle,
                                        color: active
                                            ? Colors.white
                                            : const Color(0xFF77429C)))
                            ]))));
          }),
      const SizedBox(height: 20),
      Wrap(
          alignment: WrapAlignment.spaceBetween,
          crossAxisAlignment: WrapCrossAlignment.center,
          spacing: 12,
          runSpacing: 8,
          children: [
            Text(MaterialLocalizations.of(context).formatMediumDate(selected),
                style:
                    const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            FilledButton.icon(
                onPressed: () async {
                  await Navigator.push(
                      context,
                      MaterialPageRoute<bool>(
                          builder: (_) =>
                              EventEditor(api: widget.api, day: selected)));
                  if (mounted) await load();
                },
                icon: const Icon(Icons.add),
                label: const Text('Dodaj wydarzenie')),
          ]),
      const SizedBox(height: 16),
      if (loading)
        const LinearProgressIndicator()
      else if (error != null)
        Column(children: [
          Text(error!),
          TextButton(onPressed: load, child: const Text('Spróbuj ponownie'))
        ])
      else if (todayEvents.isEmpty)
        const Padding(
            padding: EdgeInsets.all(24),
            child: Text('Spokojny dzień. Brak zapisanych wydarzeń.',
                textAlign: TextAlign.center))
      else
        ...todayEvents.map((e) => EventTile(
            event: Map<String, dynamic>.from(e),
            onTap: () => details(Map<String, dynamic>.from(e)),
            onDelete: ['vet', 'medication', 'bmi'].contains(e['kind'])
                ? () => remove(Map<String, dynamic>.from(e))
                : null)),
      const SizedBox(height: 20),
      const Text(
          'Posiłki, ostatni pomiar BMI i zaakceptowane dokumenty pojawiają się tutaj automatycznie.',
          style: TextStyle(color: Color(0xFF91769F))),
    ]);
  }
}
