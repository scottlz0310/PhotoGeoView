import { execSync } from "node:child_process";
import { existsSync, readdirSync } from "node:fs";
import { createRequire } from "node:module";
import { join, resolve } from "node:path";

if (process.platform !== "darwin") {
  console.error("build-mac.mjs must run on macOS.");
  process.exit(1);
}

const require = createRequire(import.meta.url);

const root = process.cwd();
const distDir = resolve(root, "dist");
const pkg = require(resolve(root, "package.json"));

if (!pkg?.build) {
  console.error("build config not found in package.json");
  process.exit(1);
}

const buildConfig = {
  ...pkg.build,
  publish: null,
  mac: {
    ...pkg.build.mac,
    icon: pkg.build?.mac?.icon ?? "build/icon.png",
    identity: null,
    hardenedRuntime: false,
    gatekeeperAssess: false,
  },
};

function run(cmd, args) {
  execSync([cmd, ...args].join(" "), { stdio: "inherit", cwd: root });
}

function findApp(dir) {
  if (!existsSync(dir)) {
    return null;
  }
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name.endsWith(".app")) {
        return full;
      }
      const nested = findApp(full);
      if (nested) {
        return nested;
      }
    }
  }
  return null;
}

let appPath = findApp(distDir);
if (!appPath) {
  console.log(".app not found; running electron-builder to create it.");
  run("pnpm", [
    "package",
    "--",
    "--mac",
    "--dir",
    "--publish",
    "never",
    "-c.mac.icon=build/icon.png",
    "-c.mac.identity=null",
    "-c.mac.hardenedRuntime=false",
    "-c.mac.gatekeeperAssess=false",
  ]);
  appPath = findApp(distDir);
}

if (!appPath) {
  console.error(".app bundle not found after build.");
  process.exit(1);
}

const { Packager, AppInfo } = require("app-builder-lib");
const { MacPackager } = require("app-builder-lib/out/macPackager");
const { DmgTarget } = require("dmg-builder");
const { Arch } = require("builder-util");

const arch = appPath.includes("arm64")
  ? Arch.arm64
  : appPath.includes("x64")
    ? Arch.x64
    : process.arch === "arm64"
      ? Arch.arm64
      : Arch.x64;

const packager = new Packager({ config: buildConfig, publish: "never" });
await packager.validateConfig();
packager._appInfo = new AppInfo(packager, null);
packager._framework = { name: "electron", getDefaultIcon: () => null };

const macPackager = new MacPackager(packager);
const target = new DmgTarget(macPackager, distDir);

console.log("building DMG...");
await target.build(appPath, arch);
console.log("DMG done.");
