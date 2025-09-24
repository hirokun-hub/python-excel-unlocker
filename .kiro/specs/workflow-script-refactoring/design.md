# GitHub Actions ワークフロー スクリプト リファクタリング - 設計書

## 概要

GitHub Actions ワークフロー内のインライン Python コードを外部スクリプトファイルに移行し、GitHub Actions 関連の Python スクリプトを `.github/scripts/` ディレクトリに統一して保守性を向上させる設計です。現在 `build-frontend.yml` の98-114行目に存在するインライン Python コードの外部化と、GitHub Actions で使用されている Python スクリプトの配置統一を行います。

## アーキテクチャ

### 現在の構成
```
.github/workflows/build-frontend.yml
├── Step: "Normalize Vercel project root"
│   └── インライン Python コード (98-114行目)

.github/workflows/deploy-vercel-reusable.yml
├── Step: "Normalize Vercel project root"
│   └── python3 scripts/normalize_vercel_project.py

.github/actions/validate-environment/action.yml
├── Step: "環境変数検証実行"
│   └── python scripts/validate-ci-environment.py

scripts/ (分散配置)
├── normalize_vercel_project.py (Vercel設定正規化)
├── validate-ci-environment.py (CI環境検証)
└── その他のスクリプト...
```

### 変更後の構成
```
.github/workflows/build-frontend.yml
├── Step: "Normalize Vercel project root"
│   └── python3 .github/scripts/normalize_vercel_project.py

.github/workflows/deploy-vercel-reusable.yml
├── Step: "Normalize Vercel project root"
│   └── python3 .github/scripts/normalize_vercel_project.py

.github/actions/validate-environment/action.yml
├── Step: "環境変数検証実行"
│   └── python .github/scripts/validate-ci-environment.py

.github/scripts/ (統一配置)
├── normalize_vercel_project.py (移動・統一)
├── validate-ci-environment.py (移動・統一)
└── 将来のGitHub Actions関連スクリプト...

scripts/ (一般用途スクリプト)
├── setup-*.sh (セットアップスクリプト)
├── security-audit-*.py (セキュリティ監査)
└── その他の一般スクリプト...
```

## コンポーネントとインターフェース

### 1. ワークフローステップ（変更対象）

**現在の実装:**
```yaml
- name: Normalize Vercel project root
  run: |
    python - <<'PY'
import json
import pathlib

project_file = pathlib.Path("frontend/.vercel/project.json")
if not project_file.exists():
    raise SystemExit("project.json not found after vercel pull")

data = json.loads(project_file.read_text())
settings = data.get("projectSettings") or {}

if settings.get("rootDirectory") not in (None, "", "."):
    settings["rootDirectory"] = ""
    data["projectSettings"] = settings
    project_file.write_text(json.dumps(data, indent=2) + "\n")
PY
```

**変更後の実装:**
```yaml
- name: Normalize Vercel project root
  run: python3 .github/scripts/normalize_vercel_project.py
```

### 2. 外部スクリプト（移動・活用）

#### 2.1 Vercel設定正規化スクリプト

**ファイル:** `.github/scripts/normalize_vercel_project.py`

**インターフェース:**
- **入力:** なし（ファイルパスはハードコード）
- **出力:** 標準出力（エラー時のみ）
- **戻り値:** 0（成功）、1（失敗）
- **副作用:** `frontend/.vercel/project.json` ファイルの変更

**処理フロー:**
1. `frontend/.vercel/project.json` ファイルの存在確認
2. JSON データの読み込み
3. `projectSettings.rootDirectory` の確認
4. 必要に応じて空文字列に設定
5. ファイルの書き込み

#### 2.2 CI環境検証スクリプト

**ファイル:** `.github/scripts/validate-ci-environment.py`

**インターフェース:**
- **入力:** 環境変数（AWS_*, VERCEL_*, GITHUB_* など）
- **出力:** 標準出力（検証結果）、JSON ファイル（サマリー）
- **戻り値:** 0（成功）、1（失敗）
- **副作用:** `ci-validation-summary.json` ファイルの生成

**処理フロー:**
1. AWS認証情報の検証
2. Vercel設定の検証
3. GitHub Actions環境の検証
4. Node.js/Python環境の検証
5. 検証結果のサマリー生成

