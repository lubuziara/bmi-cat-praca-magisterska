part of 'home_screen.dart';

class _HomeScreenState extends State<HomeScreen> {
  final scaffold = GlobalKey<ScaffoldState>();
  bool drawerOpen = false;
  Map<String, dynamic>? diary;
  String? error;
  bool loading = true;
  @override
  void initState() {
    super.initState();
    refresh();
  }

  Future<void> refresh() async {
    setState(() {
      loading = true;
      error = null;
    });
    final now = DateTime.now();
    final day =
        '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
    try {
      final value = await widget.api.request('diary?day=$day', get: true);
      if (mounted) setState(() => diary = value);
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> openDiary() async {
    await Navigator.push(
        context,
        MaterialPageRoute<void>(
            builder: (_) =>
                DashboardScreen(api: widget.api, profile: widget.profile)));
    if (mounted) await refresh();
  }

  Future<void> openPage(Widget page, {bool profileChanged = false}) async {
    scaffold.currentState?.closeDrawer();
    await Navigator.push(
        context, MaterialPageRoute<void>(builder: (_) => page));
    if (!mounted) return;
    if (profileChanged) {
      try {
        final data = await widget.api.request('profile', get: true);
        if (mounted)
          setState(() {
            widget.profile['first_name'] = data['owner']['first_name'];
            widget.profile['cat'] = data['cat'];
          });
      } catch (_) {}
    }
    if (mounted) await refresh();
  }

  @override
  Widget build(BuildContext context) {
    final cat = widget.profile['cat'] as Map<String, dynamic>;
    return Scaffold(
      key: scaffold,
      onDrawerChanged: (open) => setState(() => drawerOpen = open),
      drawer: Drawer(
          child: SafeArea(
              child: ListView(children: [
        const Padding(
            padding: EdgeInsets.all(24),
            child: Text('BMI Cat',
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold))),
        ListTile(
            leading: const Icon(Icons.calendar_month_outlined),
            title: const Text('Kalendarz'),
            onTap: () => openPage(CalendarScreen(api: widget.api))),
        ListTile(
            leading: const Icon(Icons.monitor_weight_outlined),
            title: const Text('Kalkulator BMI'),
            onTap: () => openPage(BmiScreen(api: widget.api))),
        ListTile(
            leading: const Icon(Icons.restaurant_outlined),
            title: const Text('Miautatu — kalorie'),
            onTap: () => openPage(
                CalorieScreen(api: widget.api, profile: widget.profile))),
        ListTile(
            leading: const Icon(Icons.folder_shared_outlined),
            title: const Text('Dokumentacja medyczna'),
            onTap: () => openPage(DocumentsScreen(api: widget.api))),
        ListTile(
            leading: const Icon(Icons.settings_outlined),
            title: const Text('Ustawienia'),
            onTap: () => openPage(SettingsScreen(api: widget.api),
                profileChanged: true)),
      ]))),
      appBar: AppBar(
          title: const Text('BMI Cat',
              style: TextStyle(fontWeight: FontWeight.bold)),
          backgroundColor: const Color(0xFFFFEEF5),
          actions: [
            IconButton(
                tooltip: 'Powiadomienia',
                icon: const Icon(Icons.notifications_none),
                onPressed: () =>
                    openPage(NotificationsScreen(api: widget.api))),
            IconButton(
                tooltip: 'Wyloguj się',
                icon: const Icon(Icons.logout),
                onPressed: () async {
                  try {
                    await widget.api.logout();
                  } finally {
                    if (context.mounted)
                      Navigator.pushNamedAndRemoveUntil(
                          context, '/', (_) => false);
                  }
                })
          ]),
      bottomNavigationBar: loading
          ? const SafeArea(
              top: false,
              child: Padding(
                  padding: EdgeInsets.all(20),
                  child: LinearProgressIndicator()))
          : error != null
              ? SafeArea(
                  top: false,
                  child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(mainAxisSize: MainAxisSize.min, children: [
                        Text(error!),
                        TextButton(
                            onPressed: refresh,
                            child: const Text('Odśwież podsumowanie'))
                      ])))
              : NutrientBar(
                  totals: diary!['totals'],
                  target: diary!['target_kcal'],
                  onOpenDiary: openDiary),
      body: Center(
          child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 900),
              child: ListView(padding: const EdgeInsets.all(24), children: [
                Text('Cześć, ${widget.profile['first_name']}!',
                    style: const TextStyle(
                        fontSize: 28, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                const Text('Dobrze Was widzieć.',
                    style: TextStyle(color: Color(0xFF91769F), fontSize: 18)),
                const SizedBox(height: 24),
                Text(cat['name'] as String,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                        fontSize: 26, fontWeight: FontWeight.bold)),
                const SizedBox(height: 16),
                SizedBox(
                    height: 390,
                    child: drawerOpen
                        ? const ColoredBox(color: Color(0xFFFFEEF5))
                        : CatAvatar(
                            settings: AvatarSettings.fromJson(
                                Map<String, dynamic>.from(
                                    cat['avatar'] ?? {})))),
                const SizedBox(height: 24),
                const Text('Dzisiejsze żywienie',
                    textAlign: TextAlign.center,
                    style:
                        TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
                const SizedBox(height: 8),
                const Text(
                    'Podsumowanie znajdziesz na dole.\nNaciśnij +, aby przejść do posiłków Rano i Wieczór.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Color(0xFF91769F), height: 1.5)),
              ]))),
    );
  }
}
