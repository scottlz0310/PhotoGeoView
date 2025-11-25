# Dockerfile for building Electron app with electron-builder
# Cross-compile Windows installer on Linux using Wine

FROM node:22-bookworm-slim

# Install system dependencies (Wine for Windows builds)
RUN dpkg --add-architecture i386 \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    wine \
    wine32 \
    wine64 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pnpm (via corepack)
RUN corepack enable && corepack prepare pnpm@latest --activate

# Set working directory
WORKDIR /app

# Copy package manifests first (allows Docker layer caching)
COPY package.json pnpm-lock.yaml .npmrc .pnpmrc ./

# Install all dependencies without running prepare scripts (lefthook fails without .git)
RUN pnpm install --ignore-scripts

# Manually download and install Windows sharp binaries
# This is necessary because pnpm/npm install scripts don't work correctly in Docker without .git
RUN mkdir -p node_modules/@img/sharp-win32-x64 node_modules/@img/sharp-libvips-win32-x64 \
    && cd node_modules/@img/sharp-win32-x64 \
    && npm pack @img/sharp-win32-x64@0.34.5 \
    && tar -xzf *.tgz --strip-components=1 \
    && rm *.tgz \
    && cd ../sharp-libvips-win32-x64 \
    && npm pack @img/sharp-libvips-win32-x64@1.2.4 \
    && tar -xzf *.tgz --strip-components=1 \
    && rm *.tgz

# Copy the rest of the source code
COPY . .

# Build the application (typescript, etc.)
RUN pnpm build

# Set environment to force Windows cross-compilation
ENV USE_HARD_LINKS=false

# Default command: package for Windows NSIS installer
CMD ["npx", "electron-builder", "-w", "nsis", "--publish", "never"]
