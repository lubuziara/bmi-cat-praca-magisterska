part of 'session_screen.dart';

class _SessionScreenState extends State<SessionScreen> {
  late final Future<Map<String, dynamic>> user = loadProfile();
  Future<Map<String, dynamic>> loadProfile() async {
    final data = await widget.api.me();
    if (data['registration_verified'] == true) {
      final profile = await widget.api.request('profile', get: true);
      data['cat'] = profile['cat'];
    }
    return data;
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<Map<String, dynamic>>(
      future: user,
      builder: (context, snapshot) => snapshot.hasData &&
              snapshot.data!['registration_verified'] == true &&
              snapshot.data!['cat'] != null
          ? HomeScreen(api: widget.api, profile: snapshot.data!)
          : AuthShell(
              title: snapshot.hasData
                  ? 'Cześć, ${snapshot.data!['first_name']}!'
                  : 'Twoje konto',
              subtitle: snapshot.hasData
                  ? 'Witaj w BMI Cat.'
                  : 'Sprawdzamy Twoją sesję.',
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    if (snapshot.connectionState == ConnectionState.waiting)
                      const Center(child: CircularProgressIndicator()),
                    if (snapshot.hasError)
                      FormMessage(snapshot.error.toString()),
                    if (snapshot.hasData) ...[
                      Text(snapshot.data!['email'] as String,
                          textAlign: TextAlign.center),
                      if (snapshot.data!['profile_complete'] == true &&
                          snapshot.data!['registration_verified'] != true)
                        TextButton(
                            onPressed: () => Navigator.pushReplacementNamed(
                                context, '/verify-registration'),
                            child: const Text('Potwierdź e-mail i telefon')),
                      if (snapshot.data!['cat'] != null) ...[
                        const SizedBox(height: 20),
                        Text(snapshot.data!['cat']['name'] as String,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                                fontSize: 24, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 12),
                        SizedBox(
                            height: 350,
                            child: CatAvatar(
                                settings: AvatarSettings.fromJson(
                                    snapshot.data!['cat']['avatar']
                                        as Map<String, dynamic>))),
                      ],
                    ],
                    const SizedBox(height: 24),
                    FilledButton(
                        onPressed: () async {
                          try {
                            await widget.api.logout();
                          } catch (_) {}
                          if (context.mounted) {
                            Navigator.pushNamedAndRemoveUntil(
                                context, '/', (_) => false);
                          }
                        },
                        child: Text(snapshot.hasError
                            ? 'Wróć do logowania'
                            : 'Wyloguj się')),
                  ]),
            ));
}
