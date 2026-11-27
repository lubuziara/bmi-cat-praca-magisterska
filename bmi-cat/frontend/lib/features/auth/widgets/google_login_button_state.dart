part of 'google_login_button.dart';

class _GoogleLoginButtonState extends State<GoogleLoginButton> {
  static const clientId = String.fromEnvironment('GOOGLE_WEB_CLIENT_ID');
  GoogleSignIn? google;
  StreamSubscription<GoogleSignInAccount?>? subscription;
  bool busy = false;
  @override
  void initState() {
    super.initState();
    if (clientId.isNotEmpty) {
      google = GoogleSignIn(
          clientId: kIsWeb ? clientId : null,
          serverClientId: kIsWeb ? null : clientId,
          scopes: ['email', 'profile']);
      subscription = google!.onCurrentUserChanged.listen((account) {
        if (account != null) complete(account);
      }, onError: (_) {
        if (mounted) {
          widget.onError(
              'Nie udało się zalogować przez Google. Spróbuj ponownie.');
        }
      });
    }
  }

  @override
  void dispose() {
    subscription?.cancel();
    super.dispose();
  }

  Future<void> complete(GoogleSignInAccount account) async {
    if (!mounted || busy || !widget.enabled) return;
    setState(() => busy = true);
    try {
      final authentication = await account.authentication;
      final token = authentication.idToken;
      if (token == null) {
        throw Exception('Brak potwierdzenia Google. Spróbuj ponownie.');
      }
      await widget.api.googleLogin(token);
      if (mounted) widget.onSuccess();
    } catch (e) {
      // Pozwala ponowić wybór tego samego konta po odrzuconym logowaniu w API.
      await google?.signOut();
      if (mounted) widget.onError(e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (clientId.isNotEmpty && kIsWeb) {
      return AbsorbPointer(
          absorbing: busy || !widget.enabled, child: buildGoogleWebButton());
    }
    return OutlinedButton.icon(
      style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(52),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
      onPressed: clientId.isEmpty || busy || !widget.enabled
          ? null
          : () async {
              try {
                await google!.signIn();
              } catch (_) {
                if (mounted) {
                  widget.onError(
                      'Nie udało się zalogować przez Google. Spróbuj ponownie.');
                }
              }
            },
      icon: const Icon(Icons.account_circle_outlined, size: 21),
      label: Text(clientId.isEmpty ? 'Google — wkrótce' : 'Kontynuuj z Google'),
    );
  }
}
