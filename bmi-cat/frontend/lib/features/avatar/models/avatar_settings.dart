class AvatarSettings {
  final String fur, coat, eyes, size, body;
  const AvatarSettings(
      {this.fur = 'short',
      this.coat = 'white',
      this.eyes = 'green',
      this.size = 'adult',
      this.body = 'medium'});
  factory AvatarSettings.fromJson(Map<String, dynamic> data) => AvatarSettings(
      fur: data['fur'] ?? 'short',
      coat: data['coat'] ?? 'white',
      eyes: data['eyes'] ?? 'green',
      size: data['size'] ?? 'adult',
      body: data['body'] ?? 'medium');
  AvatarSettings copyWith(
          {String? fur,
          String? coat,
          String? eyes,
          String? size,
          String? body}) =>
      AvatarSettings(
          fur: fur ?? this.fur,
          coat: coat ?? this.coat,
          eyes: eyes ?? this.eyes,
          size: size ?? this.size,
          body: body ?? this.body);
  Map<String, dynamic> toJson() => {
        'schema_version': 1,
        'fur': fur,
        'coat': coat,
        'eyes': eyes,
        'size': size,
        'body': body
      };
}
