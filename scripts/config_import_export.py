#!/usr/bin/env python3
"""
設定ファイルのインポート・エクスポート機能
異なる環境間での設定移行や、設定の部分的な更新を支援
"""

import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml


class ConfigImportExport:
    """設定インポート・エクスポート管理クラス"""
    
    def __init__(self, config_path: str = "setup-config.json"):
        self.config_path = Path(config_path)
        
    def export_environment(self, environment: str, output_file: str, format: str = 'json') -> bool:
        """特定環境の設定をエクスポート"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if environment not in config.get('environments', {}):
            raise ValueError(f"環境 '{environment}' が設定ファイルに存在しません")
        
        export_data = {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'environment': environment,
                'source_version': config.get('version', '1.0.0')
            },
            'environment_config': config['environments'][environment],
            'global_settings': {
                'features': config.get('features', {}),
                'limits': config.get('limits', {}),
                'logging': config.get('logging', {})
            }
        }
        
        output_path = Path(output_file)
        
        if format.lower() == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        elif format.lower() == 'yaml':
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"サポートされていないフォーマット: {format}")
        
        print(f"✅ {environment}環境の設定をエクスポートしました: {output_path}")
        return True
    
    def import_environment(self, import_file: str, target_environment: str, 
                          merge_mode: str = 'replace') -> bool:
        """設定ファイルから環境設定をインポート"""
        import_path = Path(import_file)
        
        if not import_path.exists():
            raise FileNotFoundError(f"インポートファイルが見つかりません: {import_path}")
        
        # インポートデータの読み込み
        if import_path.suffix.lower() == '.json':
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
        elif import_path.suffix.lower() in ['.yaml', '.yml']:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = yaml.safe_load(f)
        else:
            raise ValueError(f"サポートされていないファイル形式: {import_path.suffix}")
        
        # 現在の設定ファイルの読み込み
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                current_config = json.load(f)
        else:
            # 設定ファイルが存在しない場合は基本構造を作成
            current_config = {
                'version': '1.0.0',
                'environments': {},
                'features': {},
                'limits': {},
                'logging': {}
            }
        
        # 環境設定のマージ
        if merge_mode == 'replace':
            current_config['environments'][target_environment] = import_data['environment_config']
        elif merge_mode == 'merge':
            if target_environment not in current_config['environments']:
                current_config['environments'][target_environment] = {}
            self._deep_merge(current_config['environments'][target_environment], 
                           import_data['environment_config'])
        else:
            raise ValueError(f"サポートされていないマージモード: {merge_mode}")
        
        # グローバル設定のマージ（オプション）
        if 'global_settings' in import_data:
            global_settings = import_data['global_settings']
            for key in ['features', 'limits', 'logging']:
                if key in global_settings:
                    if merge_mode == 'replace':
                        current_config[key] = global_settings[key]
                    elif merge_mode == 'merge':
                        self._deep_merge(current_config[key], global_settings[key])
        
        # メタデータの更新
        current_config['metadata'] = current_config.get('metadata', {})
        current_config['metadata']['lastModified'] = datetime.now().strftime('%Y-%m-%d')
        
        # 設定ファイルの保存
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(current_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ {target_environment}環境の設定をインポートしました")
        return True
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """辞書の深いマージ"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def export_secrets_template(self, environment: str, output_file: str) -> bool:
        """機密情報のテンプレートをエクスポート"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if environment not in config.get('environments', {}):
            raise ValueError(f"環境 '{environment}' が設定ファイルに存在しません")
        
        env_config = config['environments'][environment]
        
        # 機密情報のテンプレート作成
        secrets_template = {
            'metadata': {
                'description': f'{environment}環境の機密情報テンプレート',
                'created_at': datetime.now().isoformat(),
                'environment': environment
            },
            'secrets': {
                'google_oauth': {
                    'client_id': env_config.get('google', {}).get('clientId', 'YOUR_GOOGLE_CLIENT_ID'),
                    'client_secret': 'YOUR_GOOGLE_CLIENT_SECRET'
                },
                'security': {
                    'jwt_secret': 'YOUR_JWT_SECRET',
                    'session_secret': 'YOUR_SESSION_SECRET'
                },
                'aws': {
                    'profile': env_config.get('aws', {}).get('profile', 'default'),
                    'region': env_config.get('aws', {}).get('region', 'ap-northeast-1')
                }
            },
            'instructions': {
                'google_oauth': 'Google Cloud Consoleで取得したOAuth 2.0クライアントIDとシークレット',
                'jwt_secret': '32文字以上のランダムな文字列（JWT署名用）',
                'session_secret': '32文字以上のランダムな文字列（セッション暗号化用）',
                'aws_profile': 'AWS CLIプロファイル名（aws configure --profile で設定）'
            }
        }
        
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(secrets_template, f, indent=2, ensure_ascii=False)
        
        print(f"✅ {environment}環境の機密情報テンプレートをエクスポートしました: {output_path}")
        return True
    
    def import_secrets(self, secrets_file: str, target_environment: str) -> bool:
        """機密情報をインポート"""
        secrets_path = Path(secrets_file)
        
        if not secrets_path.exists():
            raise FileNotFoundError(f"機密情報ファイルが見つかりません: {secrets_path}")
        
        with open(secrets_path, 'r', encoding='utf-8') as f:
            secrets_data = json.load(f)
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if target_environment not in config.get('environments', {}):
            raise ValueError(f"環境 '{target_environment}' が設定ファイルに存在しません")
        
        # 機密情報の更新
        env_config = config['environments'][target_environment]
        secrets = secrets_data.get('secrets', {})
        
        if 'google_oauth' in secrets:
            google_secrets = secrets['google_oauth']
            if 'google' not in env_config:
                env_config['google'] = {}
            if 'client_id' in google_secrets:
                env_config['google']['clientId'] = google_secrets['client_id']
            if 'client_secret' in google_secrets:
                env_config['google']['clientSecret'] = google_secrets['client_secret']
        
        if 'security' in secrets:
            security_secrets = secrets['security']
            if 'security' not in env_config:
                env_config['security'] = {}
            if 'jwt_secret' in security_secrets:
                env_config['security']['jwtSecret'] = security_secrets['jwt_secret']
            if 'session_secret' in security_secrets:
                env_config['security']['sessionSecret'] = security_secrets['session_secret']
        
        if 'aws' in secrets:
            aws_secrets = secrets['aws']
            if 'aws' not in env_config:
                env_config['aws'] = {}
            if 'profile' in aws_secrets:
                env_config['aws']['profile'] = aws_secrets['profile']
            if 'region' in aws_secrets:
                env_config['aws']['region'] = aws_secrets['region']
        
        # メタデータの更新
        config['metadata'] = config.get('metadata', {})
        config['metadata']['lastModified'] = datetime.now().strftime('%Y-%m-%d')
        
        # 設定ファイルの保存
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ {target_environment}環境に機密情報をインポートしました")
        return True
    
    def list_environments(self) -> List[str]:
        """設定ファイル内の環境一覧を取得"""
        if not self.config_path.exists():
            return []
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return list(config.get('environments', {}).keys())
    
    def compare_environments(self, env1: str, env2: str) -> Dict[str, Any]:
        """2つの環境設定を比較"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        environments = config.get('environments', {})
        
        if env1 not in environments:
            raise ValueError(f"環境 '{env1}' が設定ファイルに存在しません")
        if env2 not in environments:
            raise ValueError(f"環境 '{env2}' が設定ファイルに存在しません")
        
        config1 = environments[env1]
        config2 = environments[env2]
        
        differences = self._find_differences(config1, config2, f"{env1} vs {env2}")
        
        return {
            'environment1': env1,
            'environment2': env2,
            'differences': differences,
            'comparison_date': datetime.now().isoformat()
        }
    
    def _find_differences(self, dict1: Dict[str, Any], dict2: Dict[str, Any], 
                         path: str = "") -> List[Dict[str, Any]]:
        """2つの辞書の差分を検出"""
        differences = []
        
        all_keys = set(dict1.keys()) | set(dict2.keys())
        
        for key in all_keys:
            current_path = f"{path}.{key}" if path else key
            
            if key not in dict1:
                differences.append({
                    'type': 'missing_in_first',
                    'path': current_path,
                    'value_in_second': dict2[key]
                })
            elif key not in dict2:
                differences.append({
                    'type': 'missing_in_second',
                    'path': current_path,
                    'value_in_first': dict1[key]
                })
            elif isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                differences.extend(self._find_differences(dict1[key], dict2[key], current_path))
            elif dict1[key] != dict2[key]:
                differences.append({
                    'type': 'different_values',
                    'path': current_path,
                    'value_in_first': dict1[key],
                    'value_in_second': dict2[key]
                })
        
        return differences


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="設定インポート・エクスポートツール")
    subparsers = parser.add_subparsers(dest='command', help='利用可能なコマンド')
    
    # export-env コマンド
    export_parser = subparsers.add_parser('export-env', help='環境設定のエクスポート')
    export_parser.add_argument('environment', help='エクスポートする環境名')
    export_parser.add_argument('output_file', help='出力ファイルパス')
    export_parser.add_argument('--format', choices=['json', 'yaml'], default='json', help='出力フォーマット')
    export_parser.add_argument('--config', default='setup-config.json', help='設定ファイルのパス')
    
    # import-env コマンド
    import_parser = subparsers.add_parser('import-env', help='環境設定のインポート')
    import_parser.add_argument('import_file', help='インポートファイルパス')
    import_parser.add_argument('target_environment', help='インポート先環境名')
    import_parser.add_argument('--merge', choices=['replace', 'merge'], default='replace', help='マージモード')
    import_parser.add_argument('--config', default='setup-config.json', help='設定ファイルのパス')
    
    # export-secrets コマンド
    secrets_export_parser = subparsers.add_parser('export-secrets', help='機密情報テンプレートのエクスポート')
    secrets_export_parser.add_argument('environment', help='対象環境名')
    secrets_export_parser.add_argument('output_file', help='出力ファイルパス')
    secrets_export_parser.add_argument('--config', default='setup-config.json', help='設定ファイルのパス')
    
    # import-secrets コマンド
    secrets_import_parser = subparsers.add_parser('import-secrets', help='機密情報のインポート')
    secrets_import_parser.add_argument('secrets_file', help='機密情報ファイルパス')
    secrets_import_parser.add_argument('target_environment', help='インポート先環境名')
    secrets_import_parser.add_argument('--config', default='setup-config.json', help='設定ファイルのパス')
    
    # list コマンド
    list_parser = subparsers.add_parser('list', help='環境一覧の表示')
    list_parser.add_argument('--config', default='setup-config.json', help='設定ファイルのパス')
    
    # compare コマンド
    compare_parser = subparsers.add_parser('compare', help='環境設定の比較')
    compare_parser.add_argument('env1', help='比較する環境1')
    compare_parser.add_argument('env2', help='比較する環境2')
    compare_parser.add_argument('--output', help='比較結果の出力ファイル')
    compare_parser.add_argument('--config', default='setup-config.json', help='設定ファイルのパス')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        config_manager = ConfigImportExport(args.config if hasattr(args, 'config') else 'setup-config.json')
        
        if args.command == 'export-env':
            config_manager.export_environment(args.environment, args.output_file, args.format)
        
        elif args.command == 'import-env':
            config_manager.import_environment(args.import_file, args.target_environment, args.merge)
        
        elif args.command == 'export-secrets':
            config_manager.export_secrets_template(args.environment, args.output_file)
        
        elif args.command == 'import-secrets':
            config_manager.import_secrets(args.secrets_file, args.target_environment)
        
        elif args.command == 'list':
            environments = config_manager.list_environments()
            if environments:
                print("利用可能な環境:")
                for env in environments:
                    print(f"  - {env}")
            else:
                print("設定ファイルに環境が定義されていません")
        
        elif args.command == 'compare':
            comparison = config_manager.compare_environments(args.env1, args.env2)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(comparison, f, indent=2, ensure_ascii=False)
                print(f"✅ 比較結果を出力しました: {args.output}")
            else:
                print(f"\n=== {args.env1} vs {args.env2} の比較結果 ===")
                differences = comparison['differences']
                if not differences:
                    print("✅ 設定に差異はありません")
                else:
                    for diff in differences:
                        print(f"\n📍 {diff['path']}")
                        if diff['type'] == 'missing_in_first':
                            print(f"  {args.env1}に存在しない設定: {diff['value_in_second']}")
                        elif diff['type'] == 'missing_in_second':
                            print(f"  {args.env2}に存在しない設定: {diff['value_in_first']}")
                        elif diff['type'] == 'different_values':
                            print(f"  {args.env1}: {diff['value_in_first']}")
                            print(f"  {args.env2}: {diff['value_in_second']}")
    
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()