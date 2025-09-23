#!/usr/bin/env python3
"""
環境変数検証スクリプト
GitHub Secrets設定の検証とフォーマットチェックを行う
"""

import re
import sys
import json
from typing import Dict, List, Tuple, Optional


class EnvVarValidator:
    """環境変数検証クラス"""
    
    def __init__(self):
        # 環境変数の検証ルール
        self.validation_rules = {
            'GOOGLE_CLIENT_ID': {
                'required': True,
                'pattern': r'^[0-9]+-[a-zA-Z0-9]+\.apps\.googleusercontent\.com$',
                'description': 'Google OAuth Client ID',
                'example': '123456789-abcdefg.apps.googleusercontent.com'
            },
            'GOOGLE_CLIENT_SECRET': {
                'required': True,
                'pattern': r'^GOCSPX-[a-zA-Z0-9_-]+$',
                'description': 'Google OAuth Client Secret',
                'example': 'GOCSPX-abcdefghijklmnopqrstuvwxyz'
            },
            'VERCEL_TOKEN': {
                'required': True,
                'pattern': r'^[a-zA-Z0-9_-]+$',
                'min_length': 20,
                'description': 'Vercel Personal Access Token',
                'example': 'vercel_1234567890abcdef'
            },
            'VERCEL_ORG_ID': {
                'required': True,
                'pattern': r'^team_[a-zA-Z0-9]+$',
                'description': 'Vercel Team/Organization ID',
                'example': 'team_1234567890abcdef'
            },
            'VERCEL_PROJECT_ID': {
                'required': True,
                'pattern': r'^prj_[a-zA-Z0-9]+$',
                'description': 'Vercel Project ID',
                'example': 'prj_1234567890abcdef'
            },
            'AWS_ACCESS_KEY_ID': {
                'required': True,
                'pattern': r'^AKIA[0-9A-Z]{16}$',
                'description': 'AWS Access Key ID',
                'example': 'AKIAIOSFODNN7EXAMPLE'
            },
            'AWS_SECRET_ACCESS_KEY': {
                'required': True,
                'min_length': 40,
                'description': 'AWS Secret Access Key',
                'example': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
            }
        }
    
    def validate_single_var(self, var_name: str, var_value: str) -> Tuple[bool, List[str]]:
        """単一環境変数の検証"""
        errors = []
        
        if var_name not in self.validation_rules:
            errors.append(f"未知の環境変数: {var_name}")
            return False, errors
        
        rule = self.validation_rules[var_name]
        
        # 必須チェック
        if rule.get('required', False) and not var_value:
            errors.append(f"{var_name} は必須です")
            return False, errors
        
        if not var_value:
            return True, []  # 任意項目で空の場合はOK
        
        # 長さチェック
        if 'min_length' in rule and len(var_value) < rule['min_length']:
            errors.append(f"{var_name} は {rule['min_length']} 文字以上である必要があります")
        
        if 'max_length' in rule and len(var_value) > rule['max_length']:
            errors.append(f"{var_name} は {rule['max_length']} 文字以下である必要があります")
        
        # パターンチェック
        if 'pattern' in rule:
            if not re.match(rule['pattern'], var_value):
                errors.append(f"{var_name} の形式が正しくありません。例: {rule.get('example', 'N/A')}")
        
        # カスタム検証
        custom_errors = self._custom_validation(var_name, var_value)
        errors.extend(custom_errors)
        
        return len(errors) == 0, errors
    
    def _custom_validation(self, var_name: str, var_value: str) -> List[str]:
        """カスタム検証ルール"""
        errors = []
        
        # 共通の弱いパターンチェック
        weak_patterns = ['password', '123456', 'secret', 'admin', 'test', 'example']
        for pattern in weak_patterns:
            if pattern.lower() in var_value.lower():
                errors.append(f"{var_name} に弱いパターンが含まれています: {pattern}")
        
        # 環境変数固有の検証
        if var_name == 'GOOGLE_CLIENT_ID':
            if 'localhost' in var_value:
                errors.append("GOOGLE_CLIENT_ID にlocalhostが含まれています（本番環境では適切ではありません）")
        
        elif var_name == 'VERCEL_TOKEN':
            if var_value.startswith('vercel_') and len(var_value) < 30:
                errors.append("VERCEL_TOKEN が短すぎる可能性があります")
        
        elif var_name == 'AWS_ACCESS_KEY_ID':
            if not var_value.startswith('AKIA'):
                errors.append("AWS_ACCESS_KEY_ID は通常 'AKIA' で始まります")
        
        return errors
    
    def validate_env_vars(self, env_vars: Dict[str, str]) -> Tuple[bool, Dict[str, List[str]]]:
        """複数環境変数の一括検証"""
        all_valid = True
        all_errors = {}
        
        # 各環境変数を検証
        for var_name, var_value in env_vars.items():
            is_valid, errors = self.validate_single_var(var_name, var_value)
            if not is_valid:
                all_valid = False
                all_errors[var_name] = errors
        
        # 必須環境変数の存在チェック
        required_vars = [name for name, rule in self.validation_rules.items() if rule.get('required', False)]
        missing_vars = [var for var in required_vars if var not in env_vars or not env_vars[var]]
        
        if missing_vars:
            all_valid = False
            all_errors['missing'] = [f"必須環境変数が不足: {', '.join(missing_vars)}"]
        
        # 相互依存関係のチェック
        dependency_errors = self._check_dependencies(env_vars)
        if dependency_errors:
            all_valid = False
            all_errors['dependencies'] = dependency_errors
        
        return all_valid, all_errors
    
    def _check_dependencies(self, env_vars: Dict[str, str]) -> List[str]:
        """環境変数間の依存関係チェック"""
        errors = []
        
        # Google OAuth設定の整合性
        google_client_id = env_vars.get('GOOGLE_CLIENT_ID', '')
        google_client_secret = env_vars.get('GOOGLE_CLIENT_SECRET', '')
        
        if google_client_id and not google_client_secret:
            errors.append("GOOGLE_CLIENT_ID が設定されていますが、GOOGLE_CLIENT_SECRET が不足しています")
        elif google_client_secret and not google_client_id:
            errors.append("GOOGLE_CLIENT_SECRET が設定されていますが、GOOGLE_CLIENT_ID が不足しています")
        
        # Vercel設定の整合性
        vercel_token = env_vars.get('VERCEL_TOKEN', '')
        vercel_org_id = env_vars.get('VERCEL_ORG_ID', '')
        vercel_project_id = env_vars.get('VERCEL_PROJECT_ID', '')
        
        if vercel_token and not (vercel_org_id and vercel_project_id):
            errors.append("VERCEL_TOKEN が設定されていますが、VERCEL_ORG_ID または VERCEL_PROJECT_ID が不足しています")
        
        # AWS設定の整合性
        aws_access_key = env_vars.get('AWS_ACCESS_KEY_ID', '')
        aws_secret_key = env_vars.get('AWS_SECRET_ACCESS_KEY', '')
        
        if aws_access_key and not aws_secret_key:
            errors.append("AWS_ACCESS_KEY_ID が設定されていますが、AWS_SECRET_ACCESS_KEY が不足しています")
        elif aws_secret_key and not aws_access_key:
            errors.append("AWS_SECRET_ACCESS_KEY が設定されていますが、AWS_ACCESS_KEY_ID が不足しています")
        
        return errors
    
    def generate_validation_report(self, env_vars: Dict[str, str]) -> str:
        """検証レポートの生成"""
        is_valid, errors = self.validate_env_vars(env_vars)
        
        report = []
        report.append("=" * 60)
        report.append("環境変数検証レポート")
        report.append("=" * 60)
        report.append("")
        
        if is_valid:
            report.append("✅ 全ての環境変数が正常です！")
            report.append("")
            report.append("検証済み環境変数:")
            for var_name in env_vars:
                if var_name in self.validation_rules:
                    desc = self.validation_rules[var_name]['description']
                    report.append(f"  ✅ {var_name}: {desc}")
        else:
            report.append("❌ 環境変数に問題があります")
            report.append("")
            
            for var_name, var_errors in errors.items():
                if var_name == 'missing':
                    report.append("📋 不足している環境変数:")
                    for error in var_errors:
                        report.append(f"  ❌ {error}")
                elif var_name == 'dependencies':
                    report.append("🔗 依存関係の問題:")
                    for error in var_errors:
                        report.append(f"  ❌ {error}")
                else:
                    report.append(f"🔧 {var_name} の問題:")
                    for error in var_errors:
                        report.append(f"  ❌ {error}")
                report.append("")
            
            report.append("💡 修正方法:")
            report.append("  1. 上記の問題を確認してください")
            report.append("  2. 正しい形式で環境変数を設定してください")
            report.append("  3. このスクリプトを再実行して確認してください")
        
        report.append("")
        report.append("📚 参考情報:")
        report.append("  - Google OAuth: https://console.cloud.google.com/")
        report.append("  - Vercel: https://vercel.com/dashboard")
        report.append("  - AWS: https://console.aws.amazon.com/iam/")
        
        return "\n".join(report)
    
    def interactive_validation(self) -> bool:
        """対話式検証"""
        print("🔍 環境変数の対話式検証を開始します")
        print("=" * 50)
        print()
        
        env_vars = {}
        
        for var_name, rule in self.validation_rules.items():
            if rule.get('required', False):
                print(f"📝 {var_name} ({rule['description']})")
                print(f"💡 例: {rule.get('example', 'N/A')}")
                
                while True:
                    if 'SECRET' in var_name or 'TOKEN' in var_name or 'KEY' in var_name:
                        import getpass
                        var_value = getpass.getpass("🔐 値を入力してください: ")
                    else:
                        var_value = input("📝 値を入力してください: ")
                    
                    is_valid, errors = self.validate_single_var(var_name, var_value)
                    if is_valid:
                        env_vars[var_name] = var_value
                        print("✅ 検証に合格しました")
                        break
                    else:
                        print("❌ 検証に失敗しました:")
                        for error in errors:
                            print(f"  - {error}")
                        print()
                
                print()
        
        # 最終検証
        print("🔍 最終検証を実行中...")
        is_valid, errors = self.validate_env_vars(env_vars)
        
        if is_valid:
            print("✅ 全ての環境変数が正常です！")
            return True
        else:
            print("❌ 最終検証で問題が見つかりました:")
            for var_name, var_errors in errors.items():
                for error in var_errors:
                    print(f"  - {error}")
            return False


