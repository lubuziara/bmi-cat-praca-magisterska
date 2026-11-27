part of 'documents_screen.dart';

class _DocumentsScreenState extends State<DocumentsScreen> {
  final title = TextEditingController(text: 'Dokument od weterynarza');
  List<dynamic> documents = [];
  Uint8List? image;
  DateTime? captured;
  bool loading = true, saving = false;
  String? error;
  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    title.dispose();
    super.dispose();
  }

  Future<void> load() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final result = await widget.api.request('documents', get: true);
      if (mounted) setState(() => documents = result['documents'] as List);
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> choose(ImageSource source) async {
    setState(() => error = null);
    try {
      final file = await (widget.picker ?? ImagePicker()).pickImage(
          source: source, maxWidth: 3000, maxHeight: 3000, imageQuality: 95);
      if (file == null) return;
      if (await file.length() > 8 * 1024 * 1024) {
        throw Exception('Zdjęcie może mieć maksymalnie 8 MB.');
      }
      final bytes = await file.readAsBytes();
      if (mounted) {
        setState(() {
          image = bytes;
          captured = DateTime.now();
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => error =
            'Nie udało się otworzyć zdjęcia. Sprawdź uprawnienia aparatu lub wybierz plik JPG/PNG/WebP do 8 MB.');
      }
    }
  }

  Future<void> save() async {
    if (title.text.trim().length < 2) {
      setState(() => error = 'Podaj tytuł dokumentu (co najmniej 2 znaki).');
      return;
    }
    setState(() {
      saving = true;
      error = null;
    });
    try {
      await widget.api.request('documents', body: {
        'title': title.text.trim(),
        'image_base64': base64Encode(image!),
        'occurred_at': HealthDate.timestamp(captured!)
      });
      if (mounted) {
        setState(() => image = null);
        await load();
      }
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  @override
  Widget build(BuildContext context) =>
      HealthPage(title: 'Dokumentacja medyczna', children: [
        const Text('Wszystkie dokumenty w jednym miejscu',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        const Text(
            'Zrób zdjęcie lub wybierz je z urządzenia. Sprawdź czytelność i zaakceptuj — zapiszemy PDF oraz wydarzenie z datą i godziną dodania.'),
        const SizedBox(height: 20),
        if (image == null) ...[
          Wrap(spacing: 12, runSpacing: 12, children: [
            FilledButton.icon(
                onPressed: saving ? null : () => choose(ImageSource.camera),
                icon: const Icon(Icons.photo_camera_outlined),
                label: const Text('Zrób zdjęcie')),
            OutlinedButton.icon(
                onPressed: saving ? null : () => choose(ImageSource.gallery),
                icon: const Icon(Icons.photo_library_outlined),
                label: const Text('Wybierz zdjęcie')),
          ]),
          const SizedBox(height: 8),
          const Text(
              'Na komputerze wybierz plik. Na telefonie przycisk zdjęcia otworzy dostępny aparat.',
              style: TextStyle(fontSize: 12, color: Color(0xFF91769F))),
        ] else ...[
          const Text('Podgląd przed zapisaniem',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: Image.memory(image!,
                  height: 420,
                  fit: BoxFit.contain,
                  errorBuilder: (_, __, ___) => const Text(
                      'Nie można wyświetlić tego zdjęcia. Wybierz JPG, PNG lub WebP.'))),
          const SizedBox(height: 16),
          TextField(
              controller: title,
              maxLength: 120,
              decoration: const InputDecoration(labelText: 'Tytuł dokumentu')),
          const SizedBox(height: 12),
          Wrap(spacing: 12, runSpacing: 8, children: [
            FilledButton.icon(
                onPressed: saving ? null : save,
                icon: const Icon(Icons.check),
                label:
                    Text(saving ? 'Zapisuję PDF…' : 'Akceptuję — zapisz PDF')),
            OutlinedButton(
                onPressed: saving
                    ? null
                    : () => setState(() {
                          image = null;
                          error = null;
                        }),
                child: const Text('Odrzuć zdjęcie')),
          ]),
        ],
        if (error != null)
          Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: Text(error!,
                  style:
                      TextStyle(color: Theme.of(context).colorScheme.error))),
        const SizedBox(height: 28),
        Row(children: [
          const Expanded(
              child: Text('Biblioteka dokumentów',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold))),
          IconButton(
              tooltip: 'Odśwież bibliotekę',
              onPressed: loading ? null : load,
              icon: const Icon(Icons.refresh))
        ]),
        if (loading)
          const LinearProgressIndicator()
        else if (documents.isEmpty)
          const Padding(
              padding: EdgeInsets.all(24),
              child: Text('Nie masz jeszcze zapisanych dokumentów.'))
        else
          ...documents.map((doc) => Card(
              child: ListTile(
                  leading: const Icon(Icons.picture_as_pdf_outlined),
                  title: Text(doc['title'] as String),
                  subtitle:
                      Text(HealthDate.label(doc['occurred_at'] as String)),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () async {
                    await Navigator.push(
                        context,
                        MaterialPageRoute<void>(
                            builder: (_) => DocumentDetailScreen(
                                api: widget.api, id: doc['id'] as int)));
                    if (mounted) await load();
                  }))),
      ]);
}
