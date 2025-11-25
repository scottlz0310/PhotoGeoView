# Dockerfile for building Electron app with electron-builder
# This uses Linux to cross-compile Windows installers

FROM node:22-bookworm-slim

# Install dependencies for electron-builder and Wine for Windows cross-compilation
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    wine \
    wine32 \
    wine64 \
    && rm -rf /var/lib/apt/lists/*

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml .npmrc .pnpmrc ./

# Install dependencies (skip prepare scripts like lefthook since .git is not available)
RUN pnpm install --ignore-scripts

# Copy source code
COPY . .

# Build the application
RUN pnpm build

# Set environment to force Windows cross-compilation
ENV USE_HARD_LINKS=false

# Default command: package for Windows NSIS
CMD ["npx", "electron-builder", "-w", "nsis", "--publish", "never"]
