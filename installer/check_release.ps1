# Quick online check for newer installer release
param (
    [string]$CurrentVersion = "1.2.3",
    [string]$Repo = "sowmiyan-s/crewlyze"
)

$apiUrl = "https://api.github.com/repos/$Repo/releases/latest"
$headers = @{ "User-Agent" = "Crewlyze-Setup-Check" }

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

try {
    $rel = Invoke-RestMethod -Uri $apiUrl -Headers $headers -TimeoutSec 3 -ErrorAction Stop
    $remoteVer = ($rel.tag_name -replace '^v','').Trim()
    
    # Compare versions
    $v1 = $CurrentVersion.Split('.') | ForEach-Object { [int]($_ -replace '\D') }
    $v2 = $remoteVer.Split('.') | ForEach-Object { [int]($_ -replace '\D') }
    $maxL = [Math]::Max($v1.Count, $v2.Count)
    $hasNewer = $false
    for ($i = 0; $i -lt $maxL; $i++) {
        $n1 = if ($i -lt $v1.Count) { $v1[$i] } else { 0 }
        $n2 = if ($i -lt $v2.Count) { $v2[$i] } else { 0 }
        if ($n2 -gt $n1) { $hasNewer = $true; break }
        if ($n2 -lt $n1) { break }
    }
    
    if ($hasNewer) {
        $outFile = Join-Path $env:TEMP "crewlyze_latest.txt"
        Set-Content -Path $outFile -Value $remoteVer -Force
        exit 2  # newer version available
    }
    exit 0      # up-to-date
} catch {
    exit 0      # offline or no release, proceed normally
}
