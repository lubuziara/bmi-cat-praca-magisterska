package pl.bmicat.bmi_cat

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import android.content.Intent
import androidx.credentials.*
import androidx.credentials.exceptions.CreateCredentialCancellationException
import androidx.credentials.exceptions.CreateCredentialException
import androidx.credentials.exceptions.GetCredentialCancellationException
import androidx.credentials.exceptions.GetCredentialException
import androidx.credentials.exceptions.NoCredentialException
import androidx.lifecycle.lifecycleScope
import io.flutter.plugin.common.MethodChannel
import kotlinx.coroutines.launch

class MainActivity: FlutterActivity() {
    private var documentExporter: DocumentExporter? = null
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        documentExporter = DocumentExporter(this, flutterEngine.dartExecutor.binaryMessenger)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "bmi-cat/passkeys").setMethodCallHandler { call, result ->
            val options = call.argument<String>("options")
            if (options == null || (call.method != "create" && call.method != "get")) { result.notImplemented(); return@setMethodCallHandler }
            lifecycleScope.launch { try {
                val manager = CredentialManager.create(this@MainActivity)
                val json = if (call.method == "create") (manager.createCredential(this@MainActivity, CreatePublicKeyCredentialRequest(options)) as CreatePublicKeyCredentialResponse).registrationResponseJson else (manager.getCredential(this@MainActivity, GetCredentialRequest(listOf(GetPublicKeyCredentialOption(options)))).credential as PublicKeyCredential).authenticationResponseJson
                result.success(json)
            } catch (e: GetCredentialCancellationException) { result.error("cancelled", "cancelled", null)
            } catch (e: CreateCredentialCancellationException) { result.error("cancelled", "cancelled", null)
            } catch (e: NoCredentialException) { result.error("no_credential", "no_credential", null)
            } catch (e: GetCredentialException) { result.error("credential_error", "credential_error", null)
            } catch (e: CreateCredentialException) { result.error("credential_error", "credential_error", null) } }
        }
        flutterEngine.platformViewsController.registry.registerViewFactory(
            "bmi-cat/glb", CatViewFactory(flutterEngine.dartExecutor.binaryMessenger))
    }
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        if (documentExporter?.onResult(requestCode, resultCode, data) == true) return
        super.onActivityResult(requestCode, resultCode, data)
    }
}
