import { execSync } from "node:child_process";
import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import { resolve } from "node:path";

const require = createRequire(import.meta.url);

const root = process.cwd();
const distDir = resolve(root, "dist");
const unpackedDir = resolve(distDir, "linux-unpacked");
const pkg = require(resolve(root, "package.json"));

if (!pkg?.build) {
  console.error("build config not found in package.json");
  process.exit(1);
}

const buildConfig = {
  ...pkg.build,
  publish: null,
  linux: {
    ...pkg.build.linux,
    icon: pkg.build?.linux?.icon ?? "build/icon.png",
  },
};

function run(cmd, args) {
  execSync([cmd, ...args].join(" "), { stdio: "inherit", cwd: root });
}

if (!existsSync(unpackedDir)) {
  console.log("linux-unpacked not found; running electron-builder to create it.");
  run("pnpm", ["package", "--", "--linux", "--publish", "never"]);
}

const { Packager, AppInfo } = require("app-builder-lib");
const { LinuxPackager } = require("app-builder-lib/out/linuxPackager");
const AppImageTarget = require("app-builder-lib/out/targets/AppImageTarget").default;
const { LinuxTargetHelper } = require("app-builder-lib/out/targets/LinuxTargetHelper");
const { Arch } = require("builder-util");

const packager = new Packager({ config: buildConfig, publish: "never" });
await packager.validateConfig();
packager._appInfo = new AppInfo(packager, null);
packager._framework = { name: "electron", getDefaultIcon: () => null };

const linuxPackager = new LinuxPackager(packager);
const helper = new LinuxTargetHelper(linuxPackager);
const target = new AppImageTarget("appimage", linuxPackager, helper, distDir);

console.log("building AppImage...");
await target.build(unpackedDir, Arch.x64);
console.log("AppImage done.");
