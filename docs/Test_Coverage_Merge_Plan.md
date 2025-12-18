```markdown
# PhotoGeoView カバレッジ統合プラン（実装計画付き）

## 目的
- 現在のユニットテスト（Vitest）のみのカバレッジ（約63%）に、PlaywrightのE2Eテストで実行されるコードパスを追加して統合。
- カバレッジ稼ぎのための無理なテストを書かずに、**意味のあるE2Eテストで自然にカバレッジを向上**させる。
- 目標：全体カバレッジを75〜85%程度まで引き上げる（特にUIインタラクション・地図操作・ファイル操作関連のパスを補完）。

## 適用方針（本リポジトリ向け）
- Vitest（ユニット/コンポーネント）とPlaywright（E2E）の両方で **Istanbul形式** のカバレッジデータを収集し、`nyc` でマージして総合レポートを生成する。
- レンダラー（`src/renderer/src`）は `vite-plugin-istanbul` によるinstrumentを行い、E2E実行時に `window.__coverage__` を収集する。メインプロセスは初期段階では除外し、必要なら後で追加する。
- 本番ビルドへの影響を避けるため、instrumentは環境変数による有効化（例: `VITE_COVERAGE=true`）で制御する。

---

## 追加するdevDependencies（推奨）
pnpm を使っているため、以下を devDependencies に追加してください：

```bash
pnpm add -D vite-plugin-istanbul nyc @vitest/coverage-istanbul
```

- `@vitest/coverage-istanbul` は Vitest で `coverage.provider = 'istanbul'` を利用する場合の依存です（環境により不要な場合あり）。

---

## 具体的な実装手順（ファイル/コード例付き） 🔧

### 1) Renderer の instrument（`electron.vite.config.ts`）
- `renderer.plugins` に `vite-plugin-istanbul` を追加。`include` を `src/renderer/src/**` にする。
- `requireEnv: true` にして `VITE_COVERAGE=true` 時のみ有効にする。

サンプル（抜粋）:
```ts
import istanbul from 'vite-plugin-istanbul'

renderer: {
  // ...既存設定...
  plugins: [
    react(),
    istanbul({
      include: 'src/renderer/src/**',
      exclude: ['node_modules', 'tests/**', '**/*.test.*'],
      extension: ['.ts', '.tsx', '.js', '.jsx'],
      requireEnv: true,
      cypress: false,
      checkProd: false,
    }),
  ],
},
```

> 理由: Electron のレンダラーで実際に動作するコードパスを instrument するため。


### 2) Vitest の設定（`vitest.config.ts`）
- `coverage.provider` を `istanbul` に変更し、reportsDirectory を `./coverage/vitest` にする。

変更例（抜粋）:
```ts
coverage: {
  provider: 'istanbul',
  reporter: ['text', 'html', 'lcov'],
  reportsDirectory: './coverage/vitest',
  include: ['src/renderer/src/**/*.{ts,tsx}', 'src/types/**/*.ts'],
  exclude: ['**/*.test.{ts,tsx}', 'src/main/**', 'src/preload/**'],
},
```

> すでに `vitest.config.ts` は `happy-dom` を使っています。レンダラー向けのコードをユニットテストでカバーしている現在の構成は大きく変えなくて良いです。


### 3) Playwright でのカバレッジ収集（E2E）
- E2E テスト実行中に `window.__coverage__` を `page.evaluate` で取得し、`.nyc_output` にユニーク名で保存する仕組みを追加する。
- **レンダラーはビルド時に `vite-plugin-istanbul` で instrument** し、E2E はその instrument 済みビルドを起動して計測する（post-build instrumentation は不要）。

推奨：共通ヘルパ `tests/e2e/helpers/collect-coverage.ts` を作る（または各 spec の afterAll で保存）。

サンプル（単一ファイルでの例）:
```ts
import fs from 'fs'
import path from 'path'

