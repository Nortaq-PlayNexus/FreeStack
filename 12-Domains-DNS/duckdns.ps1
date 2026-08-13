# duckdns.ps1 - update DuckDNS from Windows. Set DUCKDNS_DOMAIN + DUCKDNS_TOKEN in ..\\.env.
# Task Scheduler:  schtasks /create /tn DuckDNS /tr "powershell -File ...\duckdns.ps1" /sc minute /mo 5
param()
$envFile = Join-Path $PSScriptRoot "..\\.env"
if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') { Set-Item -Path "Env:$($matches[1].Trim())" -Value $matches[2].Trim().Trim('"') }
  }
}
$domain = $env:DUCKDNS_DOMAIN
$token  = $env:DUCKDNS_TOKEN
if (-not $domain -or -not $token) { Write-Host "set DUCKDNS_DOMAIN + DUCKDNS_TOKEN in ../.env" -ForegroundColor Red; exit 1 }
$res = (Invoke-RestMethod -Uri "https://www.duckdns.org/update?domains=$domain&token=$token&ip=")
Write-Host "duckdns: $res"
