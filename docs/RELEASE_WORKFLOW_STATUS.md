Release Workflow Status (copilot/fix-windows-installer-upload)
=============================================================

Scope
-----
- Branch: copilot/fix-windows-installer-upload
- Goal: fix release workflow so electron-builder produces installers and upload artifacts.
- Note: v2.1.9 assets exist because they were manually uploaded from local builds, not from a successful CI artifact build.

Current state
-------------
- Latest commits:
  - e15629f chore: set pnpm hoist config
  - 3a8ea4d ci: add targeted electron-builder debug logs
  - db1a08c ci: run electron-builder with explicit targets
  - 790be37 ci: upload release artifacts without publishing
  - 06c8fae Fix Windows installer upload by using electron-builder publishing
- Tags used for testing: v0.0.0-test1 .. v0.0.0-test5
- Node/pnpm in CI: Node v24.12.0, pnpm 10.26.1
- electron-builder in CI: 26.0.12
- Added .npmrc for pnpm hoist:
  - node-linker=hoisted
  - shamefully-hoist=true

Workflow edits done
-------------------
- .github/workflows/release.yml:
  - Added "Print tool versions" step.
  - Added DEBUG=electron-builder and ELECTRON_BUILDER_LOG_LEVEL=debug.
  - Added "Find installers" steps (dir listing).
  - Explicit platform targets set in electron-builder command (win nsis/portable, mac dmg, linux AppImage).

Observed CI behavior (v0.0.0-test4 / v0.0.0-test5)
---------------------------------------------------
- Build and packaging steps report success, but upload step fails due to missing files.
- electron-builder logs show only "packaging" and "unpack-electron" messages.
- Only unpacked output is produced:
  - Windows: dist/win-unpacked (electron.exe present, no Setup .exe)
  - macOS: dist/mac-arm64/Electron.app (no .dmg)
  - Linux: dist/linux-unpacked (no .AppImage)
- No "building target=..." lines are printed in logs for the expected targets.

Key implication
---------------
electron-builder completes the packaging stage but does not run target builders
(nsis/dmg/AppImage), so the release artifact upload fails.

Next investigation ideas (not executed yet)
-------------------------------------------
- Verify app bundle exists:
  - Check for dist/*/resources/app.asar in CI logs.
  - Check if out/ exists and contains expected files.
- Temporarily upload full dist/** for inspection.
- Add an explicit "list dist/**" step after packaging to confirm what was produced.
- Compare local electron-builder config (files, directories, targets) vs CI.

Pending user preference
-----------------------
- Do not downgrade electron-builder unless no other option.
