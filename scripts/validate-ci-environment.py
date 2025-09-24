#!/usr/bin/env python3
"""
CI/CD環境変数設定の検証スクリプト

GitHub ActionsのSecretsと環境変数が適切に設定されているかを検証します。
"""

import os
import sys
import json
import subprocess
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class ValidationLevel(Enum):
    """検証レベル"""
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"

@dataclass
class ValidationResult:
    """検証結果"""
    name: str
    level: ValidationLevel
    status: bool
    message: str
    suggestion: Optional[str] = None

class CIEnvironmentValidator:
    """CI環境検証クラス"""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        
    def validate_aws_secrets(self) -> List[ValidationResult]:
        """AWS関連のSecrets検証"""
        results = []
        
        # GitHub OIDC (推奨)
        oidc_role = os.getenv('AWS_GITHUB_ACTIONS_ROLE_ARN')
        if oidc_role:
            results.append(ValidationResult(
                name="AWS_GITHUB_ACTIONS_ROLE_ARN",
                level=ValidationLevel.RECOMMENDED,
                status=True,
                message="GitHub OIDC用IAMロールが設定されています",
                suggestion="セキュリティのため推奨される認証方式です"
            ))
        else:
            # アクセスキー認証の確認
            access_key = os.getenv('AWS_ACCESS_KEY_ID')
            secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            
            if access_key and secret_key:
                results.append(ValidationResult(
                    name="AWS Access Keys",
                    level=ValidationLevel.REQUIRED,
                    status=True,
                    message="AWSアクセスキーが設定されています",
                    suggestion="セキュリティ向上のためGitHub OIDCへの移行を検討してください"
                ))
            else:
                results.append(ValidationResult(
                    name="AWS Authentication",
                    level=ValidationLevel.REQUIRED,
                    status=False,
                    message="AWS認証情報が設定されていません",
                    suggestion="AWS_GITHUB_ACTIONS_ROLE_ARN または AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY を設定してください"
                ))
        
        # AWS Region
        aws_region = os.getenv('AWS_REGION', os.getenv('AWS_DEFAULT_REGION'))
        results.append(ValidationResult(
            name="AWS_REGION",
            level=ValidationLevel.REQUIRED,
            status=bool(aws_region),
            message=f"AWSリージョン: {aws_region}" if aws_region else "AWSリージョンが設定されていません",
            suggestion="ap-northeast-1 (東京) を推奨します" if not aws_region else None
        ))
        
        return results
    
    def validate_vercel_secrets(self) -> List[ValidationResult]:
        """Vercel関連のSecrets検証"""
        results = []
        
        vercel_token = os.getenv('VERCEL_TOKEN')
        results.append(ValidationResult(
            name="VERCEL_TOKEN",
            level=ValidationLevel.REQUIRED,
            status=bool(vercel_token),
            message="Vercelトークンが設定されています" if vercel_token else "Vercelトークンが設定されていません",
            suggestion="Vercel Dashboard → Settings → Tokens で作成してください" if not vercel_token else None
        ))
        
        vercel_org_id = os.getenv('VERCEL_ORG_ID')
        results.append(ValidationResult(
            name="VERCEL_ORG_ID",
            level=ValidationLevel.REQUIRED,
            status=bool(vercel_org_id),
            message="Vercel組織IDが設定されています" if vercel_org_id else "Vercel組織IDが設定されていません",
            suggestion="vercel link コマンドで .vercel/project.json から取得できます" if not vercel_org_id else None
        ))
        
        vercel_project_id = os.getenv('VERCEL_PROJECT_ID')
        results.append(ValidationResult(
            name="VERCEL_PROJECT_ID",
            level=ValidationLevel.REQUIRED,
            status=bool(vercel_project_id),
            message="VercelプロジェクトIDが設定されています" if vercel_project_id else "VercelプロジェクトIDが設定されていません",
            suggestion="vercel link コマンドで .vercel/project.json から取得できます" if not vercel_project_id else None
        ))
        
        return results
    
    def validate_application_secrets(self) -> List[ValidationResult]:
        """アプリケーション固有のSecrets検証"""
        results = []
        
        allowed_users = os.getenv('ALLOWED_USERS')
        results.append(ValidationResult(
            name="ALLOWED_USERS",
            level=ValidationLevel.RECOMMENDED,
            status=bool(allowed_users),
            message="許可ユーザーリストが設定されています" if allowed_users else "許可ユーザーリストが設定されていません",
            suggestion="カンマ区切りでメールアドレスを設定してください（例: user1@example.com,user2@example.com）" if not allowed_users else None
        ))
        
        return results
    
    def validate_github_environment(self) -> List[ValidationResult]:
        """GitHub Actions環境の検証"""
        results = []
        
        # GitHub関連環境変数
        github_vars = [
            ('GITHUB_TOKEN', ValidationLevel.REQUIRED, 'GitHub Actions標準トークン'),
            ('GITHUB_REPOSITORY', ValidationLevel.REQUIRED, 'リポジトリ名'),
            ('GITHUB_ACTOR', ValidationLevel.REQUIRED, '実行者'),
            ('GITHUB_RUN_ID', ValidationLevel.REQUIRED, '実行ID'),
        ]
        
        for var_name, level, description in github_vars:
            value = os.getenv(var_name)
            results.append(ValidationResult(
                name=var_name,
                level=level,
                status=bool(value),
                message=f"{description}: {value[:20]}..." if value and len(value) > 20 else f"{description}: {value}" if value else f"{description}が設定されていません"
            ))
        
        return results
    
    def validate_node_environment(self) -> List[ValidationResult]:
        """Node.js環境の検証"""
        results = []
        
        try:
            # Node.jsバージョン確認
            node_version = subprocess.check_output(['node', '--version'], text=True).strip()
            results.append(ValidationResult(
                name="Node.js Version",
                level=ValidationLevel.REQUIRED,
                status=True,
                message=f"Node.js {node_version} が利用可能です"
            ))
        except (subprocess.CalledProcessError, FileNotFoundError):
            results.append(ValidationResult(
                name="Node.js",
                level=ValidationLevel.REQUIRED,
                status=False,
                message="Node.jsが見つかりません",
                suggestion="actions/setup-node@v4 を使用してNode.js 18をセットアップしてください"
            ))
        
        try:
            # NPMバージョン確認
            npm_version = subprocess.check_output(['npm', '--version'], text=True).strip()
            results.append(ValidationResult(
                name="NPM Version",
                level=ValidationLevel.REQUIRED,
                status=True,
                message=f"NPM {npm_version} が利用可能です"
            ))
        except (subprocess.CalledProcessError, FileNotFoundError):
            results.append(ValidationResult(
                name="NPM",
                level=ValidationLevel.REQUIRED,
                status=False,
                message="NPMが見つかりません"
            ))
        
        return results
    
    def validate_python_environment(self) -> List[ValidationResult]:
        """Python環境の検証"""
        results = []
        
        try:
            # Pythonバージョン確認
            python_version = subprocess.check_output(['python', '--version'], text=True).strip()
            results.append(ValidationResult(
                name="Python Version",
                level=ValidationLevel.REQUIRED,
                status=True,
                message=f"{python_version} が利用可能です"
            ))
        except (subprocess.CalledProcessError, FileNotFoundError):
            results.append(ValidationResult(
                name="Python",
                level=ValidationLevel.REQUIRED,
                status=False,
                message="Pythonが見つかりません",
                suggestion="actions/setup-python@v4 を使用してPython 3.9をセットアップしてください"
            ))
        
        try:
            # pipバージョン確認
            pip_version = subprocess.check_output(['pip', '--version'], text=True).strip()
            results.append(ValidationResult(
                name="Pip Version",
                level=ValidationLevel.REQUIRED,
                status=True,
                message=f"{pip_version} が利用可能です"
            ))
        except (subprocess.CalledProcessError, FileNotFoundError):
            results.append(ValidationResult(
                name="Pip",
                level=ValidationLevel.REQUIRED,
                status=False,
                message="pipが見つかりません"
            ))
        
        return results
    
    def validate_sam_cli(self) -> List[ValidationResult]:
        """AWS SAM CLI の検証"""
        results = []
        
        try:
            sam_version = subprocess.check_output(['sam', '--version'], text=True).strip()
            results.append(ValidationResult(
                name="AWS SAM CLI",
                level=ValidationLevel.REQUIRED,
                status=True,
                message=f"{sam_version} が利用可能です"
            ))
        except (subprocess.CalledProcessError, FileNotFoundError):
            results.append(ValidationResult(
                name="AWS SAM CLI",
                level=ValidationLevel.REQUIRED,
                status=False,
                message="AWS SAM CLIが見つかりません",
                suggestion="aws-actions/setup-sam@v2 を使用してSAM CLIをセットアップしてください"
            ))
        
        return results
    
    def run_all_validations(self) -> List[ValidationResult]:
        """全ての検証を実行"""
        all_results = []
        
        print("🔍 CI/CD環境変数設定の検証を開始します...\n")
        
        # 各検証を実行
        validations = [
            ("AWS Secrets", self.validate_aws_secrets),
            ("Vercel Secrets", self.validate_vercel_secrets),
            ("Application Secrets", self.validate_application_secrets),
            ("GitHub Environment", self.validate_github_environment),
            ("Node.js Environment", self.validate_node_environment),
            ("Python Environment", self.validate_python_environment),
            ("AWS SAM CLI", self.validate_sam_cli),
        ]
        
        for category, validation_func in validations:
            print(f"📋 {category} の検証中...")
            results = validation_func()
            all_results.extend(results)
            
            # カテゴリ別結果表示
            for result in results:
                status_icon = "✅" if result.status else "❌"
                level_icon = {"required": "🔴", "recommended": "🟡", "optional": "🔵"}[result.level.value]
                print(f"  {status_icon} {level_icon} {result.name}: {result.message}")
                if result.suggestion:
                    print(f"    💡 {result.suggestion}")
            print()
        
        return all_results
    
    def generate_summary(self, results: List[ValidationResult]) -> Dict:
        """検証結果のサマリーを生成"""
        summary = {
            "total": len(results),
            "passed": sum(1 for r in results if r.status),
            "failed": sum(1 for r in results if not r.status),
            "by_level": {
                "required": {"total": 0, "passed": 0, "failed": 0},
                "recommended": {"total": 0, "passed": 0, "failed": 0},
                "optional": {"total": 0, "passed": 0, "failed": 0}
            },
            "critical_failures": []
        }
        
        for result in results:
            level = result.level.value
            summary["by_level"][level]["total"] += 1
            
            if result.status:
                summary["by_level"][level]["passed"] += 1
            else:
                summary["by_level"][level]["failed"] += 1
                
                # 必須項目の失敗は重要
                if result.level == ValidationLevel.REQUIRED:
                    summary["critical_failures"].append({
                        "name": result.name,
                        "message": result.message,
                        "suggestion": result.suggestion
                    })
        
        return summary
    
    def print_summary(self, results: List[ValidationResult]):
        """検証結果サマリーを出力"""
        summary = self.generate_summary(results)
        
        print("=" * 60)
        print("📊 検証結果サマリー")
        print("=" * 60)
        print(f"総検証項目数: {summary['total']}")
        print(f"✅ 成功: {summary['passed']}")
        print(f"❌ 失敗: {summary['failed']}")
        print()
        
        # レベル別サマリー
        for level, data in summary["by_level"].items():
            level_name = {"required": "必須", "recommended": "推奨", "optional": "オプション"}[level]
            if data["total"] > 0:
                print(f"{level_name}: {data['passed']}/{data['total']} 成功")
        
        print()
        
        # 重要な失敗項目
        if summary["critical_failures"]:
            print("🚨 重要な問題（必須項目の失敗）:")
            for failure in summary["critical_failures"]:
                print(f"  ❌ {failure['name']}: {failure['message']}")
                if failure['suggestion']:
                    print(f"    💡 {failure['suggestion']}")
            print()
        
        # 全体的な判定
        if summary["by_level"]["required"]["failed"] == 0:
            print("✅ 必須項目は全て設定されています。CI/CDパイプラインが正常に動作するはずです。")
        else:
            print("❌ 必須項目に不備があります。CI/CDパイプラインが正常に動作しない可能性があります。")
        
        return summary["by_level"]["required"]["failed"] == 0

def main():
    """メイン関数"""
    validator = CIEnvironmentValidator()
    
    try:
        results = validator.run_all_validations()
        success = validator.print_summary(results)
        
        # GitHub Actions Summary用のJSON出力
        if os.getenv('GITHUB_ACTIONS'):
            summary_data = validator.generate_summary(results)
            with open('ci-validation-summary.json', 'w') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            print("\n📄 GitHub Actions Summary用のデータを ci-validation-summary.json に出力しました。")
        
        # 終了コード
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ 検証中にエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()