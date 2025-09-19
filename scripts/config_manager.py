#!/usr/bin/env python3
"""
設定情報管理システム
機密情報を含む設定ファイルの管理、検証、環境変数生成を行う
"""

import json
import os
import sys
import argparse
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import jsonschema
from cryptography.fernet import Fernet
import base64


class ConfigManager:
    """設定ファイル管理クラス"""
    
    def __init__(self, config_path: str = "setup-config.json"):
        self.config_path = Path(config_path)
        self.schema_path = Path("config-schema.json")
        self.example_path = Path("setup-config.example.json")
        self.encryption_key_path = Path(".config-encryption-key")
        
    def validate_config(self, config_data: Dict[str, Any]) -> List[str]:
        """設定ファイルの検証"""
        errors = []
        
        try:
            # JSON Schemaによる検証
            if self.schema_path.exists():
                with open(self.schema_path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                jsonschema.validate(config_data, schema)
                print("✅ JSON Schema検証: 成功")
            else:
                errors.append("⚠️  config-schema.jsonが見つかりません")
                
        except jsonschema.ValidationError as e:
            errors.append(f"❌ JSON Schema検証エラー: {e.message}")
        except Exception as e:
            errors.append(f"❌ 検証エラー: {str(e)}")
            
        # カスタム検証
        errors.extend(self._custom_validation(config_data))
        
        return errors
    
    def _custom_validation(self, config_data: Dict[str, Any]) -> List[str]:
        """カスタム検証ルール"""
        errors = []
        
        # 必須環境の存在確認
        required_envs = ['development', 'staging', 'production']
        environments = config_data.get('environments', {})
        
        for env in required_envs:
            if env not in environments:
                errors.append(f"❌ 必須環境 '{env}' が定義されていません")
                continue
                
            env_config = environments[env]
            
            # 機密情報のプレースホルダーチェック
            secrets = [
                env_config.get('google', {}).get('clientSecret'),
                env_config.get('security', {}).get('jwtSecret'),
                env_config.get('security', {}).get('sessionSecret')
            ]
            
            for secret in secrets:
                if secret and secret.startswith('YOUR_'):
                    errors.append(f"⚠️  {env}環境: プレースホルダーが残っています: {secret}")
            
            # 許可ユーザーの確認
            allowed_users = env_config.get('security', {}).get('allowedUsers', [])
            if not allowed_users:
                errors.append(f"❌ {env}環境: 許可ユーザーが設定されていません")
            elif env == 'production' and any('@example.com' in user for user in allowed_users):
                errors.append(f"⚠️  {env}環境: example.comドメインのユーザーが含まれています")
        
        return errors
    
    def load_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """設定ファイルの読み込み"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        if environment:
            if environment not in config.get('environments', {}):
                raise ValueError(f"環境 '{environment}' が設定ファイルに存在しません")
            return config['environments'][environment]
            
        return config
    
    def generate_env_vars(self, environment: str, output_format: str = 'bash') -> str:
        """環境変数の生成"""
        config = self.load_config()
        env_config = config['environments'][environment]
        
        env_vars = {}
        
        # AWS設定
        aws_config = env_config['aws']
        env_vars.update({
            'AWS_REGION': aws_config['region'],
            'S3_BUCKET_NAME': aws_config['s3']['bucketName'],
            'CORS_ORIGIN': aws_config['s3']['corsOrigin'],
            'LAMBDA_STACK_NAME': aws_config['lambda']['stackName'],
            'LAMBDA_TIMEOUT': str(aws_config['lambda']['timeout']),
            'LAMBDA_MEMORY_SIZE': str(aws_config['lambda']['memorySize'])
        })
        
        if 'profile' in aws_config:
            env_vars['AWS_PROFILE'] = aws_config['profile']
        
        # Google OAuth設定
        google_config = env_config['google']
        env_vars.update({
            'GOOGLE_CLIENT_ID': google_config['clientId'],
            'GOOGLE_CLIENT_SECRET': google_config['clientSecret'],
            'NEXTAUTH_URL': google_config['redirectUri'].replace('/api/auth/callback/google', '')
        })
        
        # Vercel設定
        vercel_config = env_config['vercel']
        env_vars.update({
            'VERCEL_PROJECT_NAME': vercel_config['projectName']
        })
        
        if 'domain' in vercel_config:
            env_vars['VERCEL_DOMAIN'] = vercel_config['domain']
        
        # セキュリティ設定
        security_config = env_config['security']
        env_vars.update({
            'ALLOWED_USERS': ','.join(security_config['allowedUsers']),
            'NEXTAUTH_SECRET': security_config.get('sessionSecret', ''),
            'JWT_SECRET': security_config.get('jwtSecret', '')
        })
        
        # 機能設定
        features = config.get('features', {})
        env_vars.update({
            'NEXT_PUBLIC_GOOGLE_DRIVE_ENABLED': str(features.get('googleDriveIntegration', True)).lower(),
            'NEXT_PUBLIC_MULTI_FILE_ENABLED': str(features.get('multiFileProcessing', True)).lower(),
            'NEXT_PUBLIC_USE_MOCK_API': str(features.get('mockMode', False)).lower()
        })
        
        # 制限設定
        limits = config.get('limits', {})
        env_vars.update({
            'MAX_FILE_SIZE': str(limits.get('maxFileSize', 20971520)),
            'MAX_FILES_PER_BATCH': str(limits.get('maxFilesPerBatch', 10)),
            'UPLOAD_TIMEOUT': str(limits.get('uploadTimeout', 60)),
            'DOWNLOAD_TIMEOUT': str(limits.get('downloadTimeout', 300))
        })
        
        # ログ設定
        logging_config = config.get('logging', {})
        env_vars.update({
            'LOG_LEVEL': logging_config.get('level', 'INFO'),
            'CLOUDWATCH_ENABLED': str(logging_config.get('enableCloudWatch', True)).lower(),
            'LOG_RETENTION_DAYS': str(logging_config.get('retentionDays', 30))
        })
        
        # フォーマット別出力
        if output_format == 'bash':
            return self._format_bash_env(env_vars)
        elif output_format == 'json':
            return json.dumps(env_vars, indent=2, ensure_ascii=False)
        elif output_format == 'dotenv':
            return self._format_dotenv(env_vars)
        else:
            raise ValueError(f"サポートされていない出力フォーマット: {output_format}")
    
    def _format_bash_env(self, env_vars: Dict[str, str]) -> str:
        """Bash形式の環境変数出力"""
        lines = ["#!/bin/bash", "# 自動生成された環境変数設定", ""]
        for key, value in env_vars.items():
            # 特殊文字をエスケープ
            escaped_value = value.replace('"', '\\"').replace('$', '\\$')
            lines.append(f'export {key}="{escaped_value}"')
        return '\n'.join(lines)
    
    def _format_dotenv(self, env_vars: Dict[str, str]) -> str:
        """.env形式の環境変数出力"""
        lines = ["# 自動生成された環境変数設定", ""]
        for key, value in env_vars.items():
            lines.append(f'{key}={value}')
        return '\n'.join(lines)
    
    def create_from_template(self) -> bool:
        """テンプレートから設定ファイルを作成"""
        if self.config_path.exists():
            response = input(f"設定ファイル {self.config_path} が既に存在します。上書きしますか？ (y/N): ")
            if response.lower() != 'y':
                print("作成をキャンセルしました。")
                return False
        
        if not self.example_path.exists():
            print(f"❌ テンプレートファイルが見つかりません: {self.example_path}")
            return False
        
        shutil.copy2(self.example_path, self.config_path)
        print(f"✅ 設定ファイルを作成しました: {self.config_path}")
        print("⚠️  機密情報（パスワード、シークレット等）を設定してください。")
        return True
    
    def backup_config(self, backup_dir: str = "config-backup") -> str:
        """設定ファイルのバックアップ"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        
        backup_path = Path(backup_dir)
        backup_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"setup-config.{timestamp}.json"
        
        shutil.copy2(self.config_path, backup_file)
        print(f"✅ バックアップを作成しました: {backup_file}")
        return str(backup_file)
    
    def encrypt_config(self, password: Optional[str] = None) -> str:
        """設定ファイルの暗号化"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        
        # 暗号化キーの生成または読み込み
        if self.encryption_key_path.exists():
            with open(self.encryption_key_path, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.encryption_key_path, 'wb') as f:
                f.write(key)
            print(f"✅ 暗号化キーを生成しました: {self.encryption_key_path}")
        
        # ファイルの暗号化
        fernet = Fernet(key)
        
        with open(self.config_path, 'rb') as f:
            data = f.read()
        
        encrypted_data = fernet.encrypt(data)
        encrypted_file = self.config_path.with_suffix('.json.encrypted')
        
        with open(encrypted_file, 'wb') as f:
            f.write(encrypted_data)
        
        print(f"✅ 設定ファイルを暗号化しました: {encrypted_file}")
        return str(encrypted_file)
    
    def decrypt_config(self, encrypted_file: str) -> str:
        """設定ファイルの復号化"""
        if not self.encryption_key_path.exists():
            raise FileNotFoundError(f"暗号化キーが見つかりません: {self.encryption_key_path}")
        
        with open(self.encryption_key_path, 'rb') as f:
            key = f.read()
        
        fernet = Fernet(key)
        
        with open(encrypted_file, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = fernet.decrypt(encrypted_data)
        
        with open(self.config_path, 'wb') as f:
            f.write(decrypted_data)
        
        print(f"✅ 設定ファイルを復号化しました: {self.config_path}")
        return str(self.config_path)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="設定情報管理システム")
    subparsers = parser.add_subparsers(dest='command', help='利用可能なコマンド')
    
    # validate コマンド
    validate_parser = subparsers.add_parser('validate', help='設定ファイルの検証')
    validate_parser.add_argument('--config', default='setup-config.json', help='設定ファイルのパス')
    
    # generate-env コマンド
    env_parser = subparsers.add_parser('generate-env', help='環境変数の生成')
    env_parser.add_argument('environment', choices=['development', 'staging', 'production'], help='対象環境')
    env_parser.add_argument('--format', choices=['bash', 'json', 'dotenv'], default='bash', help='出力フォーマット')
    env_parser.add_argument('--output', help='出力ファイル（指定しない場合は標準出力）')
    env_parser.add_argument('--config', default='setup-config.json', help='設定ファイルのパス')
    
    # create コマンド
    create_parser = subparsers.add_parser('create', help='テンプレートから設定ファイルを作成')
    create_parser.add_argument('--config', default='setup-config.json', help='設定ファイルのパス')
    
    # backup コマンド
    backup_parser = subparsers.add_parser('backup', help='設定ファイルのバックアップ')
    backup_parser.add_argument('--config', default='setup-config.json', help='設定ファイルのパス')
    backup_parser.add_argument('--dir', default='config-backup', help='バックアップディレクトリ')
    
    # encrypt コマンド
    encrypt_parser = subparsers.add_parser('encrypt', help='設定ファイルの暗号化')
    encrypt_parser.add_argument('--config', default='setup-config.json', help='設定ファイルのパス')
    
    # decrypt コマンド
    decrypt_parser = subparsers.add_parser('decrypt', help='設定ファイルの復号化')
    decrypt_parser.add_argument('encrypted_file', help='暗号化されたファイルのパス')
    decrypt_parser.add_argument('--config', default='setup-config.json', help='出力する設定ファイルのパス')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        config_manager = ConfigManager(args.config if hasattr(args, 'config') else 'setup-config.json')
        
        if args.command == 'validate':
            config_data = config_manager.load_config()
            errors = config_manager.validate_config(config_data)
            
            if errors:
                print("❌ 設定ファイルに問題があります:")
                for error in errors:
                    print(f"  {error}")
                sys.exit(1)
            else:
                print("✅ 設定ファイルは正常です")
        
        elif args.command == 'generate-env':
            env_output = config_manager.generate_env_vars(args.environment, args.format)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(env_output)
                print(f"✅ 環境変数を出力しました: {args.output}")
            else:
                print(env_output)
        
        elif args.command == 'create':
            config_manager.create_from_template()
        
        elif args.command == 'backup':
            config_manager.backup_config(args.dir)
        
        elif args.command == 'encrypt':
            config_manager.encrypt_config()
        
        elif args.command == 'decrypt':
            config_manager.decrypt_config(args.encrypted_file)
    
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()