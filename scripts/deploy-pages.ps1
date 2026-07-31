# Publishes the front-end to GitHub Pages under
#   https://<owner>.github.io/<repo>/723-oeh-singmeasong/
#
# It writes into a sub-directory of the gh-pages branch and keeps whatever
# else already lives there, so other deployments on that branch survive.
#
# Usage (from the repository root):
#   pwsh ./scripts/deploy-pages.ps1
#   pwsh ./scripts/deploy-pages.ps1 -ApiBaseUrl https://my-api.onrender.com

param(
  [string]$Branch = "723-oeh-singmeasong",
  [string]$Repo = "ManuDiasCruz/ai-training-workspace-may",
  [string]$ApiBaseUrl = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$frontEnd = Join-Path $root "front-end"
$repoName = $Repo.Split("/")[1]
$publicUrl = "/$repoName/$Branch"

Write-Host "Building front-end for $publicUrl ..."
Push-Location $frontEnd
try {
  $env:PUBLIC_URL = $publicUrl
  $env:CI = "true"
  if ($ApiBaseUrl) { $env:REACT_APP_API_BASE_URL = $ApiBaseUrl }

  npm run build
  if ($LASTEXITCODE -ne 0) { throw "front-end build failed" }

  # GitHub Pages has no SPA rewrite: serving 404.html from the built
  # index.html lets /top and /random survive a hard reload.
  Copy-Item (Join-Path $frontEnd "build\index.html") (Join-Path $frontEnd "build\404.html") -Force
}
finally {
  Remove-Item Env:PUBLIC_URL -ErrorAction SilentlyContinue
  Remove-Item Env:CI -ErrorAction SilentlyContinue
  Remove-Item Env:REACT_APP_API_BASE_URL -ErrorAction SilentlyContinue
  Pop-Location
}

$work = Join-Path ([System.IO.Path]::GetTempPath()) "gh-pages-$Branch"
if (Test-Path $work) { Remove-Item $work -Recurse -Force }

Write-Host "Cloning gh-pages ..."
git clone --depth 1 --branch gh-pages "https://github.com/$Repo.git" $work
if ($LASTEXITCODE -ne 0) { throw "could not clone the gh-pages branch" }

$target = Join-Path $work $Branch
if (Test-Path $target) { Remove-Item $target -Recurse -Force }
New-Item -ItemType Directory -Path $target | Out-Null

Copy-Item (Join-Path $frontEnd "build\*") $target -Recurse -Force

Push-Location $work
try {
  git add -A
  git commit -m "deploy($Branch): publish sing-me-a-song front-end"
  git push origin gh-pages
  if ($LASTEXITCODE -ne 0) { throw "push to gh-pages failed" }
}
finally { Pop-Location }

Write-Host "Published to https://$($Repo.Split('/')[0]).github.io/$repoName/$Branch/"