export async function saveRendererCoverage(page: any) {
  const coverage = await page.evaluate(() => (window as any).__coverage__)
  if (!coverage) return
  fs.mkdirSync('.nyc_output', { recursive: true })
  const file = path.join('.nyc_output', `renderer-${Date.now()}.json`)
  fs.writeFileSync(file, JSON.stringify(coverage))
}
```

- Playwright の各テストファイルの `afterAll` で `saveRendererCoverage(page)` を呼ぶ（`page` を引き回すかfixtureで共通化）。

> 注意: `playwright.config.ts` は現在 `workers: 1` なのでファイル名重複は起きにくいですが、並列環境でもユニーク名（タイムスタンプ）を使えば安全です。


### 4) package.json のスクリプト（pnpm 向け）
```json
"scripts": {
  "test:unit": "vitest run --coverage",
  "test:e2e": "playwright test",
  "test:e2e:coverage": "cross-env VITE_COVERAGE=true pnpm build && pnpm test:e2e",
  "coverage:merge": "node ./scripts/merge-report.js"
}
```

> 重要: E2E でカバレッジを取るには **instrumented なビルドを起動**する必要があります。`VITE_COVERAGE=true pnpm build` を行い、E2E 実行前に生成物が instrumented されることを保証してください。


### 5) CI（GitHub Actions）への組み込み
- `.github/workflows/ci.yml` の E2E ジョブでビルドを `VITE_COVERAGE=true pnpm build` に置き換え、E2E 実行後に `.nyc_output` をアーティファクトとして保存することを推奨します。

抜粋（例）:
```yaml
- name: Build instrumented application
  run: VITE_COVERAGE=true pnpm build

- name: Run E2E tests (coverage)
  run: xvfb-run --auto-servernum -- pnpm test:e2e
  env:
    ELECTRON_DISABLE_SANDBOX: 1
```

- テスト後に `.nyc_output` を CI artifact として保存しておくとデバッグが楽になります。


---

## .nycrc の推奨設定（`.nycrc.json`）
```json
{
  "reporter": ["lcov", "html", "text"],
  "exclude": ["**/tests/**", "**/*.d.ts", "src/main/**", "src/preload/**"],
  "extension": [".ts", ".tsx", ".js", ".jsx"]
}
```

---

## 検証手順（ローカルでの確認） ✅
1. 依存追加: `pnpm install`
2. ユニットカバレッジ生成: `pnpm test:unit` → `coverage/vitest` を確認
3. Instrumented ビルドとE2E実行:
   - `VITE_COVERAGE=true pnpm build`
   - `pnpm test:e2e`（または `pnpm test:e2e:coverage`）
4. E2E 実行後に `.nyc_output` に JSON ファイルが生成されていることを確認
5. `pnpm coverage:merge` を実行してターミナルに Summary が出ることを確認（`coverage/merged.json` も生成）

---

## リスクと軽減策 ⚠️
- Instrumentation により本番ビルドと挙動がわずかに異なる可能性がある（パフォーマンス/サイズ）。→ `requireEnv: true` にして CI/ローカルのみで有効化。
- E2E で coverage が出ない場合、`window.__coverage__` が存在しないケースがある（レンダラーが instrument されていない等）。→ ビルド時に生成物を確認し、Playwright のテスト最後にカバレッジを取得するチェックを入れる。
- main プロセス（Node）のカバレッジは別途対応が必要（`nyc` で main を起動して計測する等）。初期はレンダラーのみで実施することを推奨。

---

## 作業タスク（段階的）
1. `pnpm add -D vite-plugin-istanbul nyc @vitest/coverage-istanbul`（依存追加）
2. `electron.vite.config.ts` に plugin を追加（renderer）
3. `vitest.config.ts` を `provider: 'istanbul'` に更新
4. Playwright の共通 helper (`tests/e2e/helpers/collect-coverage.ts`) を追加し、各 spec の afterAll で呼ぶ
5. `package.json` スクリプトを追加/更新
6. CI（`.github/workflows/ci.yml`）で instrumented ビルドを行い、`.nyc_output` を保存
7. 実行・確認・レポート生成

---

## まとめ
この実装計画は本リポジトリに適用可能で、レンダラー中心の E2E テストを活用することで意味のあるカバレッジを追加できます。段階的に適用して動作確認 → CI に組み込む流れを推奨します。

---

*必要であれば私がPRを作成して変更を実装できます（依存追加、config変更、Playwright helper、CI更新、簡易検証含む）。*
```
