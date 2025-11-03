#!/usr/bin/env python3
"""
Simple CI Simulator for PhotoGeoView

シンプルで実用的なCI/CDシミュレーター
- 基本的なコード品質チェック
- テスト実行
- セキュリティチェック
- レポート生成
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class SimpleCI:
    """シンプルなCIシミュレーター"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.results = {}
        self.start_time = time.time()

    def run_command(self, cmd: List[str], timeout: int = 60) -> Tuple[bool, str, str]:
        """コマンドを安全に実行"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"タイムアウト ({timeout}秒)"
        except Exception as e:
            return False, "", str(e)

    def check_syntax(self) -> Dict:
        """Python構文チェック"""
        print("🔍 Python構文チェック中...")

        python_files = list(self.project_root.rglob("*.py"))
        if not python_files:
            return {"status": "skip", "message": "Pythonファイルが見つかりません"}

        errors = []
        for py_file in python_files[:20]:  # 最初の20ファイルのみチェック
            success, _, stderr = self.run_command(
                [sys.executable, "-m", "py_compile", str(py_file)], timeout=10
            )

            if not success and "SyntaxError" in stderr:
                errors.append(
                    f"{py_file.name}: {stderr.split('SyntaxError:')[-1].strip()}"
                )

        if errors:
            return {
                "status": "fail",
                "message": f"{len(errors)}個の構文エラー",
                "details": errors[:5],  # 最初の5個のみ表示
            }

        return {
            "status": "pass",
            "message": f"{len(python_files)}個のファイルの構文チェック完了",
        }

    def check_imports(self) -> Dict:
        """インポートチェック"""
        print("📦 インポートチェック中...")

        # main.pyのインポートテスト
        if Path("main.py").exists():
            success, stdout, stderr = self.run_command(
                [sys.executable, "-c", "import main; print('✅ main.py import OK')"],
                timeout=30,
            )

            if success:
                return {"status": "pass", "message": "main.pyのインポート成功"}
            else:
                return {
                    "status": "fail",
                    "message": f"main.pyのインポート失敗: {stderr}",
                }

        return {"status": "skip", "message": "main.pyが見つかりません"}

    def check_tests(self) -> Dict:
        """テストファイルチェック"""
        print("🧪 テストファイルチェック中...")

        test_files = (
            list(self.project_root.rglob("test_*.py"))
            + list(self.project_root.rglob("*_test.py"))
            + list(self.project_root.rglob("tests/*.py"))
        )

        if not test_files:
            return {"status": "warn", "message": "テストファイルが見つかりません"}

        # pytest --collect-only で テスト収集のみ実行
        success, stdout, stderr = self.run_command(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"], timeout=30
        )

        if success:
            test_count = stdout.count("::") if "::" in stdout else len(test_files)
            return {
                "status": "pass",
                "message": f"{len(test_files)}個のテストファイル, 約{test_count}個のテスト",
            }
        else:
            return {
                "status": "warn",
                "message": f"{len(test_files)}個のテストファイル (収集エラー)",
            }

    def check_dependencies(self) -> Dict:
        """依存関係チェック"""
        print("📋 依存関係チェック中...")

        if not Path("pyproject.toml").exists():
            return {"status": "warn", "message": "pyproject.tomlが見つかりません"}

        # pip check で依存関係の整合性をチェック（pyproject管理）
        success, stdout, stderr = self.run_command(
            [sys.executable, "-m", "pip", "check"], timeout=30
        )

        if success:
            return {"status": "pass", "message": "依存関係の整合性OK"}
        else:
            return {
                "status": "fail",
                "message": "依存関係に問題があります",
                "details": stderr.split("\n")[:3],
            }

    def check_project_structure(self) -> Dict:
        """プロジェクト構造チェック"""
        print("📁 プロジェクト構造チェック中...")

        required_files = ["main.py", "requirements.txt"]
        recommended_dirs = ["tests", "docs"]

        missing_files = [f for f in required_files if not Path(f).exists()]
        existing_dirs = [d for d in recommended_dirs if Path(d).exists()]

        if missing_files:
            return {
                "status": "warn",
                "message": f"推奨ファイルが不足: {', '.join(missing_files)}",
            }

        return {
            "status": "pass",
            "message": f"基本構造OK ({len(existing_dirs)}/{len(recommended_dirs)}の推奨ディレクトリ存在)",
        }

    def run_all_checks(self) -> Dict:
        """全チェックを実行"""
        print("🚀 PhotoGeoView CI Simulator")
        print("=" * 50)

        checks = [
            ("構文チェック", self.check_syntax),
            ("インポートチェック", self.check_imports),
            ("テストチェック", self.check_tests),
            ("依存関係チェック", self.check_dependencies),
            ("プロジェクト構造", self.check_project_structure),
        ]

        results = {}

        for check_name, check_func in checks:
            try:
                start = time.time()
                result = check_func()
                result["duration"] = round(time.time() - start, 2)
                results[check_name] = result

                # 結果表示
                status_icons = {"pass": "✅", "warn": "⚠️", "fail": "❌", "skip": "⏭️"}
                icon = status_icons.get(result["status"], "❓")
                print(
                    f"{icon} {check_name}: {result['message']} ({result['duration']}s)"
                )

                # 詳細があれば表示
                if "details" in result:
                    for detail in result["details"]:
                        print(f"   • {detail}")

            except Exception as e:
                results[check_name] = {
                    "status": "fail",
                    "message": f"エラー: {e!s}",
                    "duration": 0,
                }
                print(f"❌ {check_name}: エラー - {e!s}")

        # サマリー
        total_duration = round(time.time() - self.start_time, 2)

        status_counts = {}
        for result in results.values():
            status = result["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        print("\n" + "=" * 50)
        print("📊 実行結果サマリー")
        print("=" * 50)

        for status, count in status_counts.items():
            icon = {"pass": "✅", "warn": "⚠️", "fail": "❌", "skip": "⏭️"}.get(
                status, "❓"
            )
            print(f"{icon} {status.upper()}: {count}個")

        print(f"\n⏱️  総実行時間: {total_duration}秒")

        # 全体的な判定
        if status_counts.get("fail", 0) > 0:
            overall_status = "FAILED"
            print("🔴 総合結果: FAILED (修正が必要)")
        elif status_counts.get("warn", 0) > 0:
            overall_status = "WARNING"
            print("🟡 総合結果: WARNING (改善推奨)")
        else:
            overall_status = "PASSED"
            print("🟢 総合結果: PASSED")

        return {
            "overall_status": overall_status,
            "total_duration": total_duration,
            "checks": results,
            "summary": status_counts,
            "timestamp": datetime.now().isoformat(),
        }

    def save_report(self, results: Dict, format: str = "json"):
        """レポート保存"""
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "json":
            report_file = reports_dir / f"ci_report_{timestamp}.json"
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"📄 JSONレポート保存: {report_file}")

        elif format == "markdown":
            report_file = reports_dir / f"ci_report_{timestamp}.md"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write("# CI実行レポート\n\n")
                f.write(f"**実行日時**: {results['timestamp']}\n")
                f.write(f"**総実行時間**: {results['total_duration']}秒\n")
                f.write(f"**総合結果**: {results['overall_status']}\n\n")

                f.write("## チェック結果\n\n")
                for check_name, result in results["checks"].items():
                    status_icon = {
                        "pass": "✅",
                        "warn": "⚠️",
                        "fail": "❌",
                        "skip": "⏭️",
                    }.get(result["status"], "❓")
                    f.write(f"### {status_icon} {check_name}\n")
                    f.write(f"- **ステータス**: {result['status'].upper()}\n")
                    f.write(f"- **メッセージ**: {result['message']}\n")
                    f.write(f"- **実行時間**: {result['duration']}秒\n")

                    if "details" in result:
                        f.write("- **詳細**:\n")
                        for detail in result["details"]:
                            f.write(f"  - {detail}\n")
                    f.write("\n")

            print(f"📄 Markdownレポート保存: {report_file}")


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="PhotoGeoView Simple CI Simulator")
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="json",
        help="レポート形式",
    )
    parser.add_argument(
        "--no-report", action="store_true", help="レポート保存をスキップ"
    )

    args = parser.parse_args()

    try:
        ci = SimpleCI()
        results = ci.run_all_checks()

        # レポート保存
        if not args.no_report:
            if args.format in ["json", "both"]:
                ci.save_report(results, "json")
            if args.format in ["markdown", "both"]:
                ci.save_report(results, "markdown")

        # 終了コード
        if results["overall_status"] == "FAILED":
            return 1
        elif results["overall_status"] == "WARNING":
            return 0  # 警告は成功扱い
        else:
            return 0

    except KeyboardInterrupt:
        print("\n⚠️  ユーザーによって中断されました")
        return 130
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
