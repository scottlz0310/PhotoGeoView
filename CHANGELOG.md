# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.9] - 2025-11-24

### Fixed
- **Breadcrumb**: Fixed issue where Windows drive roots (e.g., `C:`) were not displaying or navigating correctly.
- **Context Menu**: Added native context menu for files, folders, and background in the file browser.
- **UI**: Removed redundant "Parent Folder" (`<`) button from navigation toolbar.

## [2.1.8] - 2025-11-22

### Added
- Comprehensive automated tests for update notification flow (10 new tests)
- Test coverage for all update scenarios: available, not available, downloading, downloaded, and error states

### Fixed
- Unused variable warning in MenuBar test file

## [2.1.7] - 2025-11-22

### Fixed
- About dialog now displays app version dynamically from package.json instead of hardcoded value
- Auto-update notifications: Added toast notifications for update checking, available, downloading, and error states
- Users now receive visual feedback when checking for updates via Help menu

### Added
- App version API (GET_APP_VERSION) to retrieve version from main process
- Update event listeners with proper user notifications in Japanese and English

## [2.1.6] - 2024-11-22

### Fixed
- Linux (AppImage) build: disable fileAssociations to fix build error with electron-builder v24

## [2.1.5] - 2024-11-22

### Fixed
- Downgrade electron-builder from v26 to v24 to fix installer build issues

## [2.1.4] - 2024-11-21

### Fixed
- Release workflow: use --publish always with create-release job to upload installers

## [2.1.3] - 2024-11-21

### Fixed
- Release workflow: explicitly specify nsis/dmg/AppImage targets to create installers

## [2.1.2] - 2024-11-21

### Fixed
- Release workflow: add `--publish never` to create installer files
- Upload glob patterns to match files in subdirectories

## [2.1.1] - 2024-11-21

### Fixed
- Release workflow now properly creates GitHub release and uploads installers

## [2.1.0] - 2024-11-21

### Added
- **Menu Bar**: New application menu with File, View, Settings, and Help menus
- **Status Bar**: EXIF information display at bottom of window (camera, exposure, GPS, date/time, dimensions)
- **Layout Presets**: Default, Preview Focus, Map Focus, and Compact layout options
- **Internationalization (i18n)**: Japanese and English language support with language selector
- **File Association**: Open images directly from file explorer (Windows)
- **Command Line Support**: Open images via command line arguments

### Changed
- Moved "Open Folder" from button to File menu
- Moved "Theme" selector to View menu
- Replaced EXIF Panel with compact Status Bar
- Improved test coverage (63% overall, 316 unit tests, 9 E2E tests)

### Removed
- Standalone "Select Folder" button (now in File menu)
- Standalone theme toggle button (now in View > Theme menu)

## [2.0.2] - 2024-11-20

### Fixed
- Various bug fixes and performance improvements

## [2.0.1] - 2024-11-19

### Fixed
- Initial bug fixes after migration

## [2.0.0] - 2024-11-18

### Added
- Complete rewrite from PySide6 to Electron + React + TypeScript
- Modern tech stack: Electron 33+, React 19, TypeScript 5.7+, Vite 6
- Interactive map with React Leaflet
- Thumbnail grid with lazy loading
- EXIF data extraction and display
- File browser with navigation history
- Image preview with zoom/pan
- Dark/Light/System theme support
- Keyboard shortcuts for navigation

### Changed
- Migrated from Python/PySide6 to TypeScript/Electron
- Replaced Qt WebEngine with Chromium (via Electron)
- Improved build performance with Vite (10x faster)
- Modern UI with TailwindCSS and shadcn/ui

[2.1.8]: https://github.com/scottlz0310/PhotoGeoView/compare/v2.1.7...v2.1.8
[2.1.7]: https://github.com/scottlz0310/PhotoGeoView/compare/v2.1.6...v2.1.7
[2.1.6]: https://github.com/scottlz0310/PhotoGeoView/compare/v2.1.5...v2.1.6
[2.1.5]: https://github.com/scottlz0310/PhotoGeoView/compare/v2.1.4...v2.1.5
[2.1.4]: https://github.com/scottlz0310/PhotoGeoView/compare/v2.1.3...v2.1.4
[2.1.3]: https://github.com/scottlz0310/PhotoGeoView/compare/v2.1.2...v2.1.3
[2.1.2]: https://github.com/scottlz0310/PhotoGeoView/compare/v2.1.1...v2.1.2
[2.1.1]: https://github.com/scottlz0310/PhotoGeoView/compare/v2.1.0...v2.1.1
[2.1.0]: https://github.com/scottlz0310/PhotoGeoView/compare/v2.0.2...v2.1.0
[2.0.2]: https://github.com/scottlz0310/PhotoGeoView/compare/v2.0.1...v2.0.2
[2.0.1]: https://github.com/scottlz0310/PhotoGeoView/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/scottlz0310/PhotoGeoView/releases/tag/v2.0.0
