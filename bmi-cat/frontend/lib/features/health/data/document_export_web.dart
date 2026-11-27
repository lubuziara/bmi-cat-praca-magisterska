// ignore_for_file: deprecated_member_use, avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:typed_data';

Future<void> exportDocument(Uint8List bytes, String name) async {
  final url =
      html.Url.createObjectUrlFromBlob(html.Blob([bytes], 'application/pdf'));
  final link = html.AnchorElement(href: url)..download = name;
  html.document.body!.append(link);
  link.click();
  link.remove();
  await Future<void>.delayed(const Duration(seconds: 2));
  html.Url.revokeObjectUrl(url);
}
