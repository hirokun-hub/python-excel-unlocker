#!/usr/bin/env python3
"""
GitHub OIDC設定の検証と改善スクリプト

このスクリプトは以下を実行します：
1. 現在のIAMロール信頼ポリシーの確認
2. 複数ブランチ対応の信頼関係設定確認
3. 最小権限原則の適用状況確認
4. セキュリティ設定の改善提案
"""

import json
import subprocess
import sys
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class SecurityAuditor:
    def __init__(self):
        self.results = {
            'oidc_provider': None,
            'iam_role': None,
            'trust_policy': None,
            'attached_policies': [],
            'security_issues': [],
            'recommendations': []
        }
        
    def run_aws_command(self, command: List[str]) -> Tuple[bool, str]:
        """AWS CLIコマンドを実行"""
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
            return False, "AWS CLI not found"
    
    def check_oidc_provider(self) -> bool:
        """GitHub OIDCプロバイダーの存在確認"""
        print("🔍 GitHub OIDCプロバイダーの確認中...")
        
        success, output = self.run_aws_command([
            'aws', 'iam', 'list-open-id-connect-providers'
        ])
        
        if not success:
            self.results['security_issues'].append({
                'type': 'oidc_provider',
                'severity': 'high',
                'message': f"OIDCプロバイダーの確認に失敗: {output}"
            })
            return False
        
        try:
            providers = json.loads(output)
            github_provider = None
            
            for provider in providers.get('OpenIDConnectProviderList', []):
                if 'token.actions.githubusercontent.com' in provider['Arn']:
                    github_provider = provider
                    break
            
            if github_provider:
                self.results['oidc_provider'] = github_provider
                print(f"✅ GitHub OIDCプロバイダーが見つかりました: {github_provider['Arn']}")
                return True
            else:
                self.results['security_issues'].append({
                    'type': 'oidc_provider',
                    'severity': 'high',
                    'message': "GitHub OIDCプロバイダーが見つかりません"
                })
                self.results['recommendations'].append({
                    'type': 'setup',
                    'message': "GitHub OIDCプロバイダーを作成してください: ./scripts/setup-github-oidc.sh"
                })
                return False
                
        except json.JSONDecodeError:
            self.results['security_issues'].append({
                'type': 'oidc_provider',
                'severity': 'medium',
                'message': "OIDCプロバイダー情報の解析に失敗"
            })
            return False
    
    def find_github_actions_role(self) -> Optional[str]:
        """GitHub Actions用IAMロールを検索"""
        print("🔍 GitHub Actions用IAMロールの検索中...")
        
        # 一般的なロール名パターンで検索
        role_patterns = [
            'GitHubActionsRole',
            'GitHubActions-Role',
            'github-actions-role',
            'ExcelUnlockerGitHubActionsRole'
        ]
        
        for role_name in role_patterns:
            success, output = self.run_aws_command([
                'aws', 'iam', 'get-role', '--role-name', role_name
            ])
            
            if success:
                try:
                    role_data = json.loads(output)
                    role = role_data['Role']
                    
                    # 信頼ポリシーでGitHub OIDCを使用しているか確認
                    trust_policy = role['AssumeRolePolicyDocument']
                    if isinstance(trust_policy, str):
                        trust_policy = json.loads(trust_policy)
                    
                    # GitHub OIDCプロバイダーを参照しているか確認
                    for statement in trust_policy.get('Statement', []):
                        principal = statement.get('Principal', {})
                        if 'Federated' in principal:
                            federated = principal['Federated']
                            if 'token.actions.githubusercontent.com' in federated:
                                print(f"✅ GitHub Actions用IAMロールが見つかりました: {role_name}")
                                return role_name
                                
                except json.JSONDecodeError:
                    continue
        
        print("⚠️ GitHub Actions用IAMロールが見つかりません")
        return None
    
    def check_trust_policy(self, role_name: str) -> bool:
        """信頼ポリシーの詳細確認"""
        print(f"🔍 IAMロール '{role_name}' の信頼ポリシー確認中...")
        
        success, output = self.run_aws_command([
            'aws', 'iam', 'get-role', '--role-name', role_name
        ])
        
        if not success:
            self.results['security_issues'].append({
                'type': 'trust_policy',
                'severity': 'high',
                'message': f"IAMロールの取得に失敗: {output}"
            })
            return False
        
        try:
            role_data = json.loads(output)
            self.results['iam_role'] = role_data['Role']
            
            trust_policy = role_data['Role']['AssumeRolePolicyDocument']
            if isinstance(trust_policy, str):
                trust_policy = json.loads(trust_policy)
            
            self.results['trust_policy'] = trust_policy
            
            # 信頼ポリシーの分析
            self._analyze_trust_policy(trust_policy)
            
            return True
            
        except json.JSONDecodeError as e:
            self.results['security_issues'].append({
                'type': 'trust_policy',
                'severity': 'medium',
                'message': f"信頼ポリシーの解析に失敗: {str(e)}"
            })
            return False
    
    def _analyze_trust_policy(self, trust_policy: Dict):
        """信頼ポリシーの詳細分析"""
        print("🔍 信頼ポリシーの詳細分析中...")
        
        for statement in trust_policy.get('Statement', []):
            # Principal確認
            principal = statement.get('Principal', {})
            if 'Federated' not in principal:
                self.results['security_issues'].append({
                    'type': 'trust_policy',
                    'severity': 'high',
                    'message': "信頼ポリシーにFederatedプリンシパルが設定されていません"
                })
                continue
            
            federated = principal['Federated']
            if 'token.actions.githubusercontent.com' not in federated:
                self.results['security_issues'].append({
                    'type': 'trust_policy',
                    'severity': 'high',
                    'message': "GitHub OIDCプロバイダーが信頼ポリシーに設定されていません"
                })
                continue
            
            # Action確認
            action = statement.get('Action', '')
            if action != 'sts:AssumeRoleWithWebIdentity':
                self.results['security_issues'].append({
                    'type': 'trust_policy',
                    'severity': 'medium',
                    'message': f"不適切なAction設定: {action}"
                })
            
            # Condition確認
            condition = statement.get('Condition', {})
            self._analyze_conditions(condition)
    
    def _analyze_conditions(self, condition: Dict):
        """信頼ポリシーの条件分析"""
        # aud条件の確認
        string_equals = condition.get('StringEquals', {})
        aud_condition = string_equals.get('token.actions.githubusercontent.com:aud')
        
        if not aud_condition or aud_condition != 'sts.amazonaws.com':
            self.results['security_issues'].append({
                'type': 'trust_policy',
                'severity': 'medium',
                'message': "aud条件が適切に設定されていません"
            })
        
        # sub条件の確認（リポジトリ制限）
        string_like = condition.get('StringLike', {})
        sub_condition = string_like.get('token.actions.githubusercontent.com:sub')
        
        if not sub_condition:
            self.results['security_issues'].append({
                'type': 'trust_policy',
                'severity': 'high',
                'message': "リポジトリ制限（sub条件）が設定されていません"
            })
        else:
            self._analyze_repository_restrictions(sub_condition)
    
    def _analyze_repository_restrictions(self, sub_condition):
        """リポジトリ制限の分析"""
        if isinstance(sub_condition, str):
            sub_conditions = [sub_condition]
        else:
            sub_conditions = sub_condition
        
        expected_patterns = [
            "repo:hironomac2025/excel-password-remover:ref:refs/heads/main",
            "repo:hironomac2025/excel-password-remover:ref:refs/heads/develop",
            "repo:hironomac2025/excel-password-remover:*"
        ]
        
        # ワイルドカード使用の確認
        has_wildcard = any('*' in condition for condition in sub_conditions)
        if has_wildcard:
            self.results['security_issues'].append({
                'type': 'trust_policy',
                'severity': 'medium',
                'message': "ワイルドカード使用により、すべてのブランチからのアクセスが許可されています"
            })
            self.results['recommendations'].append({
                'type': 'security',
                'message': "特定のブランチのみに制限することを検討してください"
            })
        
        # 複数ブランチ対応の確認
        branch_specific = [c for c in sub_conditions if 'ref:refs/heads/' in c]
        if branch_specific:
            print(f"✅ ブランチ制限が設定されています: {len(branch_specific)}個のブランチ")
        else:
            print("⚠️ 特定ブランチへの制限が設定されていません")
    
    def check_attached_policies(self, role_name: str) -> bool:
        """アタッチされたポリシーの確認"""
        print(f"🔍 IAMロール '{role_name}' のポリシー確認中...")
        
        success, output = self.run_aws_command([
            'aws', 'iam', 'list-attached-role-policies', '--role-name', role_name
        ])
        
        if not success:
            self.results['security_issues'].append({
                'type': 'policies',
                'severity': 'medium',
                'message': f"ポリシー一覧の取得に失敗: {output}"
            })
            return False
        
        try:
            policies_data = json.loads(output)
            attached_policies = policies_data.get('AttachedPolicies', [])
            
            self.results['attached_policies'] = attached_policies
            
            if not attached_policies:
                self.results['security_issues'].append({
                    'type': 'policies',
                    'severity': 'high',
                    'message': "IAMロールにポリシーがアタッチされていません"
                })
                return False
            
            # 各ポリシーの詳細確認
            for policy in attached_policies:
                self._analyze_policy(policy)
            
            return True
            
        except json.JSONDecodeError as e:
            self.results['security_issues'].append({
                'type': 'policies',
                'severity': 'medium',
                'message': f"ポリシー情報の解析に失敗: {str(e)}"
            })
            return False
    
    def _analyze_policy(self, policy: Dict):
        """個別ポリシーの分析"""
        policy_name = policy['PolicyName']
        policy_arn = policy['PolicyArn']
        
        print(f"  📋 ポリシー分析中: {policy_name}")
        
        # AWS管理ポリシーの確認
        if policy_arn.startswith('arn:aws:iam::aws:policy/'):
            aws_managed_policies = [
                'AdministratorAccess',
                'PowerUserAccess',
                'IAMFullAccess'
            ]
            
            if policy_name in aws_managed_policies:
                self.results['security_issues'].append({
                    'type': 'policies',
                    'severity': 'high',
                    'message': f"過度な権限のAWS管理ポリシーが使用されています: {policy_name}"
                })
                self.results['recommendations'].append({
                    'type': 'security',
                    'message': f"カスタムポリシーで最小権限に制限してください: {policy_name}"
                })
        
        # カスタマー管理ポリシーの詳細確認
        else:
            success, output = self.run_aws_command([
                'aws', 'iam', 'get-policy-version',
                '--policy-arn', policy_arn,
                '--version-id', 'v1'
            ])
            
            if success:
                try:
                    policy_data = json.loads(output)
                    policy_document = policy_data['PolicyVersion']['Document']
                    self._analyze_policy_permissions(policy_document, policy_name)
                except json.JSONDecodeError:
                    pass
    
    def _analyze_policy_permissions(self, policy_document: Dict, policy_name: str):
        """ポリシー権限の詳細分析"""
        for statement in policy_document.get('Statement', []):
            effect = statement.get('Effect', '')
            actions = statement.get('Action', [])
            resources = statement.get('Resource', [])
            
            if effect != 'Allow':
                continue
            
            if isinstance(actions, str):
                actions = [actions]
            
            # 危険な権限の確認
            dangerous_actions = [
                'iam:*',
                '*:*',
                'iam:CreateRole',
                'iam:AttachRolePolicy',
                'iam:PutRolePolicy'
            ]
            
            for action in actions:
                if action in dangerous_actions:
                    self.results['security_issues'].append({
                        'type': 'policies',
                        'severity': 'high',
                        'message': f"危険な権限が設定されています: {action} in {policy_name}"
                    })
            
            # リソース制限の確認
            if isinstance(resources, str):
                resources = [resources]
            
            if '*' in resources:
                self.results['security_issues'].append({
                    'type': 'policies',
                    'severity': 'medium',
                    'message': f"リソース制限が設定されていません: {policy_name}"
                })
                self.results['recommendations'].append({
                    'type': 'security',
                    'message': f"特定のリソースに制限することを検討してください: {policy_name}"
                })
    
    def generate_improved_trust_policy(self) -> Dict:
        """改善された信頼ポリシーの生成"""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": f"arn:aws:iam::{self._get_account_id()}:oidc-provider/token.actions.githubusercontent.com"
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity",
                    "Condition": {
                        "StringEquals": {
                            "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                        },
                        "StringLike": {
                            "token.actions.githubusercontent.com:sub": [
                                "repo:hironomac2025/excel-password-remover:ref:refs/heads/main",
                                "repo:hironomac2025/excel-password-remover:ref:refs/heads/develop"
                            ]
                        }
                    }
                }
            ]
        }
    
    def _get_account_id(self) -> str:
        """AWSアカウントIDの取得"""
        success, output = self.run_aws_command([
            'aws', 'sts', 'get-caller-identity', '--query', 'Account', '--output', 'text'
        ])
        
        if success:
            return output.strip()
        else:
            return "ACCOUNT-ID"
    
    def generate_minimal_policy(self) -> Dict:
        """最小権限ポリシーの生成"""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "cloudformation:CreateStack",
                        "cloudformation:UpdateStack",
                        "cloudformation:DeleteStack",
                        "cloudformation:DescribeStacks",
                        "cloudformation:DescribeStackEvents",
                        "cloudformation:DescribeStackResources",
                        "cloudformation:GetTemplate"
                    ],
                    "Resource": [
                        f"arn:aws:cloudformation:ap-northeast-1:{self._get_account_id()}:stack/excel-unlocker-api-*/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:CreateBucket",
                        "s3:DeleteBucket",
                        "s3:GetBucketLocation",
                        "s3:GetBucketPolicy",
                        "s3:PutBucketPolicy",
                        "s3:DeleteBucketPolicy",
                        "s3:GetBucketCORS",
                        "s3:PutBucketCORS",
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject"
                    ],
                    "Resource": [
                        "arn:aws:s3:::excel-unlocker-*",
                        "arn:aws:s3:::excel-unlocker-*/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:CreateFunction",
                        "lambda:UpdateFunctionCode",
                        "lambda:UpdateFunctionConfiguration",
                        "lambda:DeleteFunction",
                        "lambda:GetFunction",
                        "lambda:ListFunctions",
                        "lambda:AddPermission",
                        "lambda:RemovePermission"
                    ],
                    "Resource": [
                        f"arn:aws:lambda:ap-northeast-1:{self._get_account_id()}:function:excel-unlocker-*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "apigateway:*"
                    ],
                    "Resource": [
                        f"arn:aws:apigateway:ap-northeast-1::/restapis/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "iam:PassRole"
                    ],
                    "Resource": [
                        f"arn:aws:iam::{self._get_account_id()}:role/excel-unlocker-*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams"
                    ],
                    "Resource": [
                        f"arn:aws:logs:ap-northeast-1:{self._get_account_id()}:log-group:/aws/lambda/excel-unlocker-*"
                    ]
                }
            ]
        }
    
    def print_summary(self):
        """監査結果のサマリー表示"""
        print("\n" + "="*60)
        print("🔒 GitHub OIDC セキュリティ監査結果")
        print("="*60)
        
        # 基本情報
        if self.results['oidc_provider']:
            print(f"✅ OIDCプロバイダー: 設定済み")
        else:
            print(f"❌ OIDCプロバイダー: 未設定")
        
        if self.results['iam_role']:
            print(f"✅ IAMロール: {self.results['iam_role']['RoleName']}")
        else:
            print(f"❌ IAMロール: 見つかりません")
        
        print(f"📋 アタッチされたポリシー数: {len(self.results['attached_policies'])}")
        
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
        """結果をJSONファイルに保存"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"security-audit-{timestamp}.json"
        
        # 改善提案を追加
        self.results['improvements'] = {
            'trust_policy': self.generate_improved_trust_policy(),
            'minimal_policy': self.generate_minimal_policy()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 監査結果を保存しました: {filename}")
    
    def run_audit(self):
        """完全な監査を実行"""
        print("🔒 GitHub OIDC セキュリティ監査を開始します...")
        print(f"⏰ 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. OIDCプロバイダーの確認
        oidc_ok = self.check_oidc_provider()
        
        # 2. IAMロールの検索
        role_name = self.find_github_actions_role()
        
        if role_name:
            # 3. 信頼ポリシーの確認
            trust_ok = self.check_trust_policy(role_name)
            
            # 4. アタッチされたポリシーの確認
            policies_ok = self.check_attached_policies(role_name)
        else:
            self.results['security_issues'].append({
                'type': 'iam_role',
                'severity': 'high',
                'message': "GitHub Actions用IAMロールが見つかりません"
            })
            self.results['recommendations'].append({
                'type': 'setup',
                'message': "GitHub Actions用IAMロールを作成してください: ./scripts/setup-github-oidc.sh"
            })
        
        # 5. 結果の表示と保存
        self.print_summary()
        self.save_results()
        
        # 6. 終了コードの決定
        high_issues = [i for i in self.results['security_issues'] if i['severity'] == 'high']
        if high_issues:
            print(f"\n❌ 重大なセキュリティ問題が {len(high_issues)} 件見つかりました")
            return 1
        else:
            print(f"\n✅ セキュリティ監査が完了しました")
            return 0

def main():
    """メイン処理"""
    auditor = SecurityAuditor()
    exit_code = auditor.run_audit()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()