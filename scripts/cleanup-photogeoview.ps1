<#
.SYNOPSIS
    PhotoGeoView の完全クリーンアップスクリプト

.DESCRIPTION
    アンインストーラーが削除しないファイルを含め、PhotoGeoView に関連するすべてのファイルを削除します。
    新しいバージョンをインストールする前に実行することで、古いファイルによる問題を防ぎます。

.EXAMPLE
    .\cleanup-photogeoview.ps1

.EXAMPLE
    .\cleanup-photogeoview.ps1 -KeepUserData
    ユーザーデータ（設定、キャッシュ）を保持したまま、アプリケーションファイルのみを削除
#>

param(
    [switch]$KeepUserData = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PhotoGeoView 完全クリーンアップ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# プロセスを停止
Write-Host "📌 PhotoGeoView プロセスを停止中..." -ForegroundColor Yellow
try {
    $processes = Get-Process PhotoGeoView -ErrorAction SilentlyContinue
    if ($processes) {
        $processes | Stop-Process -Force
        Write-Host "   ✅ プロセスを停止しました" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️  実行中のプロセスはありません" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  プロセスの停止に失敗しました: $_" -ForegroundColor Yellow
}

Write-Host ""

# アプリケーションファイルを削除
$appPath = "$env:LOCALAPPDATA\Programs\photogeoview"
Write-Host "📌 アプリケーションファイルを削除中..." -ForegroundColor Yellow
Write-Host "   パス: $appPath" -ForegroundColor Gray
if (Test-Path $appPath) {
    try {
        Remove-Item -Recurse -Force $appPath -ErrorAction Stop
        Write-Host "   ✅ アプリケーションファイルを削除しました" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ 削除に失敗しました: $_" -ForegroundColor Red
    }
} else {
    Write-Host "   ℹ️  アプリケーションファイルは存在しません" -ForegroundColor Gray
}

Write-Host ""

# ユーザーデータを削除（オプション）
if (-not $KeepUserData) {
    $userDataPath = "$env:APPDATA\PhotoGeoView"
    Write-Host "📌 ユーザーデータを削除中..." -ForegroundColor Yellow
    Write-Host "   パス: $userDataPath" -ForegroundColor Gray
    if (Test-Path $userDataPath) {
        try {
            Remove-Item -Recurse -Force $userDataPath -ErrorAction Stop
            Write-Host "   ✅ ユーザーデータを削除しました" -ForegroundColor Green
        } catch {
            Write-Host "   ❌ 削除に失敗しました: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "   ℹ️  ユーザーデータは存在しません" -ForegroundColor Gray
    }
} else {
    Write-Host "📌 ユーザーデータを保持します" -ForegroundColor Yellow
}

Write-Host ""

# アップデーターキャッシュを削除
$updaterPath = "$env:LOCALAPPDATA\photogeoview-updater"
Write-Host "📌 アップデーターキャッシュを削除中..." -ForegroundColor Yellow
Write-Host "   パス: $updaterPath" -ForegroundColor Gray
if (Test-Path $updaterPath) {
    try {
        Remove-Item -Recurse -Force $updaterPath -ErrorAction Stop
        Write-Host "   ✅ アップデーターキャッシュを削除しました" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ 削除に失敗しました: $_" -ForegroundColor Red
    }
} else {
    Write-Host "   ℹ️  アップデーターキャッシュは存在しません" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ クリーンアップが完了しました" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "次のステップ:" -ForegroundColor Yellow
Write-Host "  1. PhotoGeoView の新しいインストーラーを実行" -ForegroundColor Cyan
Write-Host "  2. アプリを起動して動作を確認" -ForegroundColor Cyan
Write-Host ""
