part of 'event_editor.dart';

class _EventEditorState extends State<EventEditor> {
  final form = GlobalKey<FormState>();
  final title = TextEditingController();
  final note = TextEditingController();
  late DateTime day = widget.day;
  TimeOfDay time = const TimeOfDay(hour: 10, minute: 0);
  String kind = 'vet';
  bool saving = false;
  String? error;
  @override
  void dispose() {
    title.dispose();
    note.dispose();
    super.dispose();
  }

  Future<void> save() async {
    if (!form.currentState!.validate()) return;
    setState(() {
      saving = true;
      error = null;
    });
    try {
      await widget.api.request('calendar', body: {
        'title': title.text.trim(),
        'note': note.text.trim(),
        'kind': kind,
        'occurred_at': HealthDate.timestamp(
            DateTime(day.year, day.month, day.day, time.hour, time.minute))
      });
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        setState(() {
          error = e.toString();
          saving = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) =>
      HealthPage(title: 'Dodaj wydarzenie', children: [
        Form(
            key: form,
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  DropdownButtonFormField<String>(
                      value: kind,
                      decoration: const InputDecoration(labelText: 'Rodzaj'),
                      items: const [
                        DropdownMenuItem(
                            value: 'vet', child: Text('Wizyta u weterynarza')),
                        DropdownMenuItem(
                            value: 'medication', child: Text('Przyjęcie leku')),
                      ],
                      onChanged:
                          saving ? null : (v) => setState(() => kind = v!)),
                  const SizedBox(height: 18),
                  TextFormField(
                      controller: title,
                      maxLength: 120,
                      decoration: InputDecoration(
                          labelText:
                              kind == 'vet' ? 'Nazwa wizyty' : 'Nazwa leku'),
                      validator: (v) => (v?.trim().length ?? 0) < 2
                          ? 'Wpisz co najmniej 2 znaki.'
                          : null),
                  const SizedBox(height: 12),
                  Wrap(spacing: 12, runSpacing: 12, children: [
                    OutlinedButton.icon(
                        icon: const Icon(Icons.calendar_month),
                        label: Text(HealthDate.day(day)),
                        onPressed: saving
                            ? null
                            : () async {
                                final value = await showDatePicker(
                                    context: context,
                                    initialDate: day,
                                    firstDate: DateTime(2000),
                                    lastDate: DateTime(2100));
                                if (value != null && mounted) {
                                  setState(() => day = value);
                                }
                              }),
                    OutlinedButton.icon(
                        icon: const Icon(Icons.schedule),
                        label: Text(time.format(context)),
                        onPressed: saving
                            ? null
                            : () async {
                                final value = await showTimePicker(
                                    context: context, initialTime: time);
                                if (value != null && mounted) {
                                  setState(() => time = value);
                                }
                              }),
                  ]),
                  const SizedBox(height: 18),
                  TextFormField(
                      controller: note,
                      maxLength: 2000,
                      maxLines: 4,
                      decoration: const InputDecoration(
                          labelText: 'Notatka (opcjonalnie)',
                          hintText:
                              'Np. adres gabinetu lub zalecona dawka leku')),
                  const SizedBox(height: 18),
                  if (error != null)
                    Text(error!,
                        style: TextStyle(
                            color: Theme.of(context).colorScheme.error)),
                  FilledButton(
                      onPressed: saving ? null : save,
                      child: Text(saving ? 'Zapisuję…' : 'Zapisz wydarzenie')),
                ])),
      ]);
}
