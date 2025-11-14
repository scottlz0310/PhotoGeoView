# PhotoGeoView 2.0

> Modern photo geo-tagging application built with Electron, TypeScript, and React 19

[![Electron](https://img.shields.io/badge/Electron-33+-blue.svg)](https://www.electronjs.org/)
[![React](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7+-blue.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF.svg)](https://vite.dev/)

## ✨ Features

- 📸 Modern photo viewing and management
- 🗺️ Interactive maps with GPS data visualization
- 🎨 Beautiful, responsive UI
- ⚡ Lightning-fast performance with Vite
- 🔒 Type-safe development with TypeScript
- 🤖 AI-friendly codebase for efficient development

## 🚀 Tech Stack

### Frontend
- **Electron 33+** - Cross-platform desktop framework
- **React 19** - Latest React with improved performance
- **TypeScript 5.7+** - Type-safe development
- **Vite 6** - Next-generation build tool (10x faster than Webpack)

### Development Tools
- **electron-vite** - Vite integration for Electron
- **Biome** - Fast linter & formatter (25x faster than ESLint/Prettier)
- **Vitest** - Fast unit testing (5x faster than Jest)
- **Playwright** - E2E testing

### Future Stack
- **React Leaflet 4** - Interactive maps
- **TailwindCSS v4** - Utility-first CSS
- **shadcn/ui** - Beautiful React components
- **Zustand** - Lightweight state management
- **TanStack Query** - Data fetching & caching
- **sharp** - High-performance image processing
- **exifreader** - EXIF metadata extraction

## 📦 Installation

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
│       ├── lib/        # Utilities
│       └── types/      # TypeScript types
├── electron.vite.config.ts  # Vite configuration
├── tsconfig.json       # TypeScript configuration
└── biome.json          # Biome configuration
```

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

## 📖 Migration from PySide6

This project is a complete rewrite of the original PySide6-based PhotoGeoView with modern web technologies. See the migration documentation for details:

- [ANALYSIS_INDEX_jp.md](./ANALYSIS_INDEX_jp.md) - Migration analysis overview
- [CODEBASE_ANALYSIS_jp.md](./CODEBASE_ANALYSIS_jp.md) - Detailed codebase analysis
- [MIGRATION_QUICK_START_jp.md](./MIGRATION_QUICK_START_jp.md) - Quick start guide

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

---

**Branch**: `electron-migration`
**Status**: 🚧 Initial setup - Ready for development
**Original**: PySide6 implementation on `main` branch
