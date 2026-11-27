part of 'document_detail_screen.dart';

class _DocumentDetailScreenState extends State<DocumentDetailScreen> {
  Map<String, dynamic>? document;
  String? error;
  bool busy = false;
  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    try {
      final data =
          await widget.api.request('documents/${widget.id}', get: true);
      if (mounted) {
        setState(() {
          document = data;
          error = null;
        });
      }
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    }
  }

  Future<void> download() async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await exportDocument(
          await widget.api.download('documents/${widget.id}/pdf'),
          'bmi-cat-dokument-${widget.id}.pdf');
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> remove() async {
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
                title: const Text('Usunąć dokument?'),
                content: const Text(
                    'Zdjęcie, PDF i powiązany wpis w kalendarzu zostaną usunięte.'),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text('Anuluj')),
                  FilledButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      child: const Text('Usuń'))
                ]));
    if (ok != true || !mounted) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await widget.api.request('documents/${widget.id}/remove');
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted) {
        setState(() {
          error = e.toString();
          busy = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) =>
      HealthPage(title: 'Dokument', children: [
        if (error != null) ...[
          Text(error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error)),
          TextButton(onPressed: load, child: const Text('Spróbuj ponownie'))
        ],
        if (document == null && error == null) const LinearProgressIndicator(),
        if (document != null) ...[
          Text(document!['title'] as String,
              style:
                  const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Text(HealthDate.label(document!['occurred_at'] as String)),
          const SizedBox(height: 18),
          SizedBox(
              height: 500,
              child: InteractiveViewer(
                  minScale: 1,
                  maxScale: 5,
                  child: Image.memory(
                      base64Decode(document!['image_base64'] as String),
                      fit: BoxFit.contain))),
          const SizedBox(height: 16),
          const Text('Powiększ dokument gestem szczypania lub kółkiem myszy.',
              textAlign: TextAlign.center),
          const SizedBox(height: 20),
          Wrap(spacing: 12, runSpacing: 12, children: [
            FilledButton.icon(
                onPressed: busy ? null : download,
                icon: const Icon(Icons.download_outlined),
                label: const Text('Pobierz PDF')),
            OutlinedButton.icon(
                onPressed: busy ? null : remove,
                icon: const Icon(Icons.delete_outline),
                label: const Text('Usuń dokument'))
          ]),
        ],
      ]);
}
