# Create GitHub Release v1.0.1 (requires GITHUB_TOKEN or gh auth)
# Usage:
#   $env:GITHUB_TOKEN = "ghp_..."
#   .\scripts\create_github_release.ps1

$ErrorActionPreference = "Stop"
$repo = "Z3Pineda/ensanut-explorer"
$tag = "v1.0.1"
$bodyPath = Join-Path $PSScriptRoot "..\GITHUB_RELEASE_v1.0.1.md"
$body = Get-Content $bodyPath -Raw

$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($gh) {
    gh release create $tag --repo $repo --title "ENSANUT Explorer v1.0.1" --notes-file $bodyPath
    gh release view $tag --repo $repo --web
    exit 0
}

if (-not $env:GITHUB_TOKEN) {
    Write-Error "Install gh (gh auth login) or set GITHUB_TOKEN"
}

$payload = @{
    tag_name = $tag
    name = "ENSANUT Explorer v1.0.1"
    body = $body
    draft = $false
    prerelease = $false
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "https://api.github.com/repos/$repo/releases" `
    -Method Post `
    -Headers @{
        Authorization = "Bearer $env:GITHUB_TOKEN"
        Accept = "application/vnd.github+json"
    } `
    -Body $payload `
    -ContentType "application/json"

Write-Host "Release created: https://github.com/$repo/releases/tag/$tag"
