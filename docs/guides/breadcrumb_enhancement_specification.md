# Breadcrumb Address Bar Enhancement Specification

## 概要

`breadcrumb-addressbar`ライブラリの機能強化により、ブレッドクラムの任意のセグメントボタンをクリックした際にフォルダ選択ポップアップを表示できるようになります。これにより、ユーザーはより直感的にフォルダ階層をナビゲートできるようになります。

## 現在の動作

- 最下層（現在のフォルダ）のボタンのみがフォルダ選択ポップアップを表示
- 親フォルダのボタンは直接ナビゲーションのみ

## 提案する動作

- **任意のセグメントボタン**をクリックした際にフォルダ選択ポップアップを表示
- 親フォルダへの直接ナビゲーション機能は維持
- ポップアップの位置をクリックされたボタンに基づいて調整

## 技術仕様

### 新しい設定オプション

#### 1. `setShowPopupForAllButtons(enabled: bool)`
- **目的**: どのボタンでもポップアップを表示するかどうかを制御
- **デフォルト値**: `True`
- **型**: `bool`

#### 2. `getShowPopupForAllButtons() -> bool`
- **目的**: 現在のポップアップ表示設定を取得
- **戻り値**: 設定値

#### 3. `setPopupPositionOffset(offset: tuple[int, int])`
- **目的**: ポップアップの位置オフセットを設定
- **デフォルト値**: `(0, 2)`
- **型**: `tuple[int, int]` (x, y オフセット)

#### 4. `getPopupPositionOffset() -> tuple[int, int]`
- **目的**: 現在のポップアップ位置オフセットを取得
- **戻り値**: オフセット値

### 内部実装の変更

#### 1. 新しい内部変数
```python
# 新しい設定オプション
self._show_popup_for_all_buttons = True  # どのボタンでもポップアップを表示
self._popup_position_offset = (0, 2)  # ポップアップの位置オフセット
```

#### 2. `_on_item_clicked_with_info`メソッドの修正
```python
if path:
    # 設定に応じてポップアップを表示
    if self._show_popup_for_all_buttons:
        # どのボタンでもポップアップを表示
        self._logger.debug("Showing folder popup for clicked button")
        self._show_folder_popup(path)
    else:
        # 従来の動作: 最下層ボタン（現在のフォルダ）の場合はポップアップを表示
        if is_current:
            self._logger.debug("Showing folder popup for current path")
            self._show_folder_popup(path)
        else:
            self._logger.debug(f"Navigating to path: {path}")
            self.setPath(path)
```

#### 3. `_show_folder_popup`メソッドの修正
```python
# クリックされたボタンを特定
clicked_item = None
for item in self._breadcrumb_items:
    if item.path == path:
        clicked_item = item
        break

# ボタンが見つからない場合は最後のボタンを使用
if not clicked_item and self._breadcrumb_items:
    clicked_item = self._breadcrumb_items[-1]

if clicked_item:
    popup = FolderSelectionPopup(self)
    popup.folderSelected.connect(self._on_folder_selected)

    # クリックされたボタンの下にポップアップを表示
    pos = clicked_item.mapToGlobal(clicked_item.rect().bottomLeft())
    # オフセットを適用
    pos.setX(pos.x() + self._popup_position_offset[0])
    pos.setY(pos.y() + self._popup_position_offset[1])
    popup.showForPath(path, (pos.x(), pos.y()))
```

## 使用方法

### 基本的な使用例
```python
from breadcrumb_addressbar import BreadcrumbAddressBar

# ウィジェットの作成
breadcrumb = BreadcrumbAddressBar()

# 強化されたポップアップ機能を有効化（デフォルトで有効）
breadcrumb.setShowPopupForAllButtons(True)

# ポップアップ位置のオフセットを設定
breadcrumb.setPopupPositionOffset((0, 2))

# パスの設定
breadcrumb.setPath("/path/to/current/folder")
```

### 従来の動作に戻す場合
```python
# 従来の動作（最下層ボタンのみポップアップ表示）
breadcrumb.setShowPopupForAllButtons(False)
```

## 後方互換性

- **完全な後方互換性**を保証
- 既存のコードは変更なしで動作
- デフォルトで新しい機能が有効（`True`）
- 必要に応じて従来の動作に戻すことが可能

## テストケース

### 1. 基本機能テスト
- [ ] 任意のセグメントボタンをクリックしてポップアップが表示される
- [ ] ポップアップからフォルダを選択して正しくナビゲートされる
- [ ] 親フォルダへの直接ナビゲーションが正常に動作する

### 2. 設定テスト
- [ ] `setShowPopupForAllButtons(False)`で従来の動作に戻る
- [ ] `setShowPopupForAllButtons(True)`で新しい動作になる
- [ ] ポップアップ位置オフセットが正しく適用される

### 3. エッジケーステスト
- [ ] 存在しないパスの場合の動作
- [ ] 空のパスの場合の動作
- [ ] 非常に長いパス名の場合の動作

## パフォーマンスへの影響

- **最小限の影響**: 追加される処理は軽量
- **メモリ使用量**: 増加なし
- **CPU使用量**: 無視できる程度の増加

## セキュリティ考慮事項

- 既存のセキュリティチェックを維持
- パス検証は既存のロジックを使用
- 新しいセキュリティリスクはなし

## ドキュメント更新

### README.md への追加
```markdown
## Enhanced Popup Support

The breadcrumb address bar now supports showing folder selection popups for any segment button, not just the deepest one. This provides a more intuitive navigation experience.

### Configuration

- `setShowPopupForAllButtons(enabled: bool)`: Enable/disable popup for all buttons
- `getShowPopupForAllButtons() -> bool`: Get current popup setting
- `setPopupPositionOffset(offset: tuple[int, int])`: Set popup position offset
- `getPopupPositionOffset() -> tuple[int, int]`: Get current offset

### Example

```python
breadcrumb = BreadcrumbAddressBar()
breadcrumb.setShowPopupForAllButtons(True)  # Enable enhanced popup
breadcrumb.setPopupPositionOffset((0, 2))   # Set position offset
```
```

## リリース計画

### バージョン 0.3.0
- 新機能の追加
- 完全な後方互換性
- ドキュメント更新
- テストケース追加

### 移行ガイド
- 既存ユーザーは自動的に新機能を利用可能
- 従来の動作が必要な場合は設定で無効化可能

## フィードバックと改善

- ユーザーフィードバックに基づく調整
- 必要に応じて追加の設定オプションを検討
- パフォーマンス最適化の継続

---

**作成日**: 2024年8月4日
**作成者**: PhotoGeoView開発チーム
**バージョン**: 1.0
