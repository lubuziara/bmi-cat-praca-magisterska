import 'package:flutter/widgets.dart';
import 'package:google_sign_in_web/web_only.dart' as web;

Widget buildGoogleWebButton() => Center(
        child: web.renderButton(
            configuration: web.GSIButtonConfiguration(
      type: web.GSIButtonType.standard,
      size: web.GSIButtonSize.large,
      shape: web.GSIButtonShape.pill,
      text: web.GSIButtonText.continueWith,
    )));
