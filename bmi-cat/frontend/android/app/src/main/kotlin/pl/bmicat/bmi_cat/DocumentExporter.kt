package pl.bmicat.bmi_cat

import android.app.Activity
import android.content.Intent
import io.flutter.plugin.common.BinaryMessenger
import io.flutter.plugin.common.MethodChannel

class DocumentExporter(private val activity: Activity, messenger: BinaryMessenger) {
    private var result: MethodChannel.Result? = null
    private var bytes: ByteArray? = null
    private val requestCode = 8241

    init {
        MethodChannel(messenger, "bmi-cat/documents").setMethodCallHandler { call, reply ->
            if (call.method != "savePdf") {
                reply.notImplemented()
            } else if (result != null) {
                reply.error("busy", "Trwa zapis dokumentu.", null)
            } else {
                val data = call.argument<ByteArray>("bytes")
                if (data == null) {
                    reply.error("invalid", "Brak dokumentu.", null)
                } else {
                    bytes = data
                    result = reply
                    try {
                        val intent = Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
                            addCategory(Intent.CATEGORY_OPENABLE)
                            type = "application/pdf"
                            putExtra(Intent.EXTRA_TITLE, call.argument<String>("name") ?: "bmi-cat.pdf")
                        }
                        activity.startActivityForResult(intent, requestCode)
                    } catch (_: Exception) {
                        result?.error("save_failed", "Nie udało się otworzyć zapisu pliku.", null)
                        result = null
                        bytes = null
                    }
                }
            }
        }
    }

    fun onResult(code: Int, status: Int, data: Intent?): Boolean {
        if (code != requestCode) return false
        try {
            if (status == Activity.RESULT_OK && data?.data != null) {
                val stream = activity.contentResolver.openOutputStream(data.data!!)
                    ?: throw IllegalStateException("No output stream")
                stream.use { it.write(bytes ?: throw IllegalStateException("Missing PDF")) }
            }
            result?.success(null)
        } catch (_: Exception) {
            result?.error("save_failed", "Nie udało się zapisać dokumentu.", null)
        } finally {
            result = null
            bytes = null
        }
        return true
    }
}
