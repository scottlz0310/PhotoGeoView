# トラブルシューティング

## Sharp モジュールエラー

### 症状

アプリ起動時に以下のエラーが表示される：

```
Error: Could not load the "sharp" module using the win32-x64 runtime
```

### 原因

アンインストーラーが古いファイルを削除せずに残しているため、新しいバージョンをインストールしても古い sharp モジュールが使用されます。

### 解決方法

#### 方法 1: クリーンアップスクリプトを使用（推奨）

1. PowerShell を開く
2. プロジェクトディレクトリに移動
3. クリーンアップスクリプトを実行：

```powershell
.\scripts\cleanup-photogeoview.ps1
```

ユーザーデータ（設定、キャッシュ）を保持したい場合：

```powershell
.\scripts\cleanup-photogeoview.ps1 -KeepUserData
```

4. 新しいインストーラーを実行

#### 方法 2: 手動でクリーンアップ

1. PhotoGeoView を終了
2. PowerShell で以下のコマンドを実行：

```powershell
# プロセスを停止
Get-Process PhotoGeoView -ErrorAction SilentlyContinue | Stop-Process -Force

# アプリケーションファイルを削除
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Programs\photogeoview"

# ユーザーデータを削除
Remove-Item -Recurse -Force "$env:APPDATA\PhotoGeoView"

# アップデーターキャッシュを削除
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\photogeoview-updater"
```

3. 新しいインストーラーを実行

## ビルドエラー

### WinCodeSign シンボリックリンクエラー

#### 症状

ビルド時に以下のエラーが表示される：

```
ERROR: Cannot create symbolic link : クライアントは要求された特権を保有していません。
```

#### 解決方法

**オプション 1: 管理者権限で実行**

1. PowerShell を**管理者として実行**
2. プロジェクトディレクトリに移動
3. ビルドコマンドを実行：

```powershell
pnpm package -- --win --publish never
```

**オプション 2: Windows 開発者モードを有効化**

1. **設定** → **プライバシーとセキュリティ** → **開発者向け**
2. **開発者モード** をオンにする
3. 通常の PowerShell でビルド可能

## 依存関係の問題

### Sharp 関連パッケージが不足

#### 症状

ビルドは成功するが、インストール後に sharp エラーが発生

#### 解決方法

以下のパッケージが `package.json` に含まれていることを確認：

```json
{
  "dependencies": {
    "sharp": "^0.34.5"
  },
  "optionalDependencies": {
    "@img/sharp-libvips-win32-x64": "^1.2.4"
  }
}
```

不足している場合は追加：

```bash
pnpm add --save-optional @img/sharp-libvips-win32-x64
```

## 参考情報

- [Sharp クロスプラットフォームインストール](https://sharp.pixelplumbing.com/install#cross-platform)
- [Electron Builder Windows ビルド](https://www.electron.build/configuration/win)
- [Windows シンボリックリンク](https://docs.microsoft.com/en-us/windows/security/threat-protection/security-policy-settings/create-symbolic-links)
