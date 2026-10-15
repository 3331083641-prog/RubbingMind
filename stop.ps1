$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$statePath = Join-Path $projectRoot 'data/runtime/server-process.json'
if (-not (Test-Path $statePath)) {
    Write-Host '没有由 start.ps1 记录的运行中服务。'
    exit 0
}
$state = Get-Content -Raw -Encoding UTF8 $statePath | ConvertFrom-Json
if ($state.root -ne $projectRoot) { throw 'PID 记录指向其他项目，拒绝停止。' }
$process = Get-CimInstance Win32_Process -Filter "ProcessId=$($state.pid)" -ErrorAction SilentlyContinue
if (-not $process) {
    Remove-Item -LiteralPath $statePath
    Write-Host '记录的服务已退出。'
    exit 0
}
$command = [string]$process.CommandLine
if (-not ($command.Contains('uvicorn main:app') -and $command.Contains($projectRoot))) {
    throw 'PID 已被其他进程使用，拒绝停止。'
}
Stop-Process -Id $state.pid -ErrorAction Stop
Remove-Item -LiteralPath $statePath
Write-Host "已停止本项目服务 PID $($state.pid)。"
