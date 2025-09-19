#!/usr/bin/env python3
"""
Excel Unlocker 統合セットアップ診断ツール
セットアップ前後の環境診断、問題検出、解決提案を行う
"""

import os
import sys
import json
import subprocess
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import argparse


class SetupDiagnostics:
    """セットアップ診断クラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform.system(),
            'python_version': sys.version,
            'checks': {},
            'recommendations': [],
            'errors': [],
            'warnings': []
        }
    
    def run_command(self, command: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
        """コマンドを実行して結果を返す"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"コマンドがタイムアウトしました: {' '.join(command)}"
        except Exception as e:
            return False, "", str(e)
    
    def check_prerequisites(self) -> Dict[str, Any]:
        """前提条件のチェック"""
        print("🔍 前提条件をチェックしています...")
        
        tools = {
            'python3': ['python3', '--version'],
            'aws': ['aws', '--version'],
            'sam': ['sam', '--version'],
            'node': ['node', '--version'],
            'npm': ['npm', '--version'],
            'git': ['git', '--version']
        }
        
        results = {}
        
        for tool, command in tools.items():
            if shutil.which(command[0]):
                success, stdout, stderr = self.run_command(command)
                if success:
                    version = stdout.strip().split('\n')[0]
                    results[tool] = {
                        'installed': True,
                        'version': version,
                        'status': 'OK'
                    }
                    print(f"  ✅ {tool}: {version}")
                else:
                    results[tool] = {
                        'installed': True,
                        'version': 'unknown',
                        'status': 'ERROR',
                        'error': stderr
                    }
                    print(f"  ❌ {tool}: インストール済みだが実行エラー")
                    self.results['errors'].append(f"{tool}: {stderr}")
            else:
                results[tool] = {
                    'installed': False,
                    'status': 'MISSING'
                }
                print(f"  ❌ {tool}: インストールされていません")
                self.results['errors'].append(f"{tool}がインストールされていません")
        
        return results
    
    def check_aws_configuration(self) -> Dict[str, Any]:
        """AWS設定のチェック"""
        print("☁️  AWS設定をチェックしています...")
        
        results = {}
        
        # AWS CLI設定確認
        success, stdout, stderr = self.run_command(['aws', 'configure', 'list'])
        if success:
            results['config_list'] = {
                'status': 'OK',
                'output': stdout
            }
            print("  ✅ AWS CLI設定が確認できました")
        else:
            results['config_list'] = {
                'status': 'ERROR',
                'error': stderr
            }
            print("  ❌ AWS CLI設定に問題があります")
            self.results['errors'].append(f"AWS CLI設定エラー: {stderr}")
        
        # AWS認証確認
        success, stdout, stderr = self.run_command(['aws', 'sts', 'get-caller-identity'])
        if success:
            try:
                identity = json.loads(stdout)
                results['identity'] = {
                    'status': 'OK',
                    'user_id': identity.get('UserId', 'unknown'),
                    'account': identity.get('Account', 'unknown'),
                    'arn': identity.get('Arn', 'unknown')
                }
                print(f"  ✅ AWS認証OK: {identity.get('Arn', 'unknown')}")
            except json.JSONDecodeError:
                results['identity'] = {
                    'status': 'ERROR',
                    'error': 'JSON解析エラー'
                }
                print("  ❌ AWS認証レスポンスの解析に失敗")
        else:
            results['identity'] = {
                'status': 'ERROR',
                'error': stderr
            }
            print("  ❌ AWS認証に失敗")
            self.results['errors'].append(f"AWS認証エラー: {stderr}")
        
        return results
    
    def check_project_structure(self) -> Dict[str, Any]:
        """プロジェクト構造のチェック"""
        print("📁 プロジェクト構造をチェックしています...")
        
        required_files = [
            'setup-config.example.json',
            'config-schema.json',
            'template.yaml',
            'frontend/package.json',
            'backend/src/requirements.txt',
            'scripts/config_manager.py',
            'scripts/setup-config-manager.sh'
        ]
        
        required_dirs = [
            'frontend',
            'backend',
            'scripts',
            'docs'
        ]
        
        results = {
            'files': {},
            'directories': {}
        }
        
        # ファイルチェック
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                results['files'][file_path] = {
                    'exists': True,
                    'size': full_path.stat().st_size,
                    'status': 'OK'
                }
                print(f"  ✅ {file_path}")
            else:
                results['files'][file_path] = {
                    'exists': False,
                    'status': 'MISSING'
                }
                print(f"  ❌ {file_path}: ファイルが見つかりません")
                self.results['errors'].append(f"必須ファイルが見つかりません: {file_path}")
        
        # ディレクトリチェック
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists() and full_path.is_dir():
                results['directories'][dir_path] = {
                    'exists': True,
                    'status': 'OK'
                }
                print(f"  ✅ {dir_path}/")
            else:
                results['directories'][dir_path] = {
                    'exists': False,
                    'status': 'MISSING'
                }
                print(f"  ❌ {dir_path}/: ディレクトリが見つかりません")
                self.results['errors'].append(f"必須ディレクトリが見つかりません: {dir_path}")
        
        return results
    
    def check_configuration_files(self) -> Dict[str, Any]:
        """設定ファイルのチェック"""
        print("⚙️  設定ファイルをチェックしています...")
        
        results = {}
        
        # setup-config.json の確認
        setup_config_path = self.project_root / 'setup-config.json'
        if setup_config_path.exists():
            try:
                with open(setup_config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                results['setup_config'] = {
                    'exists': True,
                    'valid_json': True,
                    'status': 'OK'
                }
                
                # 基本構造チェック
                required_keys = ['version', 'environments']
                missing_keys = [key for key in required_keys if key not in config_data]
                
                if missing_keys:
                    results['setup_config']['missing_keys'] = missing_keys
                    results['setup_config']['status'] = 'INCOMPLETE'
                    print(f"  ⚠️  setup-config.json: 必須キーが不足 {missing_keys}")
                    self.results['warnings'].append(f"設定ファイルに必須キーが不足: {missing_keys}")
                else:
                    print("  ✅ setup-config.json: 基本構造OK")
                
                # 環境設定チェック
                environments = config_data.get('environments', {})
                for env in ['development', 'staging', 'production']:
                    if env in environments:
                        env_config = environments[env]
                        
                        # プレースホルダーチェック
                        placeholders = []
                        if 'google' in env_config:
                            google_config = env_config['google']
                            if google_config.get('clientSecret', '').startswith('YOUR_'):
                                placeholders.append('Google Client Secret')
                        
                        if 'security' in env_config:
                            security_config = env_config['security']
                            if security_config.get('jwtSecret', '').startswith('YOUR_'):
                                placeholders.append('JWT Secret')
                            if security_config.get('sessionSecret', '').startswith('YOUR_'):
                                placeholders.append('Session Secret')
                        
                        if placeholders:
                            results['setup_config'][f'{env}_placeholders'] = placeholders
                            print(f"  ⚠️  {env}環境: プレースホルダーが残っています {placeholders}")
                            self.results['warnings'].append(f"{env}環境にプレースホルダーが残っています: {placeholders}")
                        else:
                            print(f"  ✅ {env}環境: 設定完了")
                    else:
                        print(f"  ❌ {env}環境: 設定が見つかりません")
                        self.results['errors'].append(f"{env}環境の設定が見つかりません")
                
            except json.JSONDecodeError as e:
                results['setup_config'] = {
                    'exists': True,
                    'valid_json': False,
                    'status': 'ERROR',
                    'error': str(e)
                }
                print(f"  ❌ setup-config.json: JSON形式エラー {e}")
                self.results['errors'].append(f"設定ファイルのJSON形式エラー: {e}")
            
            except Exception as e:
                results['setup_config'] = {
                    'exists': True,
                    'status': 'ERROR',
                    'error': str(e)
                }
                print(f"  ❌ setup-config.json: 読み込みエラー {e}")
                self.results['errors'].append(f"設定ファイルの読み込みエラー: {e}")
        else:
            results['setup_config'] = {
                'exists': False,
                'status': 'MISSING'
            }
            print("  ⚠️  setup-config.json: ファイルが見つかりません（初回セットアップ時は正常）")
            self.results['warnings'].append("設定ファイルが見つかりません（初回セットアップ時は正常）")
        
        return results
    
    def check_dependencies(self) -> Dict[str, Any]:
        """依存関係のチェック"""
        print("📦 依存関係をチェックしています...")
        
        results = {}
        
        # Python依存関係
        requirements_path = self.project_root / 'scripts' / 'requirements.txt'
        if requirements_path.exists():
            success, stdout, stderr = self.run_command([
                'pip3', 'install', '--dry-run', '-r', str(requirements_path)
            ])
            
            results['python_requirements'] = {
                'file_exists': True,
                'installable': success,
                'status': 'OK' if success else 'ERROR'
            }
            
            if success:
                print("  ✅ Python依存関係: インストール可能")
            else:
                print(f"  ❌ Python依存関係: インストールエラー")
                self.results['errors'].append(f"Python依存関係エラー: {stderr}")
        else:
            results['python_requirements'] = {
                'file_exists': False,
                'status': 'MISSING'
            }
            print("  ❌ scripts/requirements.txt が見つかりません")
            self.results['errors'].append("Python依存関係ファイルが見つかりません")
        
        # Node.js依存関係
        package_json_path = self.project_root / 'frontend' / 'package.json'
        if package_json_path.exists():
            # package.jsonの読み込み
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                results['node_package'] = {
                    'file_exists': True,
                    'valid_json': True,
                    'dependencies_count': len(package_data.get('dependencies', {})),
                    'dev_dependencies_count': len(package_data.get('devDependencies', {})),
                    'status': 'OK'
                }
                print(f"  ✅ frontend/package.json: 依存関係 {results['node_package']['dependencies_count']}個")
                
            except json.JSONDecodeError as e:
                results['node_package'] = {
                    'file_exists': True,
                    'valid_json': False,
                    'status': 'ERROR',
                    'error': str(e)
                }
                print(f"  ❌ frontend/package.json: JSON形式エラー")
                self.results['errors'].append(f"package.jsonのJSON形式エラー: {e}")
        else:
            results['node_package'] = {
                'file_exists': False,
                'status': 'MISSING'
            }
            print("  ❌ frontend/package.json が見つかりません")
            self.results['errors'].append("Node.js依存関係ファイルが見つかりません")
        
        return results
    
    def check_network_connectivity(self) -> Dict[str, Any]:
        """ネットワーク接続のチェック"""
        print("🌐 ネットワーク接続をチェックしています...")
        
        results = {}
        
        # 重要なエンドポイントのチェック
        endpoints = {
            'aws_api': 'https://sts.amazonaws.com',
            'google_oauth': 'https://accounts.google.com',
            'vercel_api': 'https://api.vercel.com',
            'npm_registry': 'https://registry.npmjs.org',
            'pypi': 'https://pypi.org'
        }
        
        for name, url in endpoints.items():
            success, stdout, stderr = self.run_command([
                'curl', '-s', '--max-time', '10', '--head', url
            ])
            
            results[name] = {
                'url': url,
                'accessible': success,
                'status': 'OK' if success else 'ERROR'
            }
            
            if success:
                print(f"  ✅ {name}: 接続OK")
            else:
                print(f"  ⚠️  {name}: 接続エラー（ネットワーク環境による）")
                self.results['warnings'].append(f"ネットワーク接続エラー: {name} ({url})")
        
        return results
    
    def generate_recommendations(self) -> List[str]:
        """推奨事項の生成"""
        recommendations = []
        
        # エラーベースの推奨事項
        if self.results['errors']:
            recommendations.append("🔧 エラーが検出されました。以下の解決方法を試してください:")
            
            for error in self.results['errors']:
                if 'python3' in error.lower():
                    recommendations.append("  - Python 3.x をインストール: https://www.python.org/downloads/")
                elif 'aws' in error.lower():
                    recommendations.append("  - AWS CLI をインストール・設定: aws configure")
                elif 'sam' in error.lower():
                    recommendations.append("  - SAM CLI をインストール: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html")
                elif 'node' in error.lower():
                    recommendations.append("  - Node.js をインストール: https://nodejs.org/")
                elif 'git' in error.lower():
                    recommendations.append("  - Git をインストール: https://git-scm.com/")
                elif 'setup-config.json' in error:
                    recommendations.append("  - 設定ファイルを作成: ./scripts/setup-config-manager.sh init")
                elif 'プレースホルダー' in error:
                    recommendations.append("  - 設定ファイルの機密情報を設定してください")
        
        # 警告ベースの推奨事項
        if self.results['warnings']:
            recommendations.append("⚠️  警告が検出されました。以下を確認してください:")
            
            for warning in self.results['warnings']:
                if 'プレースホルダー' in warning:
                    recommendations.append("  - Google OAuth設定、JWT/セッションシークレットを設定")
                elif 'ネットワーク' in warning:
                    recommendations.append("  - インターネット接続とファイアウォール設定を確認")
        
        # 一般的な推奨事項
        if not self.results['errors']:
            recommendations.extend([
                "✅ 基本的な前提条件は満たされています",
                "📚 詳細なセットアップ手順: docs/beginner-complete-setup-guide.md",
                "🚀 統合セットアップの実行: ./scripts/setup-integrated-deployment.sh"
            ])
        
        return recommendations
    
    def run_full_diagnostics(self) -> Dict[str, Any]:
        """完全診断の実行"""
        print("🔍 Excel Unlocker セットアップ診断を開始します...\n")
        
        # 各種チェックの実行
        self.results['checks']['prerequisites'] = self.check_prerequisites()
        print()
        
        self.results['checks']['aws_configuration'] = self.check_aws_configuration()
        print()
        
        self.results['checks']['project_structure'] = self.check_project_structure()
        print()
        
        self.results['checks']['configuration_files'] = self.check_configuration_files()
        print()
        
        self.results['checks']['dependencies'] = self.check_dependencies()
        print()
        
        self.results['checks']['network_connectivity'] = self.check_network_connectivity()
        print()
        
        # 推奨事項の生成
        self.results['recommendations'] = self.generate_recommendations()
        
        return self.results
    
    def print_summary(self):
        """診断結果サマリーの表示"""
        print("=" * 70)
        print("📊 診断結果サマリー")
        print("=" * 70)
        
        # エラー数・警告数
        error_count = len(self.results['errors'])
        warning_count = len(self.results['warnings'])
        
        if error_count == 0 and warning_count == 0:
            print("🎉 すべてのチェックが正常に完了しました！")
        else:
            print(f"❌ エラー: {error_count}個")
            print(f"⚠️  警告: {warning_count}個")
        
        print()
        
        # 推奨事項の表示
        if self.results['recommendations']:
            print("💡 推奨事項:")
            for recommendation in self.results['recommendations']:
                print(f"   {recommendation}")
            print()
        
        # 次のステップ
        if error_count == 0:
            print("🚀 次のステップ:")
            print("   1. 統合セットアップの実行: ./scripts/setup-integrated-deployment.sh")
            print("   2. または簡易セットアップ: ./setup-easy.sh")
        else:
            print("🔧 まず上記のエラーを解決してから、セットアップを実行してください")
        
        print()
        print("📚 参考ドキュメント:")
        print("   - docs/index.md - 全ドキュメント索引")
        print("   - docs/beginner-complete-setup-guide.md - 初心者向けガイド")
        print("   - docs/troubleshooting-flowchart.md - トラブルシューティング")
    
    def save_report(self, output_file: str):
        """診断レポートの保存"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 診断レポートを保存しました: {output_file}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Excel Unlocker セットアップ診断ツール")
    parser.add_argument('--output', '-o', help='診断レポートの出力ファイル')
    parser.add_argument('--quiet', '-q', action='store_true', help='サマリーのみ表示')
    
    args = parser.parse_args()
    
    # 診断実行
    diagnostics = SetupDiagnostics()
    
    if not args.quiet:
        results = diagnostics.run_full_diagnostics()
    else:
        # 静かモード（基本チェックのみ）
        results = {
            'checks': {
                'prerequisites': diagnostics.check_prerequisites()
            }
        }
        diagnostics.results = results
    
    # サマリー表示
    diagnostics.print_summary()
    
    # レポート保存
    if args.output:
        diagnostics.save_report(args.output)
    
    # 終了コード
    error_count = len(diagnostics.results.get('errors', []))
    sys.exit(1 if error_count > 0 else 0)


if __name__ == '__main__':
    main()