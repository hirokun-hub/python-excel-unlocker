# 実装計画

- [ ] 1. 既存スクリプトの動作確認とテスト
  - 既存の `scripts/normalize_vercel_project.py` スクリプトの動作を確認
  - 既存の `scripts/validate-ci-environment.py` スクリプトの動作を確認
  - ローカル環境でのスクリプト実行テストを実施
  - 様々なシナリオ（正常ケース、エラーケース）での動作確認
  - _要件: 1.2, 2.2, 4.1, 4.2_

- [ ] 2. GitHub Actions 関連スクリプトの .github/scripts/ への移動
  - `scripts/normalize_vercel_project.py` を `.github/scripts/` ディレクトリに移動
  - `scripts/validate-ci-environment.py` を `.github/scripts/` ディレクトリに移動
  - 移動後のスクリプトファイルの実行権限を確認
  - 移動後のスクリプトが正常に動作することを確認
  - _要件: 2.1, 2.2, 6.1, 6.3, 7.2_

- [ ] 3. ワークフローファイルのバックアップと修正準備
  - 現在の `build-frontend.yml` ファイルのバックアップを作成
  - インライン Python コード部分（98-114行目）の正確な特定
  - 修正対象ステップの前後関係を確認
  - _要件: 1.1, 3.1, 4.3_

- [ ] 4. ワークフローファイルとカスタムアクションの参照パス更新
  - `build-frontend.yml` のインライン Python コード（98-114行目）を削除
  - `build-frontend.yml` に `python3 .github/scripts/normalize_vercel_project.py` ステップを追加
  - `deploy-vercel-reusable.yml` の参照パスを `.github/scripts/normalize_vercel_project.py` に更新
  - `validate-environment/action.yml` の参照パスを `.github/scripts/validate-ci-environment.py` に更新
  - YAML 構文の正確性を確認
  - _要件: 1.1, 1.4, 2.1, 3.3, 6.1, 6.2_

- [ ] 5. 修正後のワークフローファイルの構文検証
  - YAML 構文エラーがないことを確認
  - GitHub Actions ワークフロー構文の妥当性をチェック
  - ステップ名と処理内容の整合性を確認
  - _要件: 3.2, 5.1, 5.4_

- [ ] 6. ローカル環境での動作テスト
  - 修正したワークフローステップをローカルで模擬実行
  - `normalize_vercel_project.py` のテスト（`frontend/.vercel/project.json` ファイルを用意）
  - `validate-ci-environment.py` のテスト（環境変数を設定）
  - 正常ケースとエラーケースの両方をテスト
  - 既存のインライン コードと同じ結果が得られることを確認
  - _要件: 4.1, 4.2, 4.4, 5.2, 6.3_

- [ ] 7. GitHub Actions での統合テスト
  - 修正したワークフローを GitHub にプッシュ
  - 実際の CI/CD パイプラインでの動作確認
  - `build-frontend.yml` での `normalize_vercel_project.py` 実行テスト
  - `deploy-vercel-reusable.yml` での `normalize_vercel_project.py` 実行テスト
  - `validate-environment` カスタムアクションでの `validate-ci-environment.py` 実行テスト
  - エラーハンドリングが適切に動作することを確認
  - _要件: 4.3, 5.3, 6.1, 6.2, 6.4_

- [ ] 8. パフォーマンスと互換性の検証
  - ワークフロー実行時間の変化を測定
  - 既存機能との互換性を確認
  - エラーメッセージの内容と品質を検証
  - GitHub Actions ログでの情報表示を確認
  - _要件: 4.4, 5.1, 5.4, 6.3_

- [ ] 9. ドキュメントの更新と成果物の整理
  - 変更内容を適切なドキュメントに記録
  - GitHub Actions 関連スクリプトの配置方針を文書化
  - コードの重複解消と統一化の成果を記録
  - `.github/scripts/` ディレクトリの使用ガイドラインを作成
  - 将来的な改善提案をまとめる
  - _要件: 6.1, 6.2, 6.4, 7.1, 7.3, 7.4_