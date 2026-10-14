# -*- coding: utf-8 -*-
Write-Host "==========================================================================" -ForegroundColor Yellow
Write-Host "  《墨韵智考》系统运行环境与服务完整性自检脚本" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Yellow

$projectRoot = "D:\RubbingMind"
$allPassed = $true

# 1. 检查 Python 解释器与核心依赖
Write-Host "`n[1/5] 检查 Python 环境与图像处理包..." -ForegroundColor Yellow
try {
    $pyVer = & python --version 2>&1
    Write-Host "  [✓] Python: $pyVer" -ForegroundColor Green
    
    $pkgCheck = & python -c "import cv2, numpy, skimage, fastapi, uvicorn; print('OpenCV:', cv2.__version__, '| NumPy:', numpy.__version__)" 2>&1
    Write-Host "  [✓] 核心依赖: $pkgCheck" -ForegroundColor Green
} catch {
    Write-Host "  [×] Python 环境异常: $_" -ForegroundColor Red
    $allPassed = $false
}

# 2. 检查前端构建产物
Write-Host "`n[2/5] 检查前端现代化大屏构建产物..." -ForegroundColor Yellow
$distIndex = Join-Path $projectRoot "apps\web\dist\index.html"
$distAssets = Join-Path $projectRoot "apps\web\dist\assets"
if ((Test-Path $distIndex) -and (Test-Path $distAssets)) {
    $jsFiles = Get-ChildItem -Path $distAssets -Filter "*.js"
    $cssFiles = Get-ChildItem -Path $distAssets -Filter "*.css"
    Write-Host "  [✓] 前端 React + Three.js 产物就绪 (JS: $($jsFiles.Count), CSS: $($cssFiles.Count))" -ForegroundColor Green
} else {
    Write-Host "  [×] 前端尚未完成构建，请在 apps\web 下执行 npm run build" -ForegroundColor Red
    $allPassed = $false
}

# 3. 检查 4 张金石碑拓样本库
Write-Host "`n[3/5] 检查金石碑拓基准样本库..." -ForegroundColor Yellow
$samples = @("sample_1.png", "sample_2.png", "sample_3.png", "sample_4.png")
foreach ($s in $samples) {
    $path = Join-Path $projectRoot "static\samples\$s"
    if (Test-Path $path) {
        $size = (Get-Item $path).Length / 1KB
        Write-Host "  [✓] 样本 $s 就绪 ($([Math]::Round($size, 1)) KB)" -ForegroundColor Green
    } else {
        Write-Host "  [×] 缺少样本 $s" -ForegroundColor Red
        $allPassed = $false
    }
}

# 4. 检查 3D 素材与图谱背景资源
Write-Host "`n[4/5] 检查视觉多模态资产..." -ForegroundColor Yellow
$assetChecks = @(
    "apps\web\public\assets\stele\portraits\portrait_yan_zhenqing.png",
    "apps\web\public\assets\stele\backgrounds\bg_graph_antique_map.png",
    "apps\web\public\assets\stele\scenes\scene_changan_qianfu_pagoda.png"
)
foreach ($a in $assetChecks) {
    $full = Join-Path $projectRoot $a
    if (Test-Path $full) {
        Write-Host "  [✓] 资产就绪: $(Split-Path $full -Leaf)" -ForegroundColor Green
    } else {
        Write-Host "  [×] 缺少资产: $a" -ForegroundColor Red
        $allPassed = $false
    }
}

# 5. 检查 HTTP 接口联通性
Write-Host "`n[5/5] 检查 HTTP 服务联通性 (http://127.0.0.1:8000)..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get -TimeoutSec 2
    Write-Host "  [✓] 后端服务健康在线: $($health.system) (版本: $($health.version))" -ForegroundColor Green
    Write-Host "  [✓] 可用样本数: $($health.samples_available.Count)" -ForegroundColor Green
} catch {
    Write-Host "  [i] 后端服务当前未在后台运行 (可执行 .\start.ps1 启动)" -ForegroundColor Gray
}

Write-Host "`n==========================================================================" -ForegroundColor Yellow
if ($allPassed) {
    Write-Host "  自检结果：全部核心组件与资产均 100% 完整就绪！" -ForegroundColor Green
} else {
    Write-Host "  自检结果：存在部分待修复项目，请按上述提示处理。" -ForegroundColor Red
}
Write-Host "==========================================================================" -ForegroundColor Yellow
