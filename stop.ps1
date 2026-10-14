# -*- coding: utf-8 -*-
Write-Host "正在停止《墨韵智考》后台服务..." -ForegroundColor Yellow

$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($conn) {
    $processes = $conn.OwningProcess | Select-Object -Unique
    foreach ($pidToKill in $processes) {
        Write-Host "终止进程 PID: $pidToKill" -ForegroundColor Cyan
        Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[✓] 《墨韵智考》服务已停止，8000 端口已安全释放。" -ForegroundColor Green
} else {
    Write-Host "[i] 当前未检测到正在运行的 8000 端口服务。" -ForegroundColor Gray
}