def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description='環境変数検証スクリプト')
    parser.add_argument('--interactive', '-i', action='store_true', help='対話式検証モード')
    parser.add_argument('--json', '-j', type=str, help='JSON形式の環境変数ファイル')
    parser.add_argument('--env-file', '-e', type=str, help='.env形式のファイル')
    
    args = parser.parse_args()
    
    validator = EnvVarValidator()
    
    if args.interactive:
        # 対話式検証
        success = validator.interactive_validation()
        sys.exit(0 if success else 1)
    
    elif args.json:
        # JSON形式ファイルの検証
        try:
            with open(args.json, 'r', encoding='utf-8') as f:
                env_vars = json.load(f)
            
            report = validator.generate_validation_report(env_vars)
            print(report)
            
            is_valid, _ = validator.validate_env_vars(env_vars)
            sys.exit(0 if is_valid else 1)
            
        except FileNotFoundError:
            print(f"❌ ファイルが見つかりません: {args.json}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ JSON形式エラー: {e}")
            sys.exit(1)
    
    elif args.env_file:
        # .env形式ファイルの検証
        try:
            env_vars = {}
            with open(args.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
            
            report = validator.generate_validation_report(env_vars)
            print(report)
            
            is_valid, _ = validator.validate_env_vars(env_vars)
            sys.exit(0 if is_valid else 1)
            
        except FileNotFoundError:
            print(f"❌ ファイルが見つかりません: {args.env_file}")
            sys.exit(1)
    
    else:
        # ヘルプ表示
        parser.print_help()
        print()
        print("使用例:")
        print("  python3 validate-env-vars.py --interactive")
        print("  python3 validate-env-vars.py --json env-vars.json")
        print("  python3 validate-env-vars.py --env-file .env")


if __name__ == '__main__':
    main()