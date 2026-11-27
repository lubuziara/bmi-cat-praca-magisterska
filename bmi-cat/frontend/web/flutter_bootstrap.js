{{flutter_js}}
{{flutter_build_config}}

// CanvasKit ships with the build, so localhost does not need Google's CDN.
// This external script keeps the document compatible with script-src 'self'.
(async function loadCurrentBuild() {
  if ('serviceWorker' in navigator) {
    const registrations = await navigator.serviceWorker.getRegistrations();
    await Promise.all(registrations.map((registration) => registration.unregister()));
  }
  if ('caches' in window) {
    const names = await caches.keys();
    await Promise.all(names.map((name) => caches.delete(name)));
  }
  _flutter.loader.load({ config: { canvasKitBaseUrl: 'canvaskit/' } });
})();
