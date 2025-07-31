#!/usr/bin/env python3
"""
PhotoGeoView CI Runner

プロジェクトルートから簡単にCI実行できるスクリプト
"""

import sys
from pathlib import Path

# tools/ci/simple_ci.py を実行
ci_script = Path(__file__).parent / "tools" / "ci" / "simple_ci.py"

if not ci_script.exists():
    print("❌ CI スクリプトが見つかりません:", ci_script)
    sys.exit(1)

# 引数をそのまま渡して実行
import subprocess
result = subprocess.run([sys.executable, str(ci_script)] + sys.argv[1:])
sys.exit(result.returncode)
