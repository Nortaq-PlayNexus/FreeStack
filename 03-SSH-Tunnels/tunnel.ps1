# tunnel.ps1 - Windows: expose a local port publicly with zero install (uses built-in ssh).
# Usage:
#   .\tunnel.ps1 -Port 8080
#   .\tunnel.ps1 -Port 8080 -Provider serveo
#   .\tunnel.ps1 -Port 8080 -Provider cloudflared   # needs cloudflared installed
param(
  [Parameter(Mandatory=$true)][int]$Port,
  [ValidateSet("localhostrun","serveo","mekong","cloudflared")]
  [string]$Provider = "localhostrun",
  [string]$HostAddr = "localhost"
)

$target = "${HostAddr}:${Port}"

switch ($Provider) {
  "localhostrun" {
    Write-Host ">> Opening public tunnel to ${target} (Ctrl+C to stop)"
    ssh -R "80:${target}" nokey@localhost.run
  }
  "serveo" {
    Write-Host ">> Opening public tunnel to ${target} (Ctrl+C to stop)"
    ssh -R "80:${target}" serveo.net
  }
  "mekong" {
    Write-Host ">> Opening public tunnel to ${target} (Ctrl+C to stop)"
    ssh -t -R "80:${target}" proxy.angkorsearch.dev
  }
  "cloudflared" {
    if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
      Write-Error "cloudflared not found. Install: winget install cloudflare.cloudflared"
      exit 1
    }
    Write-Host ">> Cloudflare quick tunnel to ${target} (Ctrl+C to stop)"
    cloudflared tunnel --url "http://${target}"
  }
}