### 3. エラーハンドリング

**既存スクリプトのエラーハンドリング:**
```python
if not project_file.exists():
    sys.exit("project.json not found after vercel pull")
```

**GitHub Actions での処理:**
- スクリプトが非ゼロで終了した場合、ワークフローが停止
- エラーメッセージは GitHub Actions ログに出力
- 後続のステップは実行されない

## データモデル

### 処理対象ファイル構造

**ファイルパス:** `frontend/.vercel/project.json`

**データ構造:**
```json
{
  "projectSettings": {
    "rootDirectory": "frontend" | "" | null
  }
}
```

**変更ロジック:**
- `rootDirectory` が `null`、`""`、`"."` の場合 → 変更なし
- `rootDirectory` が他の値の場合 → `""` に設定

### 実行環境

**GitHub Actions ランナー:**
- OS: Ubuntu latest
- Python: 3.x（デフォルトインストール済み）
- 作業ディレクトリ: リポジトリルート

**前提条件:**
- `vercel pull` コマンドが正常に実行済み
- `frontend/.vercel/project.json` ファイルが存在

## エラーハンドリング

### エラーシナリオと対応

#### 1. スクリプトファイルが存在しない
**発生条件:** `.github/scripts/normalize_vercel_project.py` が削除されている
**エラーメッセージ:** `python3: can't open file '.github/scripts/normalize_vercel_project.py': [Errno 2] No such file or directory`
**対応:** ワークフロー停止、GitHub Actions ログでエラー確認

#### 2. project.json ファイルが存在しない
**発生条件:** `vercel pull` が失敗している
**エラーメッセージ:** `project.json not found after vercel pull`
**対応:** スクリプトが exit(1) で終了、ワークフロー停止

#### 3. JSON 解析エラー
**発生条件:** `project.json` が不正な JSON 形式
**エラーメッセージ:** Python の JSON 解析エラー
**対応:** スクリプトが例外で終了、ワークフロー停止

#### 4. ファイル書き込みエラー
**発生条件:** ファイルシステムの権限問題
**エラーメッセージ:** Python のファイル I/O エラー
**対応:** スクリプトが例外で終了、ワークフロー停止

### エラー処理の改善案

現在のスクリプトは基本的なエラーハンドリングを実装していますが、より詳細なエラー情報を提供するために以下の改善が可能です：

```python
def main() -> None:
    try:
        project_file = Path("frontend/.vercel/project.json")
        
        if not project_file.exists():
            sys.exit("project.json not found after vercel pull")
        
        data = json.loads(project_file.read_text())
        # ... 処理続行
        
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON in project.json: {e}")
    except PermissionError as e:
        sys.exit(f"Permission denied accessing project.json: {e}")
    except Exception as e:
        sys.exit(f"Unexpected error: {e}")
```

ただし、今回のリファクタリングでは既存スクリプトの変更は行わず、現在の実装をそのまま活用します。

## テスト戦略

### 1. 機能テスト

**テストケース 1: 正常処理**
- 前提条件: `frontend/.vercel/project.json` が存在し、`rootDirectory` が設定されている
- 実行: `python3 .github/scripts/normalize_vercel_project.py`
- 期待結果: `rootDirectory` が空文字列に設定される

**テストケース 2: 変更不要**
- 前提条件: `rootDirectory` が既に空文字列または null
- 実行: `python3 .github/scripts/normalize_vercel_project.py`
- 期待結果: ファイルが変更されない

**テストケース 3: ファイル不存在**
- 前提条件: `frontend/.vercel/project.json` が存在しない
- 実行: `python3 .github/scripts/normalize_vercel_project.py`
- 期待結果: エラーメッセージと exit(1)

### 2. 統合テスト

**ワークフロー統合テスト:**
1. `vercel pull` の実行
2. `normalize_vercel_project.py` の実行
3. `vercel build` の実行
4. 全体の成功確認

### 3. 回帰テスト

**比較テスト:**
- インライン Python コード実行結果
- 外部スクリプト実行結果
- 両者の出力ファイルが同一であることを確認

## パフォーマンス考慮事項

### 実行時間の比較

