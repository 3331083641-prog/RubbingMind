# -*- coding: utf-8 -*-
Write-Host "==========================================================================" -ForegroundColor Yellow
Write-Host "  《墨韵智考》——金石碑拓微痕修复与智能史料考据系统 (RubbingMind Pro 2.0)" -ForegroundColor Cyan
Write-Host "  全球校园人工智能算法精英大赛（智能文化赛道）全栈运行环境启动" -ForegroundColor DarkYellow
Write-Host "==========================================================================" -ForegroundColor Yellow

$projectRoot = "D:\RubbingMind"
Set-Location $projectRoot

# 1. 检查端口占用并清理
$existingConn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($existingConn) {
    Write-Host "[!] 检测到 8000 端口已被占用，正在释放..." -ForegroundColor Yellow
    $pidToKill = $existingConn.OwningProcess | Select-Object -Unique
    Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# 2. 检查前端生产构建
$distIndex = Join-Path $projectRoot "apps\web\dist\index.html"
if (-not (Test-Path $distIndex)) {
    Write-Host "[*] 检测到前端尚未构建，正在编译 React + Three.js 现代化大屏..." -ForegroundColor Cyan
    Set-Location (Join-Path $projectRoot "apps\web")
    npm run build
    Set-Location $projectRoot
}

# 3. 启动 FastAPI 后端服务
Write-Host "[*] 正在启动 FastAPI 后端服务 (http://127.0.0.1:8000)..." -ForegroundColor Green
$serverJob = Start-Process python -ArgumentList "main.py" -WorkingDirectory $projectRoot -PassThru -WindowStyle Hidden

# 4. 等待服务就绪
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Milliseconds 800
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get -TimeoutSec 2
        if ($resp.status -eq "healthy") {
            $ready = $true
            break
        }
    } catch {
        # continue waiting
    }
}

if ($ready) {
    Write-Host "[✓] 《墨韵智考》前后端服务已成功启动！" -ForegroundColor Green
    Write-Host "    - 服务主入口: http://127.0.0.1:8000" -ForegroundColor Cyan
    Write-Host "    - OpenAPI 文档: http://127.0.0.1:8000/docs" -ForegroundColor DarkCyan
    Write-Host "    - 正在自动打开默认浏览器访问系统..." -ForegroundColor Yellow
    Start-Process "http://127.0.0.1:8000"
} else {
    Write-Host "[×] 服务启动超时，请运行 check.ps1 检查日志及依赖环境。" -ForegroundColor Red
}
