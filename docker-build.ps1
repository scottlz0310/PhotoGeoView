# PowerShell script to build Electron app using Docker
# This script builds a Windows installer using Linux Docker with Wine

param(
    [switch]$SkipBuild,
    [switch]$KeepContainer
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PhotoGeoView Docker Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Clean up existing container if it exists
Write-Host "Cleaning up existing containers..." -ForegroundColor Yellow
docker rm -f photogeoview-build 2>$null | Out-Null

# Build Docker image if not skipped
if (-not $SkipBuild) {
    Write-Host "Building Docker image..." -ForegroundColor Yellow
    docker build -t photogeoview-builder .

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker image build failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Docker image built successfully" -ForegroundColor Green
    Write-Host ""
}

# Run container to build the installer
Write-Host "Running build in Docker container..." -ForegroundColor Yellow
Write-Host "(This may take several minutes)" -ForegroundColor Gray
docker run --name photogeoview-build photogeoview-builder

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed in container!" -ForegroundColor Red
    docker rm photogeoview-build 2>$null | Out-Null
    exit 1
}
Write-Host "✓ Build completed successfully" -ForegroundColor Green
Write-Host ""

# Copy build artifacts
Write-Host "Copying build artifacts..." -ForegroundColor Yellow
if (Test-Path "./dist-docker") {
    Remove-Item -Recurse -Force "./dist-docker"
}
docker cp photogeoview-build:/app/dist ./dist-docker

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to copy build artifacts!" -ForegroundColor Red
    docker rm photogeoview-build 2>$null | Out-Null
    exit 1
}
Write-Host "✓ Artifacts copied to ./dist-docker" -ForegroundColor Green
Write-Host ""

# Clean up container unless -KeepContainer is specified
if (-not $KeepContainer) {
    Write-Host "Cleaning up container..." -ForegroundColor Yellow
    docker rm photogeoview-build | Out-Null
    Write-Host "✓ Container removed" -ForegroundColor Green
    Write-Host ""
}

# Display generated files
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Generated installers:" -ForegroundColor Cyan
Get-ChildItem -Path "./dist-docker" -Recurse -File | Where-Object { $_.Extension -eq ".exe" -and $_.Name -like "*Setup*" } | ForEach-Object {
    $sizeMB = [math]::Round($_.Length / 1MB, 2)
    Write-Host "  📦 $($_.Name) ($sizeMB MB)" -ForegroundColor White
    Write-Host "     $($_.FullName)" -ForegroundColor Gray
}
Write-Host ""
Write-Host "To rebuild without rebuilding the Docker image, use:" -ForegroundColor Gray
Write-Host "  .\docker-build.ps1 -SkipBuild" -ForegroundColor Gray
Write-Host ""
