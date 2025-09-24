#!/usr/bin/env python3
"""
GitHub Secrets管理の監査スクリプト

このスクリプトは以下を実行します：
1. GitHub Secrets使用状況の確認
2. 不要なシークレットの特定と整理
3. シークレット管理手順の文書化
4. セキュリティベストプラクティスの確認
"""

import json
import subprocess
import sys
import re
from typing import Dict, List, Optional, Set
from datetime import datetime

class GitHubSecretsAuditor:
    def __init__(self):
        self.results = {
            'repository_secrets': [],
            'workflow_secrets_usage': {},
            'unused_secrets': [],
            'missing_secrets': [],
            'security_issues': [],
            'recommendations': []
        }
        
        # 必要なシークレット一覧（要件4に基づく）
        self.required_secrets = {
            'AWS_GITHUB_ACTIONS_ROLE_ARN': {
                'description': 'GitHub OIDC用IAMロールARN',
                'pattern': r'^arn:aws:iam::\d{12}:role/.+$',
                'priority': 'high',
                'alternative': ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
            },
            'AWS_ACCESS_KEY_ID': {
                'description': 'AWS認証用アクセスキーID（OIDC未使用時）',
                'pattern': r'^AKIA[0-9A-Z]{16}$',
                'priority': 'medium',
                'deprecated_by': 'AWS_GITHUB_ACTIONS_ROLE_ARN'
            },
            'AWS_SECRET_ACCESS_KEY': {
                'description': 'AWS認証用シークレットアクセスキー（OIDC未使用時）',
                'pattern': r'^[A-Za-z0-9/+=]{40}$',
                'priority': 'medium',
                'deprecated_by': 'AWS_GITHUB_ACTIONS_ROLE_ARN'
            },
            'VERCEL_TOKEN': {
                'description': 'Vercelデプロイ用トークン',
                'pattern': r'^[A-Za-z0-9]{24}$',
                'priority': 'high'
            },
            'VERCEL_ORG_ID': {
                'description': 'Vercel組織ID',
                'pattern': r'^(team_|user_)[A-Za-z0-9]{16}$',
                'priority': 'high'
            },
            'VERCEL_PROJECT_ID': {
                'description': 'VercelプロジェクトID',
                'pattern': r'^prj_[A-Za-z0-9]{16}$',
                'priority': 'high'
            },
            'ALLOWED_USERS': {
                'description': 'アプリケーション許可ユーザーリスト',
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(,[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})*$',
                'priority': 'medium'
            }
        }
        
        # 非推奨・不要なシークレット
        self.deprecated_secrets = {
            'GOOGLE_CLIENT_ID': 'フロントエンドの環境変数として設定すべき',
            'GOOGLE_CLIENT_SECRET': 'フロントエンドの環境変数として設定すべき',
            'NEXTAUTH_SECRET': 'フロントエンドの環境変数として設定すべき',
            'NEXTAUTH_URL': 'フロントエンドの環境変数として設定すべき'
        }
    
    def run_gh_command(self, command: List[str]) -> tuple[bool, str]:
        """GitHub CLIコマンドを実行"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()
        except FileNotFoundError:
            return False, "GitHub CLI not found"
    
    def check_gh_auth(self) -> bool:
        """GitHub CLI認証状態の確認"""
        print("🔍 GitHub CLI認証状態の確認中...")
        
        success, output = self.run_gh_command(['gh', 'auth', 'status'])
        
        if success:
            print("✅ GitHub CLIが認証されています")
            return True
        else:
            print("❌ GitHub CLIが認証されていません")
            self.results['security_issues'].append({
                'type': 'authentication',
                'severity': 'high',
                'message': 'GitHub CLIが認証されていません'
            })
            self.results['recommendations'].append({
                'type': 'setup',
                'message': 'GitHub CLIで認証してください: gh auth login'
            })
            return False
    
    def list_repository_secrets(self) -> bool:
        """リポジトリのシークレット一覧を取得"""
        print("🔍 リポジトリシークレットの一覧取得中...")
        
        success, output = self.run_gh_command(['gh', 'secret', 'list'])
        
        if not success:
            self.results['security_issues'].append({
                'type': 'secrets_access',
                'severity': 'high',
                'message': f'シークレット一覧の取得に失敗: {output}'
            })
            return False
        
        # シークレット一覧の解析
        secrets = []
        for line in output.split('\n'):
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2:
                    secret_name = parts[0].strip()
                    updated_at = parts[1].strip() if len(parts) > 1 else 'Unknown'
                    secrets.append({
                        'name': secret_name,
                        'updated_at': updated_at
                    })
        
        self.results['repository_secrets'] = secrets
        print(f"✅ {len(secrets)}個のシークレットが見つかりました")
        
        return True
    
    def analyze_workflow_secrets_usage(self) -> bool:
        """ワークフローでのシークレット使用状況を分析"""
        print("🔍 ワークフローでのシークレット使用状況分析中...")
        
        workflow_files = [
            '.github/workflows/deploy-aws.yml',
            '.github/workflows/deploy-backend.yml',
            '.github/workflows/deploy-frontend.yml',
            '.github/workflows/deploy-full-stack.yml',
            '.github/workflows/deploy-vercel-reusable.yml',
            '.github/workflows/build-frontend.yml',
            '.github/workflows/validate-frontend.yml',
            '.github/workflows/e2e-test-frontend.yml'
        ]
        
        workflow_secrets = {}
        
        for workflow_file in workflow_files:
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # secrets.XXX パターンを検索
                secret_pattern = r'secrets\.([A-Z_][A-Z0-9_]*)'
                matches = re.findall(secret_pattern, content)
                
                if matches:
                    workflow_secrets[workflow_file] = list(set(matches))
                    
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"⚠️ {workflow_file} の読み取りに失敗: {e}")
        
        self.results['workflow_secrets_usage'] = workflow_secrets
        
        # 使用されているシークレットの集計
        used_secrets = set()
        for secrets_list in workflow_secrets.values():
            used_secrets.update(secrets_list)
        
        print(f"✅ {len(used_secrets)}個のシークレットがワークフローで使用されています")
        
        return True
    
    def identify_unused_secrets(self):
        """未使用シークレットの特定"""
        print("🔍 未使用シークレットの特定中...")
        
        # ワークフローで使用されているシークレット
        used_secrets = set()
        for secrets_list in self.results['workflow_secrets_usage'].values():
            used_secrets.update(secrets_list)
        
        # リポジトリに存在するシークレット
        existing_secrets = {secret['name'] for secret in self.results['repository_secrets']}
        
        # 未使用シークレット
        unused_secrets = existing_secrets - used_secrets
        
        # 非推奨シークレットの確認
        deprecated_found = existing_secrets & set(self.deprecated_secrets.keys())
        
        self.results['unused_secrets'] = list(unused_secrets)
        
        if unused_secrets:
            print(f"⚠️ {len(unused_secrets)}個の未使用シークレットが見つかりました")
            for secret in unused_secrets:
                if secret in self.deprecated_secrets:
                    self.results['security_issues'].append({
                        'type': 'deprecated_secret',
                        'severity': 'medium',
                        'message': f'非推奨シークレット: {secret} - {self.deprecated_secrets[secret]}'
                    })
                else:
                    self.results['security_issues'].append({
                        'type': 'unused_secret',
                        'severity': 'low',
                        'message': f'未使用シークレット: {secret}'
                    })
        
        if deprecated_found:
            print(f"⚠️ {len(deprecated_found)}個の非推奨シークレットが見つかりました")
    
    def identify_missing_secrets(self):
        """不足しているシークレットの特定"""
        print("🔍 不足しているシークレットの特定中...")
        
        existing_secrets = {secret['name'] for secret in self.results['repository_secrets']}
        
        # OIDC vs アクセスキー認証の判定
        has_oidc = 'AWS_GITHUB_ACTIONS_ROLE_ARN' in existing_secrets
        has_access_keys = 'AWS_ACCESS_KEY_ID' in existing_secrets and 'AWS_SECRET_ACCESS_KEY' in existing_secrets
        
        missing_secrets = []
        
        for secret_name, config in self.required_secrets.items():
            if secret_name not in existing_secrets:
                # OIDC使用時はアクセスキーは不要
                if has_oidc and secret_name in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']:
                    continue
                
                # アクセスキー使用時はOIDCロールは不要
                if has_access_keys and secret_name == 'AWS_GITHUB_ACTIONS_ROLE_ARN':
                    continue
                
                missing_secrets.append({
                    'name': secret_name,
                    'description': config['description'],
                    'priority': config['priority']
                })
        
        self.results['missing_secrets'] = missing_secrets
        
        if missing_secrets:
            print(f"❌ {len(missing_secrets)}個の必要なシークレットが不足しています")
            for secret in missing_secrets:
                severity = 'high' if secret['priority'] == 'high' else 'medium'
                self.results['security_issues'].append({
                    'type': 'missing_secret',
                    'severity': severity,
                    'message': f'不足しているシークレット: {secret["name"]} - {secret["description"]}'
                })
        else:
            print("✅ 必要なシークレットはすべて設定されています")
    
    def validate_secret_formats(self):
        """シークレットの形式検証"""
        print("🔍 シークレット形式の検証中...")
        
        # 実際の値は取得できないため、名前ベースでの推定検証のみ
        existing_secrets = {secret['name'] for secret in self.results['repository_secrets']}
        
        # AWS認証方式の整合性確認
        has_oidc = 'AWS_GITHUB_ACTIONS_ROLE_ARN' in existing_secrets
        has_access_keys = 'AWS_ACCESS_KEY_ID' in existing_secrets and 'AWS_SECRET_ACCESS_KEY' in existing_secrets
        
        if has_oidc and has_access_keys:
            self.results['security_issues'].append({
                'type': 'auth_conflict',
                'severity': 'medium',
                'message': 'OIDC認証とアクセスキー認証の両方が設定されています。OIDC使用時はアクセスキーを削除することを推奨します。'
            })
            self.results['recommendations'].append({
                'type': 'security',
                'message': 'セキュリティ向上のため、OIDC認証に統一してアクセスキーを削除してください'
            })
        
        if not has_oidc and not has_access_keys:
            self.results['security_issues'].append({
                'type': 'no_auth',
                'severity': 'high',
                'message': 'AWS認証設定が見つかりません'
            })
    
    def check_security_best_practices(self):
        """セキュリティベストプラクティスの確認"""
        print("🔍 セキュリティベストプラクティスの確認中...")
        
        existing_secrets = {secret['name'] for secret in self.results['repository_secrets']}
        
        # OIDC使用の推奨
        if 'AWS_ACCESS_KEY_ID' in existing_secrets and 'AWS_GITHUB_ACTIONS_ROLE_ARN' not in existing_secrets:
            self.results['recommendations'].append({
                'type': 'security',
                'message': 'セキュリティ向上のため、GitHub OIDCへの移行を検討してください: ./scripts/setup-github-oidc.sh'
            })
        
        # 非推奨シークレットの確認
        deprecated_found = existing_secrets & set(self.deprecated_secrets.keys())
        if deprecated_found:
            for secret in deprecated_found:
                self.results['recommendations'].append({
                    'type': 'cleanup',
                    'message': f'非推奨シークレットを削除してください: {secret} - {self.deprecated_secrets[secret]}'
                })
        
        # シークレット数の確認
        if len(existing_secrets) > 10:
            self.results['recommendations'].append({
                'type': 'cleanup',
                'message': f'シークレット数が多すぎます（{len(existing_secrets)}個）。不要なシークレットを整理してください。'
            })
    
    def generate_cleanup_script(self) -> str:
        """シークレット整理スクリプトの生成"""
        script_lines = [
            "#!/bin/bash",
            "# GitHub Secrets整理スクリプト",
            "# 自動生成されたスクリプトです。実行前に内容を確認してください。",
            "",
            "set -e",
            "",
            "echo '🧹 GitHub Secrets整理を開始します...'",
            ""
        ]
        
        # 非推奨シークレットの削除
        existing_secrets = {secret['name'] for secret in self.results['repository_secrets']}
        deprecated_found = existing_secrets & set(self.deprecated_secrets.keys())
        
        if deprecated_found:
            script_lines.extend([
                "echo '🗑️ 非推奨シークレットの削除...'",
                ""
            ])
            
            for secret in deprecated_found:
                script_lines.extend([
                    f"echo '削除中: {secret}'",
                    f"gh secret delete {secret} --confirm || echo '削除に失敗: {secret}'",
                    ""
                ])
        
        # 未使用シークレットの削除（確認付き）
        if self.results['unused_secrets']:
            script_lines.extend([
                "echo '🤔 未使用シークレットの確認...'",
                ""
            ])
            
            for secret in self.results['unused_secrets']:
                if secret not in self.deprecated_secrets:
                    script_lines.extend([
                        f"echo '未使用シークレット: {secret}'",
                        f"read -p '{secret} を削除しますか？ (y/N): ' confirm",
                        f"if [[ $confirm == [yY] ]]; then",
                        f"    gh secret delete {secret} --confirm",
                        f"    echo '削除しました: {secret}'",
                        f"else",
                        f"    echo 'スキップしました: {secret}'",
                        f"fi",
                        ""
                    ])
        
        # 不足シークレットの設定案内
        if self.results['missing_secrets']:
            script_lines.extend([
                "echo '📝 不足しているシークレットの設定が必要です:'",
                ""
            ])
            
            for secret in self.results['missing_secrets']:
                script_lines.extend([
                    f"echo '  - {secret['name']}: {secret['description']}'",
                ])
            
            script_lines.extend([
                "",
                "echo '設定方法: gh secret set SECRET_NAME'",
                "echo 'または: ./scripts/setup-github-secrets.sh'",
                ""
            ])
        
        script_lines.extend([
            "echo '✅ GitHub Secrets整理が完了しました'",
            ""
        ])
        
        return '\n'.join(script_lines)
    
    def generate_documentation(self) -> str:
        """シークレット管理手順の文書化"""
        doc_lines = [
            "# GitHub Secrets管理手順",
            "",
            f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 現在の設定状況",
            "",
            "### 設定済みシークレット",
            ""
        ]
        
        if self.results['repository_secrets']:
            for secret in self.results['repository_secrets']:
                doc_lines.append(f"- `{secret['name']}` (更新: {secret['updated_at']})")
        else:
            doc_lines.append("- なし")
        
        doc_lines.extend([
            "",
            "### 必要なシークレット",
            ""
        ])
        
        existing_secrets = {secret['name'] for secret in self.results['repository_secrets']}
        
        for secret_name, config in self.required_secrets.items():
            status = "✅" if secret_name in existing_secrets else "❌"
            doc_lines.append(f"- {status} `{secret_name}`: {config['description']}")
        
        if self.results['missing_secrets']:
            doc_lines.extend([
                "",
                "### 不足しているシークレット",
                ""
            ])
            
            for secret in self.results['missing_secrets']:
                priority_emoji = "🔴" if secret['priority'] == 'high' else "🟡"
                doc_lines.append(f"- {priority_emoji} `{secret['name']}`: {secret['description']}")
        
        if self.results['unused_secrets']:
            doc_lines.extend([
                "",
                "### 未使用シークレット",
                ""
            ])
            
            for secret in self.results['unused_secrets']:
                doc_lines.append(f"- `{secret}`")
        
        doc_lines.extend([
            "",
            "## セキュリティ設定手順",
            "",
            "### 1. GitHub CLI認証",
            "",
            "```bash",
            "gh auth login",
            "```",
            "",
            "### 2. シークレット設定",
            "",
            "```bash",
            "# 自動設定スクリプト（推奨）",
            "./scripts/setup-github-secrets.sh",
            "",
            "# 手動設定",
            "gh secret set SECRET_NAME",
            "```",
            "",
            "### 3. 設定確認",
            "",
            "```bash",
            "# シークレット一覧確認",
            "gh secret list",
            "",
            "# セキュリティ監査",
            "./scripts/security-audit-github-secrets.py",
            "```",
            "",
            "## ベストプラクティス",
            "",
            "### セキュリティ",
            "",
            "- ✅ GitHub OIDCを使用してAWS認証（推奨）",
            "- ✅ 最小権限の原則に従ったIAMポリシー",
            "- ✅ 定期的なシークレットローテーション",
            "- ✅ 未使用シークレットの定期的な削除",
            "",
            "### 管理",
            "",
            "- ✅ シークレット名の統一的な命名規則",
            "- ✅ 設定変更時の文書化",
            "- ✅ 定期的なセキュリティ監査",
            "",
            "## トラブルシューティング",
            "",
            "### よくある問題",
            "",
            "1. **GitHub CLI認証エラー**",
            "   ```bash",
            "   gh auth logout",
            "   gh auth login",
            "   ```",
            "",
            "2. **シークレット設定エラー**",
            "   - リポジトリの管理者権限を確認",
            "   - シークレット名の形式を確認（大文字・アンダースコアのみ）",
            "",
            "3. **AWS認証エラー**",
            "   - OIDC設定の確認: `./scripts/security-audit-github-oidc.py`",
            "   - IAMロール信頼ポリシーの確認",
            "",
            "## 参考資料",
            "",
            "- [GitHub Secrets設定ガイド](./github-secrets-setup-guide.md)",
            "- [GitHub OIDC移行ガイド](./github-oidc-migration.md)",
            "- [セキュリティ強化ガイド](./security-enhancements.md)",
            ""
        ])
        
        return '\n'.join(doc_lines)
    
    def print_summary(self):
        """監査結果のサマリー表示"""
        print("\n" + "="*60)
        print("🔐 GitHub Secrets セキュリティ監査結果")
        print("="*60)
        
        # 基本統計
        total_secrets = len(self.results['repository_secrets'])
        missing_count = len(self.results['missing_secrets'])
        unused_count = len(self.results['unused_secrets'])
        
        print(f"📊 シークレット統計:")
        print(f"  📋 設定済み: {total_secrets}個")
        print(f"  ❌ 不足: {missing_count}個")
        print(f"  🗑️ 未使用: {unused_count}個")
        
        # セキュリティ問題
        issues_by_severity = {}
        for issue in self.results['security_issues']:
            severity = issue['severity']
            if severity not in issues_by_severity:
                issues_by_severity[severity] = []
            issues_by_severity[severity].append(issue)
        
        print(f"\n🚨 セキュリティ問題:")
        for severity in ['high', 'medium', 'low']:
            if severity in issues_by_severity:
                count = len(issues_by_severity[severity])
                emoji = "🔴" if severity == 'high' else "🟡" if severity == 'medium' else "🟢"
                print(f"  {emoji} {severity.upper()}: {count}件")
        
        if not self.results['security_issues']:
            print("  ✅ セキュリティ問題は見つかりませんでした")
        
        # 詳細な問題一覧
        if self.results['security_issues']:
            print(f"\n📝 問題の詳細:")
            for i, issue in enumerate(self.results['security_issues'], 1):
                severity_emoji = "🔴" if issue['severity'] == 'high' else "🟡" if issue['severity'] == 'medium' else "🟢"
                print(f"  {i}. {severity_emoji} [{issue['type']}] {issue['message']}")
        
        # 推奨事項
        if self.results['recommendations']:
            print(f"\n💡 推奨事項:")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"  {i}. [{rec['type']}] {rec['message']}")
    
    def save_results(self, filename: str = None):
        """結果をファイルに保存"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"github-secrets-audit-{timestamp}"
        
        # JSON結果の保存
        json_filename = f"{filename}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # 整理スクリプトの保存
        cleanup_script = self.generate_cleanup_script()
        script_filename = f"{filename}-cleanup.sh"
        with open(script_filename, 'w', encoding='utf-8') as f:
            f.write(cleanup_script)
        
        # 管理手順文書の保存
        documentation = self.generate_documentation()
        doc_filename = f"{filename}-management-guide.md"
        with open(doc_filename, 'w', encoding='utf-8') as f:
            f.write(documentation)
        
        print(f"\n💾 監査結果を保存しました:")
        print(f"  📄 監査結果: {json_filename}")
        print(f"  🧹 整理スクリプト: {script_filename}")
        print(f"  📖 管理手順: {doc_filename}")
    
    def run_audit(self):
        """完全な監査を実行"""
        print("🔐 GitHub Secrets セキュリティ監査を開始します...")
        print(f"⏰ 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. GitHub CLI認証確認
        if not self.check_gh_auth():
            return 1
        
        # 2. シークレット一覧取得
        if not self.list_repository_secrets():
            return 1
        
        # 3. ワークフローでの使用状況分析
        self.analyze_workflow_secrets_usage()
        
        # 4. 未使用シークレットの特定
        self.identify_unused_secrets()
        
        # 5. 不足シークレットの特定
        self.identify_missing_secrets()
        
        # 6. シークレット形式の検証
        self.validate_secret_formats()
        
        # 7. セキュリティベストプラクティスの確認
        self.check_security_best_practices()
        
        # 8. 結果の表示と保存
        self.print_summary()
        self.save_results()
        
        # 9. 終了コードの決定
        high_issues = [i for i in self.results['security_issues'] if i['severity'] == 'high']
        if high_issues:
            print(f"\n❌ 重大なセキュリティ問題が {len(high_issues)} 件見つかりました")
            return 1
        else:
            print(f"\n✅ GitHub Secrets監査が完了しました")
            return 0

def main():
    """メイン処理"""
    auditor = GitHubSecretsAuditor()
    exit_code = auditor.run_audit()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()