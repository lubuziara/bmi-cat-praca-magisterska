part of 'notifications_screen.dart';

class _NotificationsScreenState extends State<NotificationsScreen> {
  bool loading = true, enabled = true;
  List<dynamic> events = [];
  String? error;
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
      final settings = await widget.api.request('settings', get: true);
      final now = DateTime.now();
      final data = await widget.api.request(
          'calendar?start=${HealthDate.day(now)}&end=${HealthDate.day(now.add(const Duration(days: 7)))}',
          get: true);
      if (mounted) {
        setState(() {
          enabled = settings['notifications'] == true;
          events = (data['events'] as List)
              .where((e) =>
                  ['vet', 'medication'].contains(e['kind']) &&
                  !DateTime.parse(e['occurred_at'] as String).isBefore(now))
              .toList();
        });
      }
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) =>
      HealthPage(title: 'Powiadomienia', actions: [
        IconButton(
            tooltip: 'Odśwież powiadomienia',
            onPressed: load,
            icon: const Icon(Icons.refresh))
      ], children: [
        const Text('Najbliższe 7 dni',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        if (loading)
          const LinearProgressIndicator()
        else if (error != null)
          Text(error!)
        else if (!enabled)
          const Text(
              'Powiadomienia są wyłączone. Możesz je włączyć w ustawieniach.')
        else if (events.isEmpty)
          const Card(
              child: Padding(
                  padding: EdgeInsets.all(28),
                  child: Column(children: [
                    Icon(Icons.notifications_none, size: 48),
                    SizedBox(height: 12),
                    Text('Nie masz nadchodzących wizyt ani leków.',
                        textAlign: TextAlign.center)
                  ])))
        else
          ...events.map((e) => EventTile(
              event: Map<String, dynamic>.from(e),
              onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute<void>(
                      builder: (_) => CalendarScreen(api: widget.api))))),
      ]);
}
