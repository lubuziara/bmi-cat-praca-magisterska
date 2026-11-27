part of 'calendar_connections_screen.dart';

class _CalendarConnectionsScreenState extends State<CalendarConnectionsScreen>
    with WidgetsBindingObserver {
  List<dynamic>? connections;
  bool busy = false;
  String? error;
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    load();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) load();
  }

  Future<void> load() async {
    try {
      final data = await widget.api.request('calendar-connections', get: true);
      if (mounted) setState(() => connections = data['connections'] as List);
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    }
  }

  Future<void> action(String provider, String action) async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final data =
          await widget.api.request('calendar-connections/$provider/$action');
      if (action == 'connect') {
        final opened = await launchUrl(Uri.parse(data['url'] as String),
            mode: LaunchMode.externalApplication, webOnlyWindowName: '_blank');
        if (!opened) {
          throw Exception('Nie udało się otworzyć strony logowania.');
        }
      }
      await load();
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) =>
      HealthPage(title: 'Połączenia kalendarza', actions: [
        IconButton(
            tooltip: 'Odśwież połączenia',
            onPressed: load,
            icon: const Icon(Icons.refresh))
      ], children: [
        const Text('Twój kalendarz, zawsze pod ręką',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        const Text(
            'Po połączeniu konta wydarzenia z BMI Cat będą automatycznie dodawane, aktualizowane i usuwane w kalendarzu. Synchronizacja działa podczas pracy serwera, co około minutę.'),
        const SizedBox(height: 12),
        const Text(
            'Kierunek: BMI Cat → Google / Outlook. Zdjęcia i pliki PDF pozostają w BMI Cat; do kalendarza trafia tytuł i czas wydarzenia. Odłączenie zatrzyma synchronizację, zachowując już wysłane wydarzenia.'),
        const SizedBox(height: 20),
        if (error != null)
          Text(error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error)),
        if (connections == null && error == null)
          const LinearProgressIndicator(),
        if (connections != null)
          ...connections!.map((c) => Card(
              child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                            c['provider'] == 'google'
                                ? 'Google Calendar'
                                : 'Outlook',
                            style: const TextStyle(
                                fontSize: 22, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 8),
                        Text(c['connected'] == true
                            ? 'Konto połączone'
                            : c['configured'] == true
                                ? 'Gotowe do połączenia'
                                : 'Wymaga konfiguracji aplikacji OAuth w głównym .env.'),
                        if (c['error'] != null)
                          Text(c['error'] as String,
                              style: TextStyle(
                                  color: Theme.of(context).colorScheme.error)),
                        if (c['last_sync'] != null)
                          Text('Ostatnia synchronizacja: ${c['last_sync']}'),
                        const SizedBox(height: 12),
                        Wrap(spacing: 12, runSpacing: 8, children: [
                          FilledButton(
                              onPressed: busy || c['configured'] != true
                                  ? null
                                  : () => action(
                                      c['provider'] as String, 'connect'),
                              child: Text(c['connected'] == true
                                  ? 'Połącz ponownie'
                                  : 'Połącz konto')),
                          if (c['connected'] == true)
                            OutlinedButton(
                                onPressed: busy
                                    ? null
                                    : () => action(
                                        c['provider'] as String, 'disconnect'),
                                child: const Text('Odłącz')),
                        ]),
                      ])))),
      ]);
}
