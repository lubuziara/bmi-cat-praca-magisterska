part of 'password_field.dart';

class _PasswordFieldState extends State<PasswordField> {
  bool hidden = true;
  @override
  Widget build(BuildContext context) => TextFormField(
        controller: widget.controller,
        obscureText: hidden,
        validator: widget.validator,
        autocorrect: false,
        enableSuggestions: false,
        autofillHints: [
          widget.newPassword
              ? AutofillHints.newPassword
              : AutofillHints.password
        ],
        onFieldSubmitted: (_) => widget.onSubmitted?.call(),
        decoration: InputDecoration(
            labelText: widget.label,
            prefixIcon: const Icon(Icons.lock_outline_rounded, size: 20),
            suffixIcon: IconButton(
                tooltip: hidden ? 'Pokaż hasło' : 'Ukryj hasło',
                onPressed: () => setState(() => hidden = !hidden),
                icon: Icon(
                    hidden
                        ? Icons.visibility_outlined
                        : Icons.visibility_off_outlined,
                    size: 21))),
      );
}
