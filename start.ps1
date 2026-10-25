param(
    [int]$Port = 0
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$webRoot = Join-Path $projectRoot 'apps/web'
$distIndex = Join-Path $webRoot 'dist/index.html'
$runtime = Join-Path $projectRoot 'data/runtime'
$statePath = Join-Path $runtime 'server-process.json'

if (Test-Path $statePath) {
    $old = Get-Content -Raw -Encoding UTF8 $statePath | ConvertFrom-Json
    $running = Get-CimInstance Win32_Process -Filter "ProcessId=$($old.pid)" -ErrorAction SilentlyContinue
    if ($running -and $running.CommandLine.Contains('uvicorn main:app') -and $running.CommandLine.Contains($projectRoot)) {
        Write-Host "本项目服务已经启动：http://127.0.0.1:$($old.port)"
        exit 0
    }
    Remove-Item -LiteralPath $statePath
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw '未找到 Python，请先安装依赖。' }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw '未找到 npm，请先安装 Node.js。' }
if (-not (Test-Path (Join-Path $webRoot 'node_modules'))) {
    Push-Location $webRoot
    try { & npm ci; if ($LASTEXITCODE -ne 0) { throw 'npm ci 失败' } }
    finally { Pop-Location }
}
$sourceFiles = Get-ChildItem (Join-Path $webRoot 'src') -Recurse -File
$sourceFiles += Get-Item (Join-Path $webRoot 'index.html')
$needsBuild = -not (Test-Path $distIndex)
if (-not $needsBuild) {
    $builtAt = (Get-Item $distIndex).LastWriteTimeUtc
    $needsBuild = [bool]($sourceFiles | Where-Object LastWriteTimeUtc -GT $builtAt | Select-Object -First 1)
}
if ($needsBuild) {
    Push-Location $webRoot
    try { & npm run build; if ($LASTEXITCODE -ne 0) { throw '前端构建失败' } }
    finally { Pop-Location }
}
New-Item -ItemType Directory -Path $runtime -Force | Out-Null
# RT-003: honor -Port when provided (e.g. start.ps1 -Port 8740)
if ($Port -gt 0) {
    $port = $Port
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        throw "端口 $port 已被占用，请换一个 -Port。"
    }
} else {
    $port = 8000
    while (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) { $port++ }
    if ($port -gt 8100) { throw '8000–8100 端口均已占用。请使用 start.ps1 -Port <端口>。' }
}
$logPath = Join-Path $runtime 'server.log'
$errPath = Join-Path $runtime 'server-error.log'
$process = Start-Process python -ArgumentList @('-m','uvicorn','main:app','--app-dir',"`"$projectRoot`"",'--host','127.0.0.1','--port',"$port") -WorkingDirectory $projectRoot -RedirectStandardOutput $logPath -RedirectStandardError $errPath -PassThru -WindowStyle Hidden
$ready = $false
for ($i = 0; $i -lt 25; $i++) {
    Start-Sleep -Milliseconds 500
    if ($process.HasExited) { break }
    try {
        $health = Invoke-RestMethod "http://127.0.0.1:$port/health" -TimeoutSec 2
        $generated = Invoke-RestMethod "http://127.0.0.1:$port/generate" -Method Post -TimeoutSec 5
        if ($health.status -eq 'healthy' -and $generated) { $ready = $true; break }
    } catch {}
}
if (-not $ready) {
    if (-not $process.HasExited) { Stop-Process -Id $process.Id -ErrorAction SilentlyContinue }
    throw "服务未通过 /health 和 /generate 检查。查看 $errPath"
}
@{ pid = $process.Id; port = $port; root = $projectRoot; startedAt = (Get-Date).ToUniversalTime().ToString('o') } |
    ConvertTo-Json | Set-Content -Encoding UTF8 $statePath
Write-Host "墨韵智考已启动：http://127.0.0.1:$port"