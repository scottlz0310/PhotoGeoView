# PhotoGeoView 2.2.0

> 📍 写真に埋め込まれた位置情報を地図上に見える化するスタンドアロンアプリ。Electron・TypeScript・Reactベースで、Exifデータを解析し地図上にプロット。

[![CI](https://github.com/scottlz0310/PhotoGeoView/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/scottlz0310/PhotoGeoView/actions/workflows/ci.yml)
[![Electron](https://img.shields.io/badge/Electron-33+-blue.svg)](https://www.electronjs.org/)
[![React](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7+-blue.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF.svg)](https://vite.dev/)

## ✨ Features

- 📸 Modern photo viewing and management
- 🗺️ Interactive maps with GPS data visualization
- 🎨 Beautiful, responsive UI with layout presets
- 🌐 Internationalization (English / 日本語)
- ⚡ Lightning-fast performance with Vite
- 🔒 Type-safe development with TypeScript
- 🤖 AI-friendly codebase for efficient development

## 🆕 What's New in 2.2.0

- **Windows Icons**: Fixed transparent ICO generation and taskbar/window icon display
- **Packaging**: Auto-generates `build/icon.ico` from `assets/icon.png` during `pnpm package`

See [CHANGELOG.md](./CHANGELOG.md) for full details.

## 🚀 Tech Stack

### Frontend
- **Electron 33+** - Cross-platform desktop framework
- **React 19** - Latest React with improved performance
- **TypeScript 5.7+** - Type-safe development
- **Vite 6** - Next-generation build tool (10x faster than Webpack)
- **React Leaflet 4** - Interactive maps
- **TailwindCSS v4** - Utility-first CSS
- **shadcn/ui** - Beautiful React components
- **Zustand** - Lightweight state management
- **TanStack Query** - Data fetching & caching
- **i18next** - Internationalization

### Core Features

- **sharp** - High-performance image processing
- **exifreader** - EXIF metadata extraction

### Development Tools

- **electron-vite** - Vite integration for Electron
- **Biome** - Fast linter & formatter (25x faster than ESLint/Prettier)
- **Vitest** - Fast unit testing (5x faster than Jest)
- **Playwright** - E2E testing

## 📥 Download

Latest release is available on [GitHub Releases](https://github.com/scottlz0310/PhotoGeoView/releases).

- **Windows**: Download `.exe` installer
- **macOS**: Download `.dmg` image
- **Linux**: Download `.AppImage`

## 📦 Development Setup

```bash
# Install dependencies
pnpm install

# Start development
pnpm dev

# Build for production
pnpm build

# Run tests
pnpm test

# Lint & format
pnpm lint
pnpm format
```

## 🏗️ Project Structure

```
PhotoGeoView/
├── src/
│   ├── main/           # Electron main process
│   ├── preload/        # Preload scripts (IPC bridge)
│   └── renderer/       # React renderer process
│       ├── components/ # React components
│       ├── hooks/      # Custom React hooks
│       ├── i18n/       # Internationalization
│       ├── lib/        # Utilities
│       └── stores/     # Zustand stores
├── docs/               # Documentation
├── tests/              # Test files
├── electron.vite.config.ts  # Vite configuration
├── tsconfig.json       # TypeScript configuration
└── biome.json          # Biome configuration
```

## 📊 Quality & Testing

**Current Status:**
- ✅ Test Coverage: 63%
- ✅ Unit Tests: 316 passing
- ✅ E2E Tests: 9 passing
- ✅ CI/CD: All checks passing

## 🔧 Development

### Prerequisites
- Node.js 20+
- pnpm 9+

### Commands

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start development server |
| `pnpm build` | Build for production |
| `pnpm typecheck` | Run TypeScript type checking |
| `pnpm lint` | Run Biome linter |
| `pnpm lint:fix` | Fix linting issues |
| `pnpm format` | Format code |
| `pnpm test` | Run unit tests |
| `pnpm test:ui` | Run tests with UI |
| `pnpm test:e2e` | Run E2E tests |
| `pnpm package` | Package app for distribution |

### Building for Windows

**Important**: Building for Windows requires administrator privileges or Windows Developer Mode enabled.

#### Option 1: Run as Administrator

1. Open PowerShell as Administrator
2. Navigate to project directory
3. Run build command:

```powershell
pnpm package -- --win --publish never
```

#### Option 2: Enable Windows Developer Mode

1. Go to **Settings** → **Privacy & Security** → **For developers**
2. Turn on **Developer Mode**
3. Build with normal PowerShell

## 🔧 Troubleshooting

### Sharp Module Error

If you encounter the following error when launching the app:

```
Error: Could not load the "sharp" module using the win32-x64 runtime
```

This is caused by incomplete uninstallation leaving old files behind. Run the cleanup script before reinstalling:

```powershell
.\scripts\cleanup-photogeoview.ps1
```

To keep user data (settings, cache):

```powershell
.\scripts\cleanup-photogeoview.ps1 -KeepUserData
```

For more troubleshooting information, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## 📖 Documentation

### Migration from PySide6

This project is a complete rewrite of the original PySide6-based PhotoGeoView with modern web technologies.

**Migration Documentation (Japanese):**

1. **[ANALYSIS_INDEX_jp.md](./docs/ANALYSIS_INDEX_jp.md)** - 移行分析の概要
2. **[CODEBASE_ANALYSIS_jp.md](./docs/CODEBASE_ANALYSIS_jp.md)** - 詳細なコードベース分析
3. **[MIGRATION_QUICK_START_jp.md](./docs/MIGRATION_QUICK_START_jp.md)** - クイックスタートガイド

### Why the Migration?

- **Type Safety**: TypeScript provides better AI-assisted development
- **Performance**: 5-25x faster build/test/lint tools
- **Modern Stack**: Latest React 19, Vite 6, all actively maintained
- **Cross-Platform**: Native Chromium, no WebEngine complexity
- **Developer Experience**: Hot reload, better debugging, modern tooling

## 🤝 Contributing

We welcome contributions! This project is designed for AI-driven development with TypeScript, making it easy to:

- Add features with AI assistance
- Refactor with confidence (type safety)
- Test comprehensively (Vitest + Playwright)
- Maintain code quality (Biome)

## 📄 License

MIT

## 🙏 Acknowledgments

Built with:
- 🤖 AI-assisted development (Claude Code)
- ⚡ Modern web technologies
- 💙 Open source community
