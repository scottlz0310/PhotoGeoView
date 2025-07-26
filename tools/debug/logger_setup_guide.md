# デバッグ作業用ロガー設定ガイド

## 概要
デバッグ作業時に使用するロガーの設定方法と使用例を説明します。

## ロガーの基本設定

```python
import logging
import sys
from pathlib import Path

# ログ設定の初期化
def setup_debug_logger(name: str = "debug") -> logging.Logger:
    """
    デバッグ用ロガーを設定する

    Args:
        name: ロガー名

    Returns:
        設定済みのロガーインスタンス
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # ファイルハンドラー
    log_file = Path("logs") / f"{name}.log"
    log_file.parent.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # フォーマッター（日本語対応）
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
```

## 使用例

### 基本的なデバッグ出力
```python
# ✅ 正しい方法
logger = setup_debug_logger("my_debug")
logger.debug("変数の値: %s", variable_value)
logger.info("処理開始: %s", process_name)
logger.warning("警告: %s", warning_message)
logger.error("エラー発生: %s", error_message)

# ❌ 避けるべき方法
print("デバッグ情報:", variable_value)  # 使用禁止
```

### 例外処理でのロガー使用
```python
try:
    # 何らかの処理
    result = some_function()
    logger.debug("処理結果: %s", result)
except Exception as e:
    logger.error("例外が発生しました: %s", str(e), exc_info=True)
```

### パフォーマンス測定
```python
import time

start_time = time.time()
# 処理実行
end_time = time.time()
logger.debug("処理時間: %.3f秒", end_time - start_time)
```

## 注意事項

1. **必ずロガーを使用**: print()文は使用しない
2. **適切なログレベル**: DEBUG < INFO < WARNING < ERROR < CRITICAL
3. **日本語メッセージ**: すべてのログメッセージは日本語で記述
4. **構造化ログ**: 変数は%sを使用してフォーマット
5. **ファイル出力**: 重要なデバッグ情報はファイルにも出力

## デバッグ終了時のクリーンアップ

```python
def cleanup_debug_resources():
    """デバッグリソースのクリーンアップ"""
    # ログハンドラーのクローズ
    for handler in logger.handlers:
        handler.close()
        logger.removeHandler(handler)

    logger.info("デバッグセッション終了")
```
