import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Bundled GLB contains the supplied mesh, textures and attribution',
      () async {
    TestWidgetsFlutterBinding.ensureInitialized();
    final data = await rootBundle.load('assets/avatar3d/cat.glb');
    expect(data.getUint32(0, Endian.little), 0x46546c67);
    expect(data.getUint32(4, Endian.little), 2);
    expect(data.getUint32(8, Endian.little), data.lengthInBytes);
    final length = data.getUint32(12, Endian.little);
    final document = jsonDecode(utf8.decode(
        data.buffer.asUint8List(data.offsetInBytes + 20, length))) as Map;
    expect(document['meshes'], isNotEmpty);
    expect(document['images'].length, 3);
    expect(document['asset']['extras']['author'], contains('3D Creator'));
    final viewer = await rootBundle.loadString('assets/avatar3d/viewer.js');
    expect(viewer, contains("loadAsync('cat.glb')"));
  });
}
