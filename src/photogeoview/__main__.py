"""
PhotoGeoView CLI エントリーポイント

python -m photogeoview で実行可能
"""

import sys
import traceback
from pathlib import Path


def main() -> int:
    """メインアプリケーション起動"""
    # プロジェクトルートからmain.pyをインポート
    # 段階的移行のため、既存のmain.pyを再利用
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    try:
        # 既存のmainモジュールを使用(段階的移行)
        import main as main_module

        # main.main()はsys.exit()を呼ぶので、ここで直接実行
        main_module.main()
        return 0  # 通常はここには到達しない
    except (ImportError, RuntimeError) as e:
        print(f"❌ アプリケーション起動エラー: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
