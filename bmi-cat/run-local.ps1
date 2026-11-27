param(
    [ValidateSet('Api','Web','BuildWeb','WebDev','BuildAndroid','PhoneApi','PhoneWeb','BuildPhoneWeb')]
    [string]$Service = 'Web',
    [string]$PhoneAddress = '192.168.100.4',
    [int]$PhonePort = 5173
)
$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$venvPython = Join-Path $PSScriptRoot 'backend\.venv\Scripts\python.exe'
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $venvPython) {
    $runtimePython = $venvPython
} elseif (Test-Path -LiteralPath $bundledPython) {
    $runtimePython = $bundledPython
    $env:PYTHONPATH = Join-Path $workspaceRoot 'work\python-packages'
} else {
    $runtimePython = (Get-Command python -ErrorAction Stop).Source
}
if ($Service -in @('Api','PhoneApi')) {
    if ($Service -eq 'PhoneApi') {
        $env:BMI_CORS_ORIGINS = '["http://' + $PhoneAddress + ':5173","http://localhost:5173"]'
    }
    Push-Location (Join-Path $PSScriptRoot 'backend')
    $listenAddress = if ($Service -eq 'PhoneApi') { '0.0.0.0' } else { '127.0.0.1' }
    try { & $runtimePython -m uvicorn app.main:create_app --factory --host $listenAddress --port 8000 }
    finally { Pop-Location }
} elseif ($Service -in @('BuildWeb','WebDev','BuildAndroid','BuildPhoneWeb')) {
    $targetPlatform = if ($Service -eq 'BuildAndroid') { 'android' } else { 'web' }
    $publicConfig = Join-Path $PSScriptRoot "frontend\.dart_tool\bmi-cat-$targetPlatform.json"
    if ($Service -eq 'BuildPhoneWeb') {
        $publicConfig = Join-Path $PSScriptRoot 'frontend\.dart_tool\bmi-cat-phone-web.json'
        # The phone web server proxies /api to FastAPI, so Safari only needs
        # one reachable port and never makes a cross-origin API request.
        $env:BMI_API_BASE_URL = "http://${PhoneAddress}:$PhonePort"
        & $runtimePython (Join-Path $PSScriptRoot 'tools\export_flutter_config.py') --target web --output $publicConfig
        if ($LASTEXITCODE -ne 0) { throw 'Could not prepare phone configuration.' }
    } else {
        & $runtimePython (Join-Path $PSScriptRoot 'tools\export_flutter_config.py') --target $targetPlatform --output $publicConfig
        if ($LASTEXITCODE -ne 0) { throw 'Could not read .env configuration.' }
    }
    $flutterCommand = (Get-Command flutter -ErrorAction Stop).Source
    Push-Location (Join-Path $PSScriptRoot 'frontend')
    try {
        if ($Service -eq 'WebDev') {
            & $flutterCommand run -d chrome --web-hostname localhost --web-port 5173 "--dart-define-from-file=$publicConfig"
        } elseif ($Service -eq 'BuildAndroid') {
            & $flutterCommand build apk --debug "--dart-define-from-file=$publicConfig"
        } else {
            & $flutterCommand build web "--dart-define-from-file=$publicConfig"
        }
        if ($LASTEXITCODE -ne 0) { throw 'Flutter did not finish successfully.' }
    } finally { Pop-Location }
} else {
    $webRoot = Join-Path $PSScriptRoot 'frontend\build\web'
    if (-not (Test-Path -LiteralPath (Join-Path $webRoot 'index.html'))) {
        throw 'Najpierw wykonaj .\run-local.ps1 -Service BuildWeb.'
    }
    if ($Service -eq 'PhoneWeb') {
        & $runtimePython (Join-Path $PSScriptRoot 'tools\serve_phone.py') --port $PhonePort --directory $webRoot
    } else {
        & $runtimePython -m http.server 5173 --bind 127.0.0.1 --directory $webRoot
    }
}
