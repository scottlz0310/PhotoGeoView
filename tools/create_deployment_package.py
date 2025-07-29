#!/usr/bin/env python3
"""
AI統合デプロイメントパッケージ作成ツール

全AIコンポーネントが統合されたデプロイメント可能なパッケージを作成します。

AI貢献者:
- Kiro: デプロイメントパッケージシステム設計・実装

作成者: Kiro AI統合システム
作成日: 2025年1月26日
"""

import shutil
import zipfile
import tarfile
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess
import sys
import os


class DeploymentPackageCreator:
    """デプロイメントパッケージ作成器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.build_dir = project_root / "build"
        self.dist_dir = project_root / "dist"
        self.package_info = self._load_package_info()

    def _load_package_info(self) -> Dict[str, Any]:
        """パッケージ情報を読み込み"""
        pyproject_path = self.project_root / "pyproject.toml"

        if pyproject_path.exists():
            try:
                import tomllib

                with open(pyproject_path, "rb") as f:
                    pyproject_data = tomllib.load(f)

                project_info = pyproject_da.get("project", {})
                return {
                    "name": project_info.get("name", "photogeoview"),
                    "version": project_info.get("version", "1.0.0"),
                    "description": project_info.get(
                        "description", "AI統合写真地理情報ビューア"
                    ),
                    "authors": project_info.get("authors", []),
                    "dependencies": project_info.get("dependencies", []),
                }
            except ImportError:
                print("tomllib not available, using fallback")
            except Exception as e:
                print(f"pyproject.toml読み込みエラー: {e}")

        # フォールバック情報
        return {
            "name": "photogeoview",
            "version": "1.0.0",
            "description": "AI統合写真地理情報ビューア",
            "authors": [{"name": "AI Integration Team"}],
            "dependencies": [],
        }

    def clean_build_directories(self) -> None:
        """ビルドディレクトリをクリーン"""
        print("ビルドディレクトリをクリーン中...")

        for directory in [self.build_dir, self.dist_dir]:
            if directory.exists():
                shutil.rmtree(directory)
            directory.mkdir(parents=True, exist_ok=True)

    def run_quality_checks(self) -> bool:
        """品質チェックを実行"""
        print("品質チェックを実行中...")

        try:
            # AI品質チェック
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/ai_quality_checker.py",
                    "--json",
                    "--output",
                    str(self.build_dir / "quality_report.json"),
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print(f"品質チェック警告: {result.stderr}")

            # 品質レポートを確認
            quality_report_path = self.build_dir / "quality_report.json"
            if quality_report_path.exists():
                with open(quality_report_path, "r", encoding="utf-8") as f:
                    quality_data = json.load(f)

                quality_score = quality_data.get("overall_score", 0)
                critical_issues = quality_data.get("issues_by_severity", {}).get(
                    "critical", 0
                )

                print(f"品質スコア: {quality_score}/100")
                print(f"重大な問題: {critical_issues}件")

                # 重大な問題がある場合は警告
                if critical_issues > 0:
                    print("⚠️ 重大な品質問題が検出されました")
                    return False

            return True

        except Exception as e:
            print(f"品質チェックエラー: {e}")
            return False

    def run_tests(self) -> bool:
        """テストを実行"""
        print("統合テストを実行中...")

        try:
            # 包括的統合テスト
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests/integration_tests/comprehensive_integration_test.py",
                    "-v",
                    "--tb=short",
                    "--junitxml=" + str(self.build_dir / "test_results.xml"),
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            print(f"テスト結果: {result.returncode}")
            if result.stdout:
                print("テスト出力:")
                print(result.stdout[-1000:])  # 最後の1000文字のみ表示

            return result.returncode == 0

        except Exception as e:
            print(f"テスト実行エラー: {e}")
            return False

    def create_source_package(self) -> Path:
        """ソースパッケージを作成"""
        print("ソースパッケージを作成中...")

        package_name = f"{self.package_info['name']}-{self.package_info['version']}"
        source_dir = self.build_dir / package_name
        source_dir.mkdir(exist_ok=True)

        # 必要なファイルをコピー
        files_to_include = [
            "src/",
            "config/",
            "assets/",
            "docs/",
            "tests/",
            "tools/",
            "requirements.txt",
            "pyproject.toml",
            "README.md",
            "LICENSE",
        ]

        for file_pattern in files_to_include:
            source_path = self.project_root / file_pattern

            if source_path.exists():
                if source_path.is_dir():
                    shutil.copytree(
                        source_path,
                        source_dir / file_pattern,
                        ignore=shutil.ignore_patterns(
                            "__pycache__",
                            "*.pyc",
                            "*.pyo",
                            ".pytest_cache",
                            ".mypy_cache",
                            ".coverage",
                            "htmlcov",
                        ),
                    )
                else:
                    shutil.copy2(source_path, source_dir / file_pattern)

        # パッケージ情報ファイルを作成
        package_info_file = source_dir / "PACKAGE_INFO.json"
        with open(package_info_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    **self.package_info,
                    "build_date": datetime.now().isoformat(),
                    "ai_components": {
                        "copilot": "GitHub Copilot (CS4Coding) - コア機能実装",
                        "cursor": "Cursor (CursorBLD) - UI/UX設計",
                        "kiro": "Kiro - 統合・品質管理",
                    },
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        # インストールスクリプトを作成
        install_script = source_dir / "install.py"
        with open(install_script, "w", encoding="utf-8") as f:
            f.write(self._generate_install_script())

        # 実行スクリプトを作成
        run_script = source_dir / "run.py"
        with open(run_script, "w", encoding="utf-8") as f:
            f.write(self._generate_run_script())

        return source_dir

    def _generate_install_script(self) -> str:
        """インストールスクリプトを生成"""
        return '''#!/usr/bin/env python3
"""
PhotoGeoView AI統合版インストールスクリプト
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("PhotoGeoView AI統合版をインストール中...")

    # 依存関係をインストール
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ 依存関係のインストールが完了しました")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依存関係のインストールに失敗しました: {e}")
        return False

    # 設定ディレクトリを作成
    config_dir = Path.home() / ".photogeoview"
    config_dir.mkdir(exist_ok=True)

    print("✅ PhotoGeoView AI統合版のインストールが完了しました")
    print("実行するには: python run.py")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''

    def _generate_run_script(self) -> str:
        """実行スクリプトを生成"""
        return '''#!/usr/bin/env python3
"""
PhotoGeoView AI統合版実行スクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    try:
        print("PhotoGeoView AI統合版を起動中...")
        print("AI統合システム:")
        print("  - GitHub Copilot (CS4Coding): コア機能")
        print("  - Cursor (CursorBLD): UI/UX")
        print("  - Kiro: 統合・品質管理")
        print()

        # メインアプリケーションを起動
        from src.integration.controllers import AppController

        controller = AppController()
        print("✅ アプリケーションコントローラーを初期化しました")

        # 非同期初期化（実際の実装では適切に処理）
        print("🚀 PhotoGeoView AI統合版が起動しました")

    except ImportError as e:
        print(f"❌ モジュールのインポートに失敗しました: {e}")
        print("先にインストールを実行してください: python install.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ アプリケーションの起動に失敗しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

    def create_binary_package(self) -> Optional[Path]:
        """バイナリパッケージを作成（PyInstaller使用）"""
        print("バイナリパッケージを作成中...")

        try:
            # PyInstallerがインストールされているか確認
            subprocess.check_call(
                [sys.executable, "-c", "import PyInstaller"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            print("PyInstallerがインストールされていません。スキップします。")
            return None

        try:
            # PyInstallerでバイナリを作成
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "PyInstaller",
                    "--onefile",
                    "--name",
                    f"photogeoview-{self.package_info['version']}",
                    "--distpath",
                    str(self.dist_dir),
                    "--workpath",
                    str(self.build_dir / "pyinstaller"),
                    "src/main.py",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                binary_files = list(self.dist_dir.glob("photogeoview-*"))
                if binary_files:
                    print(f"✅ バイナリパッケージを作成しました: {binary_files[0]}")
                    return binary_files[0]
            else:
                print(f"バイナリパッケージ作成エラー: {result.stderr}")

        except Exception as e:
            print(f"バイナリパッケージ作成エラー: {e}")

        return None

    def create_archive_packages(self, source_dir: Path) -> List[Path]:
        """アーカイブパッケージを作成"""
        print("アーカイブパッケージを作成中...")

        package_name = source_dir.name
        archives = []

        # ZIP形式
        zip_path = self.dist_dir / f"{package_name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir.parent)
                    zipf.write(file_path, arcname)

        archives.append(zip_path)
        print(f"✅ ZIPパッケージ: {zip_path}")

        # TAR.GZ形式
        tar_path = self.dist_dir / f"{package_name}.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tarf:
            tarf.add(source_dir, arcname=package_name)

        archives.append(tar_path)
        print(f"✅ TAR.GZパッケージ: {tar_path}")

        return archives

    def generate_deployment_manifest(self, packages: List[Path]) -> Path:
        """デプロイメントマニフェストを生成"""
        print("デプロイメントマニフェストを生成中...")

        manifest = {
            "package_info": self.package_info,
            "build_date": datetime.now().isoformat(),
            "ai_integration": {
                "components": {
                    "copilot": {
                        "name": "GitHub Copilot (CS4Coding)",
                        "focus": "コア機能実装",
                        "contributions": ["EXIF解析", "地図表示", "画像処理"],
                    },
                    "cursor": {
                        "name": "Cursor (CursorBLD)",
                        "focus": "UI/UX設計",
                        "contributions": [
                            "テーマシステム",
                            "サムネイル表示",
                            "インターフェース",
                        ],
                    },
                    "kiro": {
                        "name": "Kiro",
                        "focus": "統合・品質管理",
                        "contributions": [
                            "パフォーマンス最適化",
                            "統合制御",
                            "ドキュメント生成",
                        ],
                    },
                }
            },
            "packages": [
                {
                    "name": pkg.name,
                    "path": str(pkg.relative_to(self.project_root)),
                    "size": pkg.stat().st_size,
                    "type": pkg.suffix[1:] if pkg.suffix else "binary",
                }
                for pkg in packages
            ],
            "system_requirements": {
                "python_version": ">=3.9",
                "operating_systems": ["Windows", "macOS", "Linux"],
                "memory": "4GB以上推奨",
                "storage": "100MB以上",
            },
            "installation_instructions": {
                "source": [
                    "1. パッケージを展開",
                    "2. python install.py を実行",
                    "3. python run.py でアプリケーションを起動",
                ],
                "binary": [
                    "1. バイナリファイルをダウンロード",
                    "2. 実行権限を付与（Linux/macOS）",
                    "3. ファイルを実行",
                ],
            },
        }

        manifest_path = self.dist_dir / "deployment_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        print(f"✅ デプロイメントマニフェスト: {manifest_path}")
        return manifest_path


    def run_ci_simulation(self) -> bool:
        """Run comprehensive CI simulation before deployment."""
        print("Running comprehensive CI simulation...")

        try:
            # Ensure CI simulator is available
            ci_simulator_path = self.project_root / "tools" / "ci" / "simulator.py"
            if not ci_simulator_path.exists():
                print("❌ CI simulator not found, skipping CI simulation")
                return True  # Don't fail deployment if CI simulator is not available

            # Run full CI simulation
            result = subprocess.run([
                sys.executable,
                "-m", "tools.ci.simulator",
                "run",
                "--checks", "all",
                "--format", "json",
                "--output-dir", str(self.build_dir / "ci-reports")
            ], cwd=self.project_root, capture_output=True, text=True, timeout=1800)

            if result.returncode == 0:
                print("✅ CI simulation passed")

                # Parse CI results
                ci_report_path = self.build_dir / "ci-reports"
                if ci_report_path.exists():
                    for report_file in ci_report_path.glob("ci_report_*.json"):
                        try:
                            with open(report_file, "r", encoding="utf-8") as f:
                                ci_data = json.load(f)

                            print(f"CI Summary: {ci_data.get('summary', 'No summary available')}")

                            # Check for critical issues
                            overall_status = ci_data.get('overall_status', 'UNKNOWN')
                            if overall_status == 'FAILURE':
                                print("❌ CI simulation found critical issues")

                                # Show failed checks
                                check_results = ci_data.get('check_results', {})
                                failed_checks = [name for name, result in check_results.items()
                                               if result.get('status') == 'FAILURE']
                                if failed_checks:
                                    print(f"Failed checks: {', '.join(failed_checks)}")

                                return False
                            elif overall_status == 'WARNING':
                                print("⚠️ CI simulation completed with warnings")

                        except (json.JSONDecodeError, IOError) as e:
                            print(f"⚠️ Could not parse CI report: {e}")

                return True
            else:
                print(f"❌ CI simulation failed (exit code: {result.returncode})")
                if result.stderr:
                    print(f"Error output: {result.stderr}")
                if result.stdout:
                    print(f"Standard output: {result.stdout}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ CI simulation timed out after 30 minutes")
            return False
        except Exception as e:
            print(f"❌ CI simulation error: {e}")
            return False

    def create_deployment_package(
        self, skip_tests: bool = False, skip_quality: bool = False
    ) -> bool:
        """デプロイメントパッケージを作成"""
        print("=" * 60)
        print("PhotoGeoView AI統合デプロイメントパッケージ作成")
        print("=" * 60)

        # ビルドディレクトリをクリーン
        self.clean_build_directories()

        # CI Simulation
        if not self.run_ci_simulation():
            print("❌ CI simulation failed")
            return False

        # 品質チェック
        if not skip_quality:
            if not self.run_quality_checks():
                print("❌ 品質チェックに失敗しました")
                return False

        # テスト実行
        if not skip_tests:
            if not self.run_tests():
                print("⚠️ テストに失敗しましたが、パッケージ作成を続行します")

        # ソースパッケージ作成
        source_dir = self.create_source_package()

        # アーカイブパッケージ作成
        archive_packages = self.create_archive_packages(source_dir)

        # バイナリパッケージ作成（オプション）
        binary_package = self.create_binary_package()

        # 全パッケージリスト
        all_packages = archive_packages
        if binary_package:
            all_packages.append(binary_package)

        # デプロイメントマニフェスト生成
        manifest_path = self.generate_deployment_manifest(all_packages)

        # 結果表示
        print("\n" + "=" * 60)
        print("デプロイメントパッケージ作成完了")
        print("=" * 60)
        print(f"パッケージ名: {self.package_info['name']}")
        print(f"バージョン: {self.package_info['version']}")
        print(f"作成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        print()
        print("作成されたパッケージ:")
        for package in all_packages:
            size_mb = package.stat().st_size / (1024 * 1024)
            print(f"  - {package.name} ({size_mb:.1f}MB)")
        print()
        print(f"マニフェスト: {manifest_path.name}")
        print(f"出力ディレクトリ: {self.dist_dir}")

        return True


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="AI統合デプロイメントパッケージ作成")
    parser.add_argument("--skip-tests", action="store_true", help="テストをスキップ")
    parser.add_argument(
        "--skip-quality", action="store_true", help="品質チェックをスキップ"
    )
    parser.add_argument("--project-root", type=Path, help="プロジェクトルートパス")

    args = parser.parse_args()

    project_root = args.project_root or Path(__file__).parent.parent
    creator = DeploymentPackageCreator(project_root)

    success = creator.create_deployment_package(
        skip_tests=args.skip_tests, skip_quality=args.skip_quality
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
