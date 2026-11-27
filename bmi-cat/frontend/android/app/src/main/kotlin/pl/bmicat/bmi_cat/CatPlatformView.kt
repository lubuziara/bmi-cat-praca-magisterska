package pl.bmicat.bmi_cat

import android.content.Context
import android.view.View
import android.webkit.WebView
import android.webkit.WebViewClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import io.flutter.plugin.common.BinaryMessenger
import io.flutter.plugin.common.MethodChannel
import io.flutter.plugin.common.StandardMessageCodec
import io.flutter.plugin.platform.PlatformView
import io.flutter.plugin.platform.PlatformViewFactory
import org.json.JSONObject
import java.io.ByteArrayInputStream

internal class CatPlatformView(context: Context, id: Int, messenger: BinaryMessenger, initial: Any?): PlatformView {
    private val web = WebView(context)
    private val channel = MethodChannel(messenger, "bmi-cat/glb/$id")
    private var values: Map<*, *> = initial as? Map<*, *> ?: emptyMap<Any,Any>()
    init {
        web.settings.javaScriptEnabled = true
        web.settings.allowFileAccess = false
        web.settings.allowContentAccess = false
        web.webViewClient = object: WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest) = true
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse {
                val uri = request.url
                val path = uri.path ?: ""
                if (uri.scheme != "https" || uri.host != "bmi-cat.local" || path.contains("..")) {
                    return WebResourceResponse("text/plain", "UTF-8", ByteArrayInputStream(ByteArray(0)))
                }
                val mime = when {
                    path.endsWith(".js") -> "text/javascript"
                    path.endsWith(".html") -> "text/html"
                    path.endsWith(".glb") -> "model/gltf-binary"
                    else -> "text/plain"
                }
                return try {
                    WebResourceResponse(mime, "UTF-8", context.assets.open("flutter_assets/assets/avatar3d" + path))
                } catch (error: Exception) {
                    WebResourceResponse("text/plain", "UTF-8", ByteArrayInputStream(ByteArray(0)))
                }
            }
            override fun onPageFinished(view: WebView, url: String) { applySettings() }
        }
        channel.setMethodCallHandler { call, result ->
            if (call.method == "settings") {
                values = call.arguments as? Map<*, *> ?: values
                applySettings()
                result.success(null)
            } else if (call.method == "view") {
                val measurement = call.arguments as? Boolean ?: false
                web.evaluateJavascript("window.setMeasurementView && window.setMeasurementView($measurement)", null)
                result.success(null)
            } else result.notImplemented()
        }
        web.loadUrl("https://bmi-cat.local/index.html")
    }
    private fun applySettings() {
        val json = JSONObject(values).toString()
        web.evaluateJavascript("window.setCatSettings && window.setCatSettings($json)", null)
    }
    override fun getView(): View = web
    override fun dispose() { channel.setMethodCallHandler(null); web.stopLoading(); web.destroy() }
}

