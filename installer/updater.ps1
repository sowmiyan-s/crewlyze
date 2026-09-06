# Crewlyze Auto-Updater Script
param (
    [switch]$CheckOnly,
    [switch]$Silent,
    [string]$Repo = "sowmiyan-s/crewlyze"
)

function Write-Color([string]$text, [ConsoleColor]$color) {
    $prev = [Console]::ForegroundColor
    [Console]::ForegroundColor = $color
    Write-Host $text
    [Console]::ForegroundColor = $prev
}

Write-Color "" White
Write-Color "==========================================================" Cyan
Write-Color "   CREWLYZE AUTO-UPDATE ASSISTANT" Cyan
Write-Color "==========================================================" Cyan
Write-Color "" White

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppDir = Split-Path -Parent $ScriptDir
if (-not (Test-Path "$AppDir\package.json")) {
    $AppDir = $ScriptDir
}

$LocalVersion = "1.2.3"
$pkgPath = Join-Path $AppDir "package.json"
if (Test-Path $pkgPath) {
    try {
        $pkg = Get-Content $pkgPath -Raw | ConvertFrom-Json
        if ($pkg.version) { $LocalVersion = $pkg.version }
    } catch {}
}

Write-Host "Current installed version: " -NoNewline
Write-Color "v$LocalVersion" Yellow

Write-Host "Checking GitHub for latest release... " -NoNewline

$apiUrl = "https://api.github.com/repos/$Repo/releases/latest"
$headers = @{
    "User-Agent" = "Crewlyze-Updater"
    "Accept"     = "application/vnd.github.v3+json"
}

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$release = $null
try {
    $release = Invoke-RestMethod -Uri $apiUrl -Headers $headers -TimeoutSec 8 -ErrorAction Stop
} catch {
    Write-Host ""
    $errMsg = $_.Exception.Message
    if ($errMsg -match "404") {
        Write-Color "No remote releases published yet on GitHub ($Repo)." Gray
        Write-Color "You are running the latest version (v$LocalVersion)." Green
    } else {
        Write-Color "Unable to reach GitHub: $errMsg" Yellow
        Write-Color "Please check your network or visit https://github.com/$Repo/releases" Gray
    }
    Write-Color "" White
    return
}

if (-not $release) {
    Write-Host ""
    Write-Color "No release information returned." Yellow
    return
}

$RemoteTag = $release.tag_name
$RemoteVersion = $RemoteTag.TrimStart("v")

Write-Host ""
Write-Host "Latest available release:  " -NoNewline
Write-Color "v$RemoteVersion" Green

function Compare-SemVer([string]$v1, [string]$v2) {
    $parts1 = $v1.Split('.')
    $parts2 = $v2.Split('.')
    $maxLen = [Math]::Max($parts1.Length, $parts2.Length)
    for ($i = 0; $i -lt $maxLen; $i++) {
        $n1 = 0
        $n2 = 0
        if ($i -lt $parts1.Length) { [int]::TryParse(($parts1[$i] -replace '\D', ''), [ref]$n1) | Out-Null }
        if ($i -lt $parts2.Length) { [int]::TryParse(($parts2[$i] -replace '\D', ''), [ref]$n2) | Out-Null }
        if ($n1 -lt $n2) { return -1 }
        if ($n1 -gt $n2) { return 1 }
    }
    return 0
}

$comp = Compare-SemVer $LocalVersion $RemoteVersion

if ($comp -ge 0) {
    Write-Color "Crewlyze is already up-to-date (v$LocalVersion)!" Green
    Write-Color "" White
    return
}

Write-Color "A newer version of Crewlyze is available: v$RemoteVersion (Installed: v$LocalVersion)" Magenta

if ($CheckOnly) {
    return
}

# Look for .exe installer in assets
$exeAsset = $release.assets | Where-Object { $_.name -like "*.exe" } | Select-Object -First 1

if (-not $exeAsset) {
    Write-Color "No Windows installer executable found in latest release assets." Yellow
    Write-Color "Please visit https://github.com/$Repo/releases/tag/$RemoteTag to update manually." Cyan
    Write-Color "" White
    return
}

$downloadUrl = $exeAsset.browser_download_url
$tempInstaller = Join-Path $env:TEMP $exeAsset.name

Write-Color "Downloading $($exeAsset.name)..." Cyan

try {
    $wc = New-Object System.Net.WebClient
    $wc.DownloadFile($downloadUrl, $tempInstaller)
    Write-Color "Download completed successfully!" Green
} catch {
    Write-Color "Failed to download update: $($_.Exception.Message)" Red
    return
}

Write-Color "Launching update installer..." Green

$installArgs = if ($Silent) { "/SILENT /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS" } else { "" }
Start-Process -FilePath $tempInstaller -ArgumentList $installArgs
Write-Color "Update installer started. You may close this window." Gray
Write-Color "" White
