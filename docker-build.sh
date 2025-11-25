#!/bin/bash
# Bash script to build Electron app using Docker
# This script builds a Windows installer using Linux Docker with Wine

set -e

SKIP_BUILD=false
KEEP_CONTAINER=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --keep-container)
            KEEP_CONTAINER=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-build] [--keep-container]"
            exit 1
            ;;
    esac
done

echo "========================================"
echo "PhotoGeoView Docker Build Script"
echo "========================================"
echo ""

# Clean up existing container if it exists
echo "Cleaning up existing containers..."
docker rm -f photogeoview-build 2>/dev/null || true

# Build Docker image if not skipped
if [ "$SKIP_BUILD" = false ]; then
    echo "Building Docker image..."
    docker build -t photogeoview-builder .

    if [ $? -ne 0 ]; then
        echo "❌ Docker image build failed!"
        exit 1
    fi
    echo "✓ Docker image built successfully"
    echo ""
fi

# Run container to build the installer
echo "Running build in Docker container..."
echo "(This may take several minutes)"
docker run --name photogeoview-build photogeoview-builder

if [ $? -ne 0 ]; then
    echo "❌ Build failed in container!"
    docker rm photogeoview-build 2>/dev/null || true
    exit 1
fi
echo "✓ Build completed successfully"
echo ""

# Copy build artifacts
echo "Copying build artifacts..."
if [ -d "./dist-docker" ]; then
    rm -rf "./dist-docker"
fi
docker cp photogeoview-build:/app/dist ./dist-docker

if [ $? -ne 0 ]; then
    echo "❌ Failed to copy build artifacts!"
    docker rm photogeoview-build 2>/dev/null || true
    exit 1
fi
echo "✓ Artifacts copied to ./dist-docker"
echo ""

# Clean up container unless --keep-container is specified
if [ "$KEEP_CONTAINER" = false ]; then
    echo "Cleaning up container..."
    docker rm photogeoview-build >/dev/null
    echo "✓ Container removed"
    echo ""
fi

# Display generated files
echo "========================================"
echo "Build completed successfully!"
echo "========================================"
echo ""
echo "Generated installers:"
find ./dist-docker -type f -name "*Setup*.exe" | while read file; do
    size=$(du -h "$file" | cut -f1)
    echo "  📦 $(basename "$file") ($size)"
    echo "     $file"
done
echo ""
echo "To rebuild without rebuilding the Docker image, use:"
echo "  ./docker-build.sh --skip-build"
echo ""
