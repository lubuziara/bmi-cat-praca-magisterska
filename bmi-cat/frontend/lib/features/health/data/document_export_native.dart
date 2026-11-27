import 'package:flutter/services.dart';

Future<void> exportDocument(Uint8List bytes, String name) async {
  await const MethodChannel('bmi-cat/documents')
      .invokeMethod<void>('savePdf', {'bytes': bytes, 'name': name});
}
