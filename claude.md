# PhotoGeoView Tauri版 - AI開発ガイドライン

**作成日**: 2025-12-29
**対象**: Claude Codeおよび他のAI支援ツール
**言語**: 日本語

このドキュメントは、PhotoGeoView Tauri版の開発におけるAIの振る舞いを規定するルールファイルです。AI支援開発を行う際は、必ずこのガイドラインに従ってください。

---

## 目次

1. [基本方針](#1-基本方針)
2. [コミュニケーション](#2-コミュニケーション)
3. [コーディング規約](#3-コーディング規約)
4. [実装ガイドライン](#4-実装ガイドライン)
5. [禁止事項](#5-禁止事項)
6. [タスク管理](#6-タスク管理)
7. [品質基準](#7-品質基準)
8. [ドキュメント管理](#8-ドキュメント管理)

---

## 1. 基本方針

### 1.1 プロジェクトの性質

このプロジェクトは**実験的・学習目的**のプロジェトです：

- **失敗が許容される**: C#/.NET版が本命実装として存在するため、リスクを取った実装が可能
- **技術的挑戦を歓迎**: 新しい技術やアプローチを積極的に試すことを推奨
- **学習を優先**: 完璧さよりも学びと成長を重視

### 1.2 開発スタイル

- **段階的実装**: 一度に全てを実装せず、小さく動くものから始める
- **実用最小限の機能 (MVP) 優先**: 完璧な機能よりも動作する基本機能を優先
- **リファクタリング歓迎**: 初期実装が汚くても、後で改善する前提で進める
- **ドキュメント重視**: コードと同じくらいドキュメントを大切にする

### 1.3 AI支援開発の原則

AIは以下の役割を担います：

1. **実装の支援**: コード生成、バグ修正、リファクタリング
2. **設計の提案**: アーキテクチャ、データ構造、API設計の提案
3. **学習のサポート**: Rust、Tauriの学習をサポート
4. **品質の向上**: テスト、ドキュメント、コードレビューの支援

ただし、**最終的な意思決定は人間が行う**ことを原則とします。

---

## 2. コミュニケーション

### 2.1 言語

- **日本語を使用**: すべてのコミュニケーションは日本語で行う
- **コード内のコメント**: 日本語で記述（複雑なロジックのみ）
- **Gitコミットメッセージ**: 日本語または英語（プロジェクトの慣例に従う）

### 2.2 説明の明確さ

- **専門用語の使用**: 必要に応じて専門用語を使用するが、初出時は説明を添える
- **コード例の提供**: 抽象的な説明だけでなく、具体的なコード例を示す
- **理由の説明**: 「なぜそうするのか」を必ず説明する

### 2.3 質問と確認

- **不明点は質問する**: 曖昧な指示や不明な要求がある場合は、実装前に必ず質問する
- **前提条件の確認**: 重要な実装を行う前に、前提条件や期待される動作を確認する
- **複数の選択肢を提示**: 実装方法が複数ある場合は、選択肢を提示して意見を求める

---

## 3. コーディング規約

### 3.1 TypeScript / React

#### 命名規則

- **コンポーネント**: PascalCase (`PhotoList`, `MapView`)
- **関数・変数**: camelCase (`selectPhoto`, `photoData`)
- **定数**: UPPER_SNAKE_CASE (`MAX_PHOTO_COUNT`)
- **型**: PascalCase (`PhotoData`, `AppSettings`)
- **インターフェース**: PascalCaseで、接頭辞`I`は付けない

#### ファイル構成

- **コンポーネントファイル**: `ComponentName.tsx`
- **フックファイル**: `useCustomHook.ts`
- **型定義ファイル**: `types.ts` または `ComponentName.types.ts`
- **テストファイル**: `ComponentName.test.tsx`

#### コーディングスタイル

- **関数コンポーネント**: アロー関数で定義
  ```typescript
  export const PhotoList: React.FC = () => {
    // ...
  };
  ```
- **Hooksの順序**: useState → useEffect → カスタムフック → その他
- **propsの型定義**: インターフェースまたはtypeで明示的に定義
- **早期リターン**: ガード節を使って早期リターン

#### 禁止事項

- ❌ `any`型の使用（やむを得ない場合のみ`unknown`を使用）
- ❌ `console.log`の残置（デバッグ後は削除）
- ❌ 未使用のインポート・変数
- ❌ マジックナンバー（定数として定義）

### 3.2 Rust

#### 命名規則

- **構造体**: PascalCase (`PhotoData`, `ExifInfo`)
- **関数・変数**: snake_case (`read_exif`, `photo_path`)
- **定数**: UPPER_SNAKE_CASE (`MAX_FILE_SIZE`)
- **列挙型**: PascalCase (`ImageFormat::Jpeg`)
- **モジュール**: snake_case (`commands::exif`)

#### ファイル構成

- **モジュールファイル**: `module_name.rs`
- **モジュールディレクトリ**: `module_name/mod.rs`
- **テストファイル**: 同じファイル内の`#[cfg(test)]`モジュール

#### コーディングスタイル

- **エラーハンドリング**: `Result<T, E>`を使用、`unwrap()`は避ける
  ```rust
  fn read_exif(path: &str) -> Result<ExifData, ExifError> {
      // ...
  }
  ```
- **所有権**: 必要最小限のclone、可能な限り借用を使用
- **ライフタイム**: 必要な場合のみ明示的に指定
- **マクロの使用**: 控えめに（デバッグ用`dbg!`は削除）

#### 禁止事項

- ❌ `unwrap()`の多用（開発中は許容、本番コードでは`?`演算子を使用）
- ❌ `panic!`の使用（Tauri Commandでは必ずResultを返す）
- ❌ グローバルな可変状態（mutexやatomicを使用）
- ❌ unsafeブロック（どうしても必要な場合はコメントで理由を説明）

### 3.3 共通規約

#### インデント・フォーマット

- **TypeScript/React**: 2スペース（Biome設定に従う）
- **Rust**: 4スペース（rustfmt設定に従う）
- **自動フォーマット**: 保存時に自動実行（Biome, rustfmt）

#### コメント

- **複雑なロジックのみ**: 自明なコードにはコメント不要
- **TODOコメント**: `// TODO: 説明` 形式で記述
- **日本語**: コメントは日本語で記述

---

## 4. 実装ガイドライン

### 4.1 新機能追加の流れ

1. **tasks.mdの確認**: 実装するタスクがリストにあるか確認
2. **設計の検討**: 必要に応じて設計を提案・議論
3. **型定義の作成**: TypeScriptの型、Rustの構造体を先に定義
4. **バックエンドの実装**: Rust側のTauri Commandを実装
5. **フロントエンドの実装**: React側のUIと状態管理を実装
6. **テストの追加**: ユニットテスト、必要に応じてE2Eテスト
7. **tasks.mdの更新**: 完了したタスクにチェック

### 4.2 既存コードの修正

- **影響範囲の確認**: 変更が他の部分に影響しないか確認
- **テストの実行**: 修正後、関連するテストを実行
- **リファクタリングの提案**: 改善の余地があれば提案

### 4.3 Tauri Commandの実装パターン

```rust
// src-tauri/src/commands/example.rs

use serde::{Deserialize, Serialize};
use tauri::command;

#[derive(Debug, Serialize, Deserialize)]
pub struct InputData {
    pub value: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OutputData {
    pub result: String,
}

#[command]
pub async fn example_command(input: InputData) -> Result<OutputData, String> {
    // 実装
    match process(&input.value) {
        Ok(result) => Ok(OutputData { result }),
        Err(e) => Err(format!("エラー: {}", e)),
    }
}

fn process(value: &str) -> Result<String, Box<dyn std::error::Error>> {
    // ビジネスロジック
    Ok(value.to_uppercase())
}
```

フロントエンド側の呼び出し：

```typescript
import { invoke } from '@tauri-apps/api/tauri';

interface InputData {
  value: string;
}

interface OutputData {
  result: string;
}

async function callCommand(value: string): Promise<string> {
  try {
    const output = await invoke<OutputData>('example_command', {
      input: { value } as InputData,
    });
    return output.result;
  } catch (error) {
    console.error('Command failed:', error);
    throw error;
  }
}
```

### 4.4 エラーハンドリングパターン

#### Rust側

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ExifError {
    #[error("ファイルが見つかりません: {0}")]
    FileNotFound(String),

    #[error("EXIF情報の読み取りに失敗しました: {0}")]
    ReadError(String),

    #[error("GPS情報が存在しません")]
    NoGpsData,
}

#[command]
pub async fn read_exif(path: String) -> Result<ExifData, String> {
    read_exif_internal(&path).map_err(|e| e.to_string())
}

fn read_exif_internal(path: &str) -> Result<ExifData, ExifError> {
    // ...
}
```

#### TypeScript側

```typescript
import { toast } from 'sonner';

try {
  const data = await invoke<ExifData>('read_exif', { path });
  return data;
} catch (error) {
  toast.error('EXIF情報の読み取りに失敗しました', {
    description: String(error),
  });
  throw error;
}
```

---

## 5. 禁止事項

### 5.1 絶対にやってはいけないこと

- ❌ **未テストのコードをmainブランチにマージ**
  - 理由: プロジェクトの安定性を損なう
  - 対策: 必ずテストを実行してからマージ

- ❌ **セキュリティリスクのある実装**
  - 例: ユーザー入力を直接SQLやシェルコマンドに渡す
  - 対策: 必ず入力検証・サニタイズを行う

- ❌ **過度な最適化**
  - 理由: 読みやすさを損ない、バグの温床になる
  - 対策: まず動くコードを書き、必要に応じて最適化

- ❌ **ドキュメント未更新のまま大きな変更**
  - 理由: 他の開発者（将来の自分）が理解できなくなる
  - 対策: コードと同時にドキュメントを更新

### 5.2 避けるべきパターン

- ⚠️ **神クラス・神関数**: 1つのファイル/関数が500行を超える場合は分割を検討
- ⚠️ **深いネスト**: if文のネストが3階層を超える場合は早期リターンを検討
- ⚠️ **グローバル状態の乱用**: 必要最小限に留める
- ⚠️ **テストのないバグ修正**: バグ修正時は必ず再現テストを追加

---

## 6. タスク管理

### 6.1 tasks.mdの更新ルール

#### タスク開始時

```markdown
- [ ] タスク名 <!-- 2025-12-30開始 -->
```

#### タスク完了時

```markdown
- [x] タスク名 <!-- 2025-12-30開始 → 2025-12-31完了 -->
```

#### 新しいタスクの追加

- 実装中に新たなタスクが発覚した場合、適切なPhaseに追加
- 優先度が高い場合は、セクション上部に追加

### 6.2 進捗報告

週次で以下を確認：

- 完了したタスクの数
- 残りタスクの見積もり
- ブロッカーの有無

### 6.3 Git運用

#### ブランチ戦略

- `main`: 本番リリース可能な状態
- `tauri-rewrite`: Tauri移行作業ブランチ（現在のブランチ）
- `feature/*`: 新機能開発用（必要に応じて）

#### コミットメッセージ

```
種別: 簡潔な説明

詳細な説明（必要に応じて）
```

種別の例：
- `feat`: 新機能
- `fix`: バグ修正
- `refactor`: リファクタリング
- `test`: テスト追加
- `docs`: ドキュメント更新
- `chore`: ビルド設定、依存関係更新等

例：
```
feat: EXIF読み取り機能を実装

kamadak-exifクレートを使用してGPS情報を抽出
tasks.md Phase 2.2 を完了
```

---

## 7. 品質基準

### 7.1 テストカバレッジ

- **フロントエンド**: 70%以上を目標
- **バックエンド**: 80%以上を目標
- **クリティカルパス**: 100%

### 7.2 パフォーマンス

- **100枚の写真読み込み**: 3秒以内
- **1000枚の写真読み込み**: 10秒以内
- **サムネイル生成**: 100ms以内/枚
- **地図レンダリング**: 60fps維持

ベンチマークが基準を満たさない場合は、最適化を検討。

### 7.3 コード品質（最重要：型安全性）

**型安全性を何より重視** - このプロジェクトでは型安全性が最優先事項です。

#### TypeScript厳格ルール

- ❌ **`any`型の使用は絶対禁止**
  - 理由: 型安全性を完全に破壊する
  - 例外: 外部ライブラリの型定義が不完全な場合のみ`unknown`を使用し、型ガードで絞り込む
  ```typescript
  // ❌ 禁止
  const data: any = response.data;

  // ✅ 正しい
  const data: unknown = response.data;
  if (isPhotoData(data)) {
    // 型ガードで型を確定
    const photo: PhotoData = data;
  }
  ```

- ❌ **`as`型アサーションの多用禁止**
  - 理由: コンパイラの型チェックを回避してしまう
  - 許容: 型ガードでチェック済みの場合のみ
  ```typescript
  // ❌ 禁止（チェックなしのアサーション）
  const photo = data as PhotoData;

  // ✅ 正しい（型ガードを使用）
  function isPhotoData(data: unknown): data is PhotoData {
    return typeof data === 'object' && data !== null && 'path' in data;
  }
  if (isPhotoData(data)) {
    const photo = data; // PhotoData型に自動推論
  }
  ```

- ❌ **`@ts-ignore`、`@ts-expect-error`の使用禁止**
  - 理由: 型エラーを隠蔽するだけで根本解決にならない
  - 例外: 絶対に必要な場合は、コメントで詳細な理由を説明

- ✅ **必須設定（tsconfig.json）**
  ```json
  {
    "compilerOptions": {
      "strict": true,
      "noImplicitAny": true,
      "strictNullChecks": true,
      "strictFunctionTypes": true,
      "strictBindCallApply": true,
      "strictPropertyInitialization": true,
      "noImplicitThis": true,
      "alwaysStrict": true,
      "noUnusedLocals": true,
      "noUnusedParameters": true,
      "noImplicitReturns": true,
      "noFallthroughCasesInSwitch": true
    }
  }
  ```

- ✅ **明示的な型定義**
  - すべての関数の引数と戻り値に型を明示
  - インターフェース・型エイリアスを積極的に使用
  ```typescript
  // ❌ 禁止（暗黙的な型）
  function processPhoto(path) {
    // ...
  }

  // ✅ 正しい（明示的な型）
  function processPhoto(path: string): Promise<PhotoData> {
    // ...
  }
  ```

- ✅ **nullチェックの徹底**
  ```typescript
  // ❌ 禁止（nullチェックなし）
  const lat = photo.gps.lat;

  // ✅ 正しい（オプショナルチェーン + nullish coalescing）
  const lat = photo.gps?.lat ?? 0;
  ```

#### Rust厳格ルール

- ❌ **`unwrap()`、`expect()`の本番コード使用禁止**
  - 理由: panicを引き起こし、アプリケーションがクラッシュする
  - 許容: テストコード、プロトタイプのみ
  ```rust
  // ❌ 禁止（本番コード）
  let data = read_file(path).unwrap();

  // ✅ 正しい（Resultを返す）
  fn process_file(path: &str) -> Result<PhotoData, FileError> {
      let data = read_file(path)?;
      Ok(data)
  }
  ```

- ❌ **`panic!`の使用禁止**
  - 理由: 回復不可能なエラーを引き起こす
  - 例外: バグを示す`unreachable!()`のみ許容（明確なコメント付き）

- ✅ **すべてのエラーは`Result<T, E>`で返す**
  ```rust
  #[command]
  pub async fn read_exif(path: String) -> Result<ExifData, String> {
      read_exif_internal(&path).map_err(|e| e.to_string())
  }
  ```

- ✅ **型推論に頼りすぎない**
  - 公開API、構造体フィールドには明示的な型を記述
  ```rust
  // ✅ 正しい
  pub struct PhotoData {
      pub path: String,
      pub gps: Option<GPS>,
      pub datetime: Option<String>,
  }
  ```

- ❌ **unsafeブロックの使用は原則禁止**
  - 例外: パフォーマンス上どうしても必要な場合のみ
  - 必須: SAFETYコメントで安全性を証明
  ```rust
  // ✅ やむを得ない場合のみ（詳細なコメント付き）
  // SAFETY: このポインタは有効であることが保証されている。なぜなら...
  unsafe {
      // ...
  }
  ```

#### 静的解析ツール

- **Biomeチェック**: エラー・警告ゼロ
- **Rustfmtチェック**: フォーマット準拠
- **Clippyチェック**: 警告ゼロ（許容される警告は`#[allow(...)]`で理由を明示）
- **TypeScriptコンパイル**: エラーゼロ、`noUnusedLocals`、`noUnusedParameters`を有効化

#### コードレビューチェックリスト

すべてのコード変更は、以下を確認してからコミット：

- [ ] 型注釈が明示的に付いているか
- [ ] `any`型を使用していないか
- [ ] nullチェックが適切に行われているか
- [ ] エラーハンドリングが適切か（`unwrap()`を使用していないか）
- [ ] 未使用の変数・インポートがないか
- [ ] すべての警告が解消されているか

### 7.4 セキュリティ

#### 個人情報・機密情報の漏洩防止（最重要）

このアプリケーションは写真を扱うため、位置情報やメタデータなど個人情報を含む可能性があります。

- ❌ **ログに個人情報を出力しない**
  ```rust
  // ❌ 禁止（GPS座標がログに残る）
  println!("Photo GPS: lat={}, lng={}", lat, lng);

  // ✅ 正しい（個人情報をマスク）
  debug!("Photo GPS data found");
  ```

- ❌ **エラーメッセージにファイルパスを含めない**
  ```rust
  // ❌ 禁止（ユーザーのファイルパスが漏洩）
  Err(format!("Failed to read file: {}", path))

  // ✅ 正しい（パスを含めない）
  Err("Failed to read file".to_string())
  ```

- ❌ **外部サービスへのデータ送信禁止**
  - 理由: ユーザーの同意なく位置情報等を送信してはならない
  - 例外: 明示的な同意を得た機能（オンライン地図タイル取得など）のみ

- ✅ **ログファイルの取り扱い**
  - ログファイルには個人情報を記録しない
  - デバッグログは開発環境のみで有効化
  - 本番ビルドではデバッグログを無効化

#### 依存関係のセキュリティ

- **定期的な脆弱性チェック**:
  - Rust: `cargo audit`（週次実行）
  - Node.js: `pnpm audit`（週次実行）
  - GitHub Dependabotを有効化

- **信頼できるクレート・パッケージのみ使用**:
  - ダウンロード数、最終更新日、メンテナンス状況を確認
  - 不明なクレートは使用前にソースコードをレビュー

#### 入力検証

- **すべてのユーザー入力を検証**:
  ```rust
  fn validate_file_path(path: &str) -> Result<PathBuf, ValidationError> {
      let path = PathBuf::from(path);

      // パストラバーサル対策
      if path.components().any(|c| matches!(c, std::path::Component::ParentDir)) {
          return Err(ValidationError::InvalidPath);
      }

      // 許可された拡張子のみ
      let ext = path.extension()
          .and_then(|s| s.to_str())
          .ok_or(ValidationError::NoExtension)?;

      if !["jpg", "jpeg", "png", "tiff", "webp"].contains(&ext.to_lowercase().as_str()) {
          return Err(ValidationError::UnsupportedFormat);
      }

      Ok(path)
  }
  ```

- **ファイルサイズ制限**:
  - 巨大なファイルによるDoS攻撃を防ぐ
  - 合理的な上限を設定（例: 100MB）

#### Tauri特有のセキュリティ

- **Allowlistの適切な設定**（tauri.conf.json）:
  - 必要最小限の権限のみ許可
  - ファイルシステムアクセスはスコープを制限

- **IPC通信の検証**:
  - フロントエンドからのコマンド呼び出しも検証
  - 信頼境界を明確にする

### 7.5 デバッグフロー

効率的なデバッグのため、以下のサイクルを遵守してください。

#### デバッグサイクル

```
1. ログファイルを起動時に消去
   ↓
2. プロセスをキル
   ↓
3. ビルド
   ↓
4. エラー確認（ビルドエラー）
   ↓
5. 起動
   ↓
6. エラー確認（ランタイムエラー）
   ↓
7. ログファイル確認
   ↓
8. 問題が残っていれば 1. に戻る
```

#### ログファイル管理

**起動時の自動消去**:

```rust
// src-tauri/src/main.rs
use std::fs;

fn setup_logging() -> Result<(), Box<dyn std::error::Error>> {
    let log_path = get_log_file_path();

    // 起動時にログファイルを削除
    if log_path.exists() {
        fs::remove_file(&log_path)?;
    }

    // 新しいログファイルを作成
    // ...

    Ok(())
}
```

#### ログレベルの使い分け

- **ERROR**: 回復不可能なエラー、ユーザーに通知すべき問題
- **WARN**: 潜在的な問題、非推奨の使用
- **INFO**: 重要なイベント（ファイル読み込み開始/完了など）
- **DEBUG**: 詳細なデバッグ情報（開発時のみ）
- **TRACE**: 非常に詳細な情報（パフォーマンス調査時のみ）

**開発環境と本番環境の切り替え**:

```rust
#[cfg(debug_assertions)]
let log_level = LevelFilter::Debug;

#[cfg(not(debug_assertions))]
let log_level = LevelFilter::Info;
```

#### デバッグツール

- **Rustデバッグ**:
  - `dbg!()` マクロ（開発時のみ、コミット前に削除）
  - `tracing` クレートでログ出力
  - `cargo test --nocapture` でテスト時のprintln出力を表示

- **TypeScriptデバッグ**:
  - `console.log()`, `console.error()`（開発時のみ、コミット前に削除）
  - React DevTools
  - Vite DevToolsのソースマップ

---

## 8. ドキュメント管理

### 8.1 更新が必要なドキュメント

新機能追加や仕様変更時に更新すべきドキュメント：

1. **README.md**: プロジェクト概要、インストール方法
2. **CHANGELOG.md**: 変更履歴
3. **docs/TAURI_MIGRATION_PLAN.md**: アーキテクチャや技術的決定が変わった場合
4. **tasks.md**: タスクの完了状況
5. **このファイル（claude.md）**: ルールの追加・変更

### 8.2 コード内ドキュメント

- **TypeScript**: JSDocコメント（複雑な関数のみ）
  ```typescript
  /**
   * EXIF情報から位置データを抽出
   * @param exif EXIF情報オブジェクト
   * @returns GPS座標、存在しない場合はnull
   */
  function extractGPS(exif: ExifData): GPS | null {
    // ...
  }
  ```

- **Rust**: Docコメント（公開API）
  ```rust
  /// EXIF情報からGPS座標を抽出します
  ///
  /// # Arguments
  /// * `path` - 画像ファイルのパス
  ///
  /// # Returns
  /// GPS座標を含むResult、失敗時はエラー
  pub fn extract_gps(path: &str) -> Result<GPS, ExifError> {
      // ...
  }
  ```

### 8.3 ドキュメントの品質

- **正確性**: 実装と一致していること
- **網羅性**: 必要な情報が揃っていること
- **明確性**: 曖昧さがないこと
- **最新性**: 古い情報が残っていないこと

---

## 9. AIへの具体的な指示

### 9.1 実装依頼を受けた時

1. **理解の確認**: 要求を正しく理解できているか確認
2. **関連ドキュメントの参照**: `docs/TAURI_MIGRATION_PLAN.md`, `tasks.md`を確認
3. **実装方針の提案**: 複数の実装方法がある場合は選択肢を提示
4. **承認後に実装**: 方針が承認されてから実装開始
5. **テストの追加**: 実装と同時にテストを追加
6. **tasks.mdの更新**: 完了したタスクにチェック

### 9.2 質問を受けた時

1. **明確な回答**: 曖昧な表現を避ける
2. **理由の説明**: 「なぜそうなのか」を説明
3. **コード例の提示**: 具体的な例を示す
4. **関連ドキュメントの参照**: 参照すべきドキュメントを案内

### 9.3 レビュー依頼を受けた時

1. **コードの理解**: まずコード全体を理解
2. **問題点の指摘**: バグ、パフォーマンス、可読性の問題を指摘
3. **改善提案**: 具体的な改善案を提示
4. **良い点の評価**: 良い実装は積極的に評価

---

## 10. 緊急時の対応

### 10.1 ビルドエラー

1. **エラーメッセージの確認**: 完全なエラーメッセージを読む
2. **原因の特定**: どのファイルのどの行でエラーが発生しているか
3. **修正の実施**: エラーを修正
4. **再ビルド**: 修正後、再度ビルドして確認

### 10.2 ランタイムエラー

1. **エラーログの確認**: コンソール、ログファイルを確認
2. **再現手順の特定**: エラーが発生する手順を特定
3. **デバッグ**: `console.log`, `dbg!`等でデバッグ
4. **修正**: 原因を特定して修正
5. **テスト追加**: 再発防止のためにテストを追加

### 10.3 パフォーマンス問題

1. **計測**: まず実際のパフォーマンスを計測
2. **ボトルネックの特定**: プロファイリングツールで特定
3. **最適化**: ボトルネックを最適化
4. **再計測**: 最適化後、効果を確認

---

## 11. 最後に

このガイドラインは**絶対的なルール**ではなく、**より良い開発のための指針**です。状況に応じて柔軟に解釈し、必要であればこのドキュメント自体を更新してください。

**重要な原則**:
- 🎯 **動くものを優先**: 完璧よりもまず動作するものを
- 📚 **学びを大切に**: 失敗から学び、成長する
- 🤝 **協力的に**: AIと人間が協力して最良の結果を目指す
- 🔄 **継続的改善**: 常により良い方法を模索する

**質問・提案・改善はいつでも歓迎**します！

---

**作成者**: PhotoGeoView開発チーム
**最終更新**: 2025-12-29
**バージョン**: 1.0
