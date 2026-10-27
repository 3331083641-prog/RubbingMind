$projectRoot = $PSScriptRoot
$statePath = Join-Path $projectRoot 'data/runtime/server-process.json'
$failures = @()
try { & python -c "import cv2,numpy,skimage,fastapi,uvicorn; print('Python dependencies OK')" } catch { $failures += 'Python dependencies' }
if (-not (Test-Path (Join-Path $projectRoot 'apps/web/dist/index.html'))) { $failures += 'Frontend build' }
foreach ($name in @('sample_1.png','sample_2.png','sample_3.png','sample_4.png')) {
    if (-not (Test-Path (Join-Path $projectRoot "static/samples/$name"))) { $failures += $name }
}
if (Test-Path $statePath) {
    $state = Get-Content -Raw -Encoding UTF8 $statePath | ConvertFrom-Json
    if ($state.root -eq $projectRoot) {
        try {
            # RT-011: GET health only (remote-safe)
            $health = Invoke-RestMethod "http://127.0.0.1:$($state.port)/api/health" -TimeoutSec 3
            if ($health.status -ne 'healthy' -and $health.status -ne 'degraded') { $failures += '/api/health' }
            Write-Host "服务：http://127.0.0.1:$($state.port)"
        } catch { $failures += 'Backend /api/health' }
    } else { $failures += 'Server PID record' }
} else { Write-Host '服务未由 start.ps1 启动。' }
if ($failures.Count) {
    Write-Error ("检查未通过：" + ($failures -join '、'))
    exit 1
}
Write-Host '项目依赖、前端产物、四件样本与运行服务检查通过。'
