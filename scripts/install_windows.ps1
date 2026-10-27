param([Parameter(Mandatory=$true)][string]$Archive, [switch]$InstallSendTo)
$ErrorActionPreference = 'Stop'
$installRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs\LanBridge'))
$expectedRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs\LanBridge'))
if ($installRoot -ne $expectedRoot) { throw 'Unexpected installation path' }
$archivePath = (Resolve-Path -LiteralPath $Archive).Path
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($archivePath)
try {
    foreach ($entry in $zip.Entries) {
        $relative = $entry.FullName.Replace('/', '\')
        if (-not $relative.StartsWith('LanBridge\') -or $relative.Contains('..') -or $relative.Contains(':')) {
            throw "Unexpected archive entry: $relative"
        }
    }
} finally { $zip.Dispose() }
$stage = Join-Path ([IO.Path]::GetTempPath()) ('lanbridge-install-' + [Guid]::NewGuid().ToString('N'))
$resolvedStage = [IO.Path]::GetFullPath($stage)
if (-not $resolvedStage.StartsWith([IO.Path]::GetFullPath([IO.Path]::GetTempPath()), [StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected staging path' }
try {
    Expand-Archive -LiteralPath $archivePath -DestinationPath $stage
    $sourceRoot = Join-Path $stage 'LanBridge'
    if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot 'LanBridge.exe'))) { throw 'Executable missing from archive' }
    $running = Get-Process -Name LanBridge -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq (Join-Path $installRoot 'LanBridge.exe') }
    if ($running) { throw 'Quit LanBridge from the system tray before updating.' }
    New-Item -ItemType Directory -Force -Path $installRoot | Out-Null
    Get-ChildItem -LiteralPath $sourceRoot -Force | Copy-Item -Destination $installRoot -Recurse -Force
    $shell = New-Object -ComObject WScript.Shell
    $shortcutPath = Join-Path ([Environment]::GetFolderPath('Programs')) 'LanBridge.lnk'
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = Join-Path $installRoot 'LanBridge.exe'
    $shortcut.Save()
    if ($InstallSendTo) {
        $result = Start-Process -FilePath (Join-Path $installRoot 'LanBridge.exe') -ArgumentList '--install-integration' -Wait -PassThru -WindowStyle Hidden
        if ($result.ExitCode -ne 0) { throw 'Send To integration installation failed' }
    }
    Write-Host "Installed LanBridge to $installRoot"
} finally {
    if (Test-Path -LiteralPath $resolvedStage) { Remove-Item -LiteralPath $resolvedStage -Recurse -Force }
}
