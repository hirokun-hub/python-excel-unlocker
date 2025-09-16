# テスト戦略とディレクトリ構成

## 概要

Secure Excel Unlockプロジェクトのテスト戦略は、設計書で定義された品質目標を達成するために、複数レイヤーでのテストを実装します。

## テストレイヤー

### 1. 単体テスト (Unit Tests)
**目標カバレッジ**: 80%以上

#### フロントエンド
- **フレームワーク**: Jest + React Testing Library
- **対象**: コンポーネント、hooks、ユーティリティ関数
- **実行**: `npm run test` (frontend/)

#### バックエンド
- **フレームワーク**: pytest + moto
- **対象**: Lambda関数、ビジネスロジック、AWS統合
- **実行**: `pytest tests/` (backend/)

### 2. 統合テスト (Integration Tests)
#### API統合テスト
- **フレームワーク**: Postman/Newman
- **対象**: APIエンドポイント間の連携
- **実行**: GitHub Actions CI

#### 認証フロー統合テスト
- **対象**: Google OAuth認証フロー
- **環境**: テスト用Google OAuth設定

### 3. E2Eテスト (End-to-End Tests)
- **フレームワーク**: Playwright
- **対象**: ユーザージャーニー全体
- **実行**: `npm run test:e2e` (frontend/)

### 4. パフォーマンステスト
- **フレームワーク**: Artillery.js
- **目標**: P95 < 8秒、同時実行50
- **実行**: 本番デプロイ後

## ディレクトリ構成

```
tests/
├── README.md                           # このファイル
├── api/                               # API統合テスト
│   ├── secure-excel-unlock.postman_collection.json
│   ├── test.postman_environment.json
│   └── README.md
├── performance/                       # パフォーマンステスト
│   ├── load-test.yml
│   ├── stress-test.yml
│   └── README.md
└── fixtures/                         # テスト用データ
    ├── sample-files/
    │   ├── password-protected.xlsx
    │   ├── corrupted.xlsx
    │   └── large-file.xlsx
    └── mock-responses/
        ├── auth-responses.json
        └── api-responses.json

frontend/
├── __tests__/                        # フロントエンド単体テスト
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   └── pages/
├── e2e/                              # E2Eテスト
│   ├── auth.spec.ts
│   ├── file-upload.spec.ts
│   ├── password-unlock.spec.ts
│   └── error-handling.spec.ts
└── playwright.config.ts

backend/
├── tests/                            # バックエンド単体テスト
│   ├── unit/
│   │   ├── test_upload_url.py
│   │   ├── test_unlock.py
│   │   └── test_auth.py
│   ├── integration/
│   │   ├── test_s3_integration.py
│   │   └── test_lambda_integration.py
│   └── conftest.py                   # pytest設定
└── pytest.ini
```

## テスト実行方法

### ローカル開発環境

#### フロントエンド
```bash
cd frontend
npm run test              # 単体テスト
npm run test:coverage     # カバレッジ付き単体テスト
npm run test:e2e          # E2Eテスト
npm run test:e2e:ui       # E2EテストUI付き
```

#### バックエンド
```bash
cd backend
pytest                    # 全テスト実行
pytest --cov=src         # カバレッジ付きテスト
pytest tests/unit/       # 単体テストのみ
pytest tests/integration/ # 統合テストのみ
```

### CI/CD環境
GitHub Actionsが自動実行：
1. プルリクエスト作成時：全テスト実行
2. mainブランチマージ時：全テスト + デプロイ + パフォーマンステスト

## テストデータ管理

### テスト用Excelファイル
- **パスワード付きファイル**: `tests/fixtures/sample-files/`
- **パスワード**: 環境変数 `TEST_EXCEL_PASSWORDS`
- **破損ファイル**: テストケース用

### モックデータ
- **AWS S3**: motoライブラリでモック
- **Google OAuth**: テスト用トークン
- **API レスポンス**: `tests/fixtures/mock-responses/`

## 品質ゲート

### プルリクエスト要件
- [ ] 単体テストカバレッジ ≥ 80%
- [ ] 全テストパス
- [ ] Linting エラーなし
- [ ] 型チェックエラーなし
- [ ] セキュリティスキャンパス

### デプロイ要件
- [ ] 全テストスイートパス
- [ ] E2Eテストパス
- [ ] API統合テストパス
- [ ] セキュリティスキャンパス

### パフォーマンス要件
- [ ] P95レスポンス時間 < 8秒
- [ ] 同時実行50ユーザー対応
- [ ] エラー率 < 5%

## 継続的改善

### メトリクス監視
- テストカバレッジの推移
- テスト実行時間の監視
- フレーキーテストの特定

### テスト戦略の見直し
- 月次でテスト結果レビュー
- 新機能追加時のテスト拡張
- パフォーマンス目標の調整

## トラブルシューティング

### よくある問題
1. **E2Eテストの不安定性**: ページロード待機時間の調整
2. **AWS motoエラー**: 環境変数の設定確認
3. **認証テスト失敗**: テスト用OAuth設定の確認

### デバッグ方法
- ローカルでのテスト実行
- GitHub Actions ログの確認
- テスト用データの検証