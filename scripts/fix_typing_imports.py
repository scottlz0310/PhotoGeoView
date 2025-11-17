#!/usr/bin/env python3
"""
typing.Dict/List/Tupleをimport文から削除し、組み込み型に置換するスクリプト
"""

import re
from pathlib import Path


def fix_typing_imports(file_path: Path) -> bool:
    """Fix typing imports in a Python file."""
    content = file_path.read_text(encoding="utf-8")
    original_content = content

    # パターン1: from typing import ... の行を修正
    # Dict, List, Tupleを削除
    def replace_typing_import(match):
        imports = match.group(1)
        # Dict, List, Tupleを除去
        items = [item.strip() for item in imports.split(",")]
        items = [item for item in items if item not in ["Dict", "List", "Tuple"]]

        if not items:
            # 他のimportがない場合は行ごと削除
            return ""
        else:
            # 残りのimportを保持
            return f"from typing import {', '.join(items)}"

    # from typing import ... の行を処理
    content = re.sub(r"^from typing import ([^\n]+)$", replace_typing_import, content, flags=re.MULTILINE)

    # 空行が連続しないように調整
    content = re.sub(r"\n\n\n+", "\n\n", content)

    if content != original_content:
        file_path.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    src_dir = Path("src")
    fixed_count = 0

    for py_file in src_dir.rglob("*.py"):
        if fix_typing_imports(py_file):
            print(f"Fixed: {py_file}")
            fixed_count += 1

    print(f"\nTotal files fixed: {fixed_count}")


if __name__ == "__main__":
    main()
