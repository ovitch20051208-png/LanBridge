$ErrorActionPreference = 'Stop'
python "$PSScriptRoot/build.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python "$PSScriptRoot/smoke_bundle.py" "$PSScriptRoot/../dist/LanBridge/LanBridge.exe"
exit $LASTEXITCODE