**インライン Python コード:**
- Python インタープリター起動: ~100ms
- スクリプト実行: ~10ms
- 合計: ~110ms

**外部スクリプト:**
- Python インタープリター起動: ~100ms
- ファイル読み込み: ~5ms
- スクリプト実行: ~10ms
- 合計: ~115ms

**差異:** 約5ms の増加（無視できるレベル）

### リソース使用量

**メモリ使用量:** 変化なし（同じ処理内容）
**ディスク I/O:** 微増（スクリプトファイル読み込み）
**CPU 使用量:** 変化なし

## セキュリティ考慮事項

### 1. スクリプトファイルの整合性

**リスク:** スクリプトファイルの改ざん
**対策:** Git による版数管理、コードレビュー

### 2. 実行権限

**現在の設定:** スクリプトファイルに実行権限は不要（python3 コマンドで実行）
**セキュリティ:** 最小権限の原則に従い、実行権限を付与しない

### 3. パス注入攻撃

**リスク:** 相対パスによる意図しないファイル実行
**対策:** 固定パス `.github/scripts/normalize_vercel_project.py` を使用

## 実装計画

### Phase 1: GitHub Actions 関連スクリプトの移動

1. `scripts/normalize_vercel_project.py` を `.github/scripts/` に移動
2. `scripts/validate-ci-environment.py` を `.github/scripts/` に移動
3. 移動後のスクリプトファイルの動作確認

### Phase 2: ワークフローファイルとカスタムアクションの修正

1. `build-frontend.yml` の98-114行目のインライン Python コードを削除
2. `build-frontend.yml` に新しいステップを追加:
   ```yaml
   - name: Normalize Vercel project root
     run: python3 .github/scripts/normalize_vercel_project.py
   ```
3. `deploy-vercel-reusable.yml` の参照パスを更新:
   ```yaml
   - name: Normalize Vercel project root
     run: python3 .github/scripts/normalize_vercel_project.py
   ```
4. `validate-environment/action.yml` の参照パスを更新:
   ```yaml
   python .github/scripts/validate-ci-environment.py
   ```

### Phase 2: 動作確認

1. ローカル環境でのスクリプト実行テスト
2. GitHub Actions での動作確認
3. 既存機能との互換性確認

### Phase 3: ドキュメント更新

1. 変更内容の記録
2. 今後のスクリプト外部化方針の文書化

## 運用考慮事項

### 1. 監視ポイント

- ワークフロー実行時間の変化
- エラー発生率の変化
- スクリプト実行成功率

### 2. メンテナンス

- スクリプトファイルの定期的な見直し
- エラーハンドリングの改善
- パフォーマンス最適化

### 3. 拡張性

**将来的な改善:**
- 他のワークフローでの同様のリファクタリング
- スクリプトディレクトリの整理
- 共通ユーティリティスクリプトの作成

## 成功基準

### 1. 機能的成功基準

- ✅ インライン Python コードの完全削除
- ✅ 外部スクリプトの正常実行
- ✅ 既存機能との100%互換性
- ✅ エラーハンドリングの維持

### 2. 非機能的成功基準

- ✅ 実行時間の大幅な増加なし（5ms以内）
- ✅ ワークフローファイルの可読性向上
- ✅ コードの重複解消
- ✅ 保守性の向上

### 3. 運用的成功基準

- ✅ CI/CD パイプラインの安定性維持
- ✅ エラー発生時の適切な情報提供
- ✅ 将来的な拡張性の確保

## リスク分析

### 高リスク

**なし** - 既存スクリプトを活用するため、新規実装リスクは最小

### 中リスク

1. **ワークフロー構文エラー**
   - 確率: 低
   - 影響: 中
   - 対策: 事前の構文チェック、段階的デプロイ

### 低リスク

1. **パフォーマンス劣化**
   - 確率: 低
   - 影響: 低
   - 対策: 実行時間の監視

2. **互換性問題**
   - 確率: 極低
   - 影響: 中
   - 対策: 既存スクリプトの事前テスト

## 結論

このリファクタリングは、既存の実装済みスクリプトを活用することで、リスクを最小限に抑えながらコードの重複を解消し、保守性を向上させる効果的な改善です。実装は単純で、既存機能への影響も最小限に抑えられます。