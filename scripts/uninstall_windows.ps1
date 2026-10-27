$ErrorActionPreference = 'Stop'
$programsRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs'))
$installRoot = [IO.Path]::GetFullPath((Join-Path $programsRoot 'LanBridge'))
if ((Split-Path -Parent $installRoot) -ne $programsRoot -or (Split-Path -Leaf $installRoot) -ne 'LanBridge') { throw 'Unexpected uninstall path' }
$running = Get-Process -Name LanBridge -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq (Join-Path $installRoot 'LanBridge.exe') }
if ($running) { throw 'Quit LanBridge from the system tray before uninstalling.' }
if (Test-Path -LiteralPath $installRoot) { Remove-Item -LiteralPath $installRoot -Recurse -Force }
$shortcut = Join-Path ([Environment]::GetFolderPath('Programs')) 'LanBridge.lnk'
if (Test-Path -LiteralPath $shortcut) { Remove-Item -LiteralPath $shortcut }
$sendTo = Join-Path $env:APPDATA 'Microsoft\Windows\SendTo\Send with LanBridge.lnk'
if (Test-Path -LiteralPath $sendTo) { Remove-Item -LiteralPath $sendTo }
Remove-ItemProperty -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name LanBridge -ErrorAction SilentlyContinue
Write-Host 'LanBridge removed. Settings, trust, identity and received files were preserved.'
