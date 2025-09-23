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
import secrets
import string
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
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
        
        # プレースホルダーパターン
        self.placeholder_patterns = [
            r'YOUR_[A-Z_]+',
            r'REPLACE_[A-Z_]+',
            r'CHANGE_[A-Z_]+',
            r'UPDATE_[A-Z_]+',
            r'SET_[A-Z_]+',
            r'example\.com',
            r'developer@example\.com',
            r'user\d+@example\.com'
        ]
        
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
            
            # プレースホルダーの包括的チェック
            placeholders = self.find_placeholders(env_config)
            for placeholder_info in placeholders:
                errors.append(f"⚠️  {env}環境: プレースホルダーが残っています: {placeholder_info['path']} = {placeholder_info['value']}")
            
            # 許可ユーザーの確認
            allowed_users = env_config.get('security', {}).get('allowedUsers', [])
            if not allowed_users:
                errors.append(f"❌ {env}環境: 許可ユーザーが設定されていません")
            elif env == 'production' and any('@example.com' in user for user in allowed_users):
                errors.append(f"⚠️  {env}環境: example.comドメインのユーザーが含まれています")
            
            # セキュリティ設定の強度チェック
            security_issues = self._check_security_strength(env_config, env)
            errors.extend(security_issues)
        
        return errors
    
    def find_placeholders(self, data: Any, path: str = "") -> List[Dict[str, str]]:
        """プレースホルダーを再帰的に検索"""
        placeholders = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                placeholders.extend(self.find_placeholders(value, current_path))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                placeholders.extend(self.find_placeholders(item, current_path))
        elif isinstance(data, str):
            for pattern in self.placeholder_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    placeholders.append({
                        'path': path,
                        'value': data,
                        'pattern': pattern
                    })
                    break
        
        return placeholders
    
    def _check_security_strength(self, env_config: Dict[str, Any], environment: str) -> List[str]:
        """セキュリティ設定の強度チェック"""
        issues = []
        
        security = env_config.get('security', {})
        
        # JWT/セッションシークレットの強度チェック
        jwt_secret = security.get('jwtSecret', '')
        session_secret = security.get('sessionSecret', '')
        
        if jwt_secret and len(jwt_secret) < 32:
            issues.append(f"⚠️  {environment}環境: JWTシークレットが短すぎます（推奨: 32文字以上）")
        
        if session_secret and len(session_secret) < 32:
            issues.append(f"⚠️  {environment}環境: セッションシークレットが短すぎます（推奨: 32文字以上）")
        
        # 本番環境での追加チェック
        if environment == 'production':
            if jwt_secret == session_secret:
                issues.append(f"⚠️  {environment}環境: JWTシークレットとセッションシークレットが同じです")
            
            # 弱いパスワードパターンのチェック
            weak_patterns = ['password', '123456', 'secret', 'admin']
            for pattern in weak_patterns:
                if pattern.lower() in jwt_secret.lower() or pattern.lower() in session_secret.lower():
                    issues.append(f"⚠️  {environment}環境: 弱いシークレットパターンが検出されました")
                    break
        
        return issues
    
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
    
    def generate_secure_secret(self, length: int = 64) -> str:
        """安全なシークレットの生成"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def auto_fix_placeholders(self, interactive: bool = True) -> bool:
        """プレースホルダーの自動修正"""
        if not self.config_path.exists():
            print(f"❌ 設定ファイルが見つかりません: {self.config_path}")
            return False
        
        # バックアップ作成
        backup_file = self.backup_config()
        print(f"📁 バックアップを作成しました: {backup_file}")
        
        config_data = self.load_config()
        modified = False
        
        print("\n🔧 プレースホルダーの自動修正を開始します...")
        print("=" * 60)
        
        for env_name, env_config in config_data.get('environments', {}).items():
            print(f"\n📋 {env_name}環境の処理中...")
            
            # Google OAuth設定の修正
            if self._fix_google_oauth_placeholders(env_config, env_name, interactive):
                modified = True
            
            # セキュリティ設定の修正
            if self._fix_security_placeholders(env_config, env_name, interactive):
                modified = True
            
            # ユーザー設定の修正
            if self._fix_user_placeholders(env_config, env_name, interactive):
                modified = True
        
        if modified:
            # 設定ファイルを保存
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ 設定ファイルを更新しました: {self.config_path}")
            
            # 検証実行
            print("\n🔍 更新された設定ファイルを検証中...")
            errors = self.validate_config(config_data)
            if errors:
                print("⚠️  まだ修正が必要な項目があります:")
                for error in errors:
                    print(f"  {error}")
            else:
                print("✅ 全ての設定が正常です！")
            
            return True
        else:
            print("\n📝 修正が必要なプレースホルダーは見つかりませんでした。")
            return False
    
    def _fix_google_oauth_placeholders(self, env_config: Dict[str, Any], env_name: str, interactive: bool) -> bool:
        """Google OAuth設定のプレースホルダー修正"""
        modified = False
        google_config = env_config.get('google', {})
        
        # Client ID
        client_id = google_config.get('clientId', '')
        if client_id.startswith('YOUR_'):
            if interactive:
                print(f"\n🔑 {env_name}環境のGoogle OAuth Client IDを設定してください")
                print("💡 Google Cloud Consoleで取得したClient IDを入力してください")
                print("   例: 123456789-abcdefghijklmnop.apps.googleusercontent.com")
                new_client_id = input("Client ID: ").strip()
                if new_client_id:
                    google_config['clientId'] = new_client_id
                    modified = True
                    print("✅ Client IDを設定しました")
            else:
                print(f"⚠️  {env_name}環境: Google OAuth Client IDの手動設定が必要です")
        
        # Client Secret
        client_secret = google_config.get('clientSecret', '')
        if client_secret.startswith('YOUR_'):
            if interactive:
                print(f"\n🔐 {env_name}環境のGoogle OAuth Client Secretを設定してください")
                print("💡 Google Cloud Consoleで取得したClient Secretを入力してください")
                print("   例: GOCSPX-abcdefghijklmnopqrstuvwxyz")
                new_client_secret = input("Client Secret: ").strip()
                if new_client_secret:
                    google_config['clientSecret'] = new_client_secret
                    modified = True
                    print("✅ Client Secretを設定しました")
            else:
                print(f"⚠️  {env_name}環境: Google OAuth Client Secretの手動設定が必要です")
        
        return modified
    
    def _fix_security_placeholders(self, env_config: Dict[str, Any], env_name: str, interactive: bool) -> bool:
        """セキュリティ設定のプレースホルダー修正"""
        modified = False
        security_config = env_config.get('security', {})
        
        # JWT Secret
        jwt_secret = security_config.get('jwtSecret', '')
        if jwt_secret.startswith('YOUR_'):
            if interactive:
                print(f"\n🔐 {env_name}環境のJWTシークレットを生成しますか？")
                print("💡 安全なランダム文字列を自動生成します（推奨）")
                choice = input("自動生成する場合は Enter、手動入力する場合は 'manual' を入力: ").strip().lower()
                
                if choice == 'manual':
                    print("💡 32文字以上の安全な文字列を入力してください")
                    new_jwt_secret = input("JWT Secret: ").strip()
                    if new_jwt_secret:
                        security_config['jwtSecret'] = new_jwt_secret
                        modified = True
                        print("✅ JWTシークレットを設定しました")
                else:
                    new_jwt_secret = self.generate_secure_secret(64)
                    security_config['jwtSecret'] = new_jwt_secret
                    modified = True
                    print("✅ JWTシークレットを自動生成しました")
            else:
                # 非対話モードでは自動生成
                new_jwt_secret = self.generate_secure_secret(64)
                security_config['jwtSecret'] = new_jwt_secret
                modified = True
                print(f"✅ {env_name}環境: JWTシークレットを自動生成しました")
        
        # Session Secret
        session_secret = security_config.get('sessionSecret', '')
        if session_secret.startswith('YOUR_'):
            if interactive:
                print(f"\n🔐 {env_name}環境のセッションシークレットを生成しますか？")
                print("💡 安全なランダム文字列を自動生成します（推奨）")
                choice = input("自動生成する場合は Enter、手動入力する場合は 'manual' を入力: ").strip().lower()
                
                if choice == 'manual':
                    print("💡 32文字以上の安全な文字列を入力してください")
                    new_session_secret = input("Session Secret: ").strip()
                    if new_session_secret:
                        security_config['sessionSecret'] = new_session_secret
                        modified = True
                        print("✅ セッションシークレットを設定しました")
                else:
                    new_session_secret = self.generate_secure_secret(64)
                    security_config['sessionSecret'] = new_session_secret
                    modified = True
                    print("✅ セッションシークレットを自動生成しました")
            else:
                # 非対話モードでは自動生成
                new_session_secret = self.generate_secure_secret(64)
                security_config['sessionSecret'] = new_session_secret
                modified = True
                print(f"✅ {env_name}環境: セッションシークレットを自動生成しました")
        
        return modified
    
    def _fix_user_placeholders(self, env_config: Dict[str, Any], env_name: str, interactive: bool) -> bool:
        """ユーザー設定のプレースホルダー修正"""
        modified = False
        security_config = env_config.get('security', {})
        allowed_users = security_config.get('allowedUsers', [])
        
        # example.comドメインのユーザーをチェック
        example_users = [user for user in allowed_users if '@example.com' in user]
        
        if example_users:
            if interactive:
                print(f"\n👥 {env_name}環境の許可ユーザーリストにテンプレートユーザーが含まれています")
                print("💡 実際のユーザーのメールアドレスに変更してください")
                print(f"現在のユーザー: {', '.join(example_users)}")
                
                new_users = []
                for example_user in example_users:
                    print(f"\n'{example_user}' を置き換えてください:")
                    new_email = input("新しいメールアドレス (空白でスキップ): ").strip()
                    if new_email and '@' in new_email:
                        new_users.append(new_email)
                        print(f"✅ {new_email} を追加しました")
                
                if new_users:
                    # example.comユーザーを削除して新しいユーザーを追加
                    updated_users = [user for user in allowed_users if '@example.com' not in user]
                    updated_users.extend(new_users)
                    security_config['allowedUsers'] = updated_users
                    modified = True
                    print("✅ 許可ユーザーリストを更新しました")
            else:
                print(f"⚠️  {env_name}環境: example.comドメインのユーザーの手動修正が必要です: {', '.join(example_users)}")
        
        return modified
    
    def interactive_setup_wizard(self) -> bool:
        """初心者向け対話式セットアップウィザード"""
        print("🎉 Excel解除ツール 設定ウィザードへようこそ！")
        print("=" * 60)
        print("💡 このウィザードでは、初心者の方でも簡単に設定を完了できます")
        print("🛡️ 完全に安全です。何も壊れません")
        print("🔄 いつでも元に戻すことができます")
        print("⏱️ 約10分で完了します")
        print()
        
        # 設定ファイルの存在確認
        if not self.config_path.exists():
            print("📁 設定ファイルが見つかりません。テンプレートから作成します...")
            if not self.create_from_template():
                return False
        
        print("🔍 現在の設定を確認中...")
        config_data = self.load_config()
        placeholders = []
        
        for env_name, env_config in config_data.get('environments', {}).items():
            env_placeholders = self.find_placeholders(env_config)
            if env_placeholders:
                placeholders.extend([(env_name, p) for p in env_placeholders])
        
        if not placeholders:
            print("✅ 設定は既に完了しています！")
            return True
        
        print(f"📋 {len(placeholders)}個の設定項目が見つかりました")
        print()
        
        # 環境選択
        print("🌍 どの環境から設定を始めますか？")
        print("1. 開発環境（development）- テスト用")
        print("2. 本番環境（production）- 実際の運用用")
        print("3. 全ての環境を一度に設定")
        print()
        print("推奨：初めての方は「1」がおすすめです")
        
        while True:
            choice = input("選択してください (1-3): ").strip()
            if choice == '1':
                target_envs = ['development']
                break
            elif choice == '2':
                target_envs = ['production']
                break
            elif choice == '3':
                target_envs = ['development', 'staging', 'production']
                break
            else:
                print("❌ 1、2、または3を入力してください")
        
        print(f"\n🚀 {', '.join(target_envs)}環境の設定を開始します...")
        
        # 各環境の設定
        for env_name in target_envs:
            if env_name in config_data.get('environments', {}):
                print(f"\n📋 {env_name}環境の設定")
                print("-" * 40)
                env_config = config_data['environments'][env_name]
                
                # Google OAuth設定
                self._wizard_google_oauth(env_config, env_name)
                
                # セキュリティ設定
                self._wizard_security(env_config, env_name)
                
                # ユーザー設定
                self._wizard_users(env_config, env_name)
        
        # 設定保存
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print("\n🎉 設定が完了しました！")
        print("✅ 設定ファイルを保存しました")
        
        # 最終検証
        print("\n🔍 設定の最終確認中...")
        errors = self.validate_config(config_data)
        if errors:
            print("⚠️  以下の項目をご確認ください:")
            for error in errors:
                print(f"  {error}")
        else:
            print("✅ 全ての設定が正常です！")
        
        print("\n📞 困ったときは:")
        print("  - 設定ファイル: setup-config.json")
        print("  - バックアップ: config-backup/ フォルダ")
        print("  - サポート: 管理者にお問い合わせください")
        
        return True
    
    def _wizard_google_oauth(self, env_config: Dict[str, Any], env_name: str):
        """Google OAuth設定ウィザード"""
        google_config = env_config.get('google', {})
        
        print(f"\n🔑 {env_name}環境のGoogle OAuth設定")
        print("💡 GoogleでログインするためのIDとパスワードを設定します")
        print("🛡️ これらの情報は安全に保存されます")
        
        # Client ID
        client_id = google_config.get('clientId', '')
        if client_id.startswith('YOUR_'):
            print("\n📝 Google Client IDを入力してください")
            print("💡 Google Cloud Consoleで「認証情報」から取得できます")
            print("   形式例: 123456789-abc...xyz.apps.googleusercontent.com")
            
            while True:
                new_client_id = input("Client ID: ").strip()
                if new_client_id:
                    if '.apps.googleusercontent.com' in new_client_id:
                        google_config['clientId'] = new_client_id
                        print("✅ Client IDを設定しました")
                        break
                    else:
                        print("❌ 正しいClient ID形式ではありません。もう一度入力してください")
                else:
                    print("❌ Client IDは必須です。もう一度入力してください")
        
        # Client Secret
        client_secret = google_config.get('clientSecret', '')
        if client_secret.startswith('YOUR_'):
            print("\n🔐 Google Client Secretを入力してください")
            print("💡 Google Cloud Consoleで「認証情報」から取得できます")
            print("   形式例: GOCSPX-abcdefghijklmnopqrstuvwxyz")
            
            while True:
                new_client_secret = input("Client Secret: ").strip()
                if new_client_secret:
                    if new_client_secret.startswith('GOCSPX-') or len(new_client_secret) > 20:
                        google_config['clientSecret'] = new_client_secret
                        print("✅ Client Secretを設定しました")
                        break
                    else:
                        print("❌ 正しいClient Secret形式ではありません。もう一度入力してください")
                else:
                    print("❌ Client Secretは必須です。もう一度入力してください")
    
    def _wizard_security(self, env_config: Dict[str, Any], env_name: str):
        """セキュリティ設定ウィザード"""
        security_config = env_config.get('security', {})
        
        print(f"\n🔐 {env_name}環境のセキュリティ設定")
        print("💡 ログイン時の暗号化に使用する秘密の文字列を設定します")
        print("🛡️ 自動生成が最も安全です（推奨）")
        
        # JWT Secret
        jwt_secret = security_config.get('jwtSecret', '')
        if jwt_secret.startswith('YOUR_'):
            print("\n🔑 JWTシークレット（ログイン暗号化キー）の設定")
            print("1. 自動生成する（推奨・最も安全）")
            print("2. 手動で入力する")
            print()
            print("推奨：初めての方は「1」がおすすめです")
            
            while True:
                choice = input("選択してください (1-2): ").strip()
                if choice == '1' or choice == '':
                    new_jwt_secret = self.generate_secure_secret(64)
                    security_config['jwtSecret'] = new_jwt_secret
                    print("✅ JWTシークレットを自動生成しました")
                    break
                elif choice == '2':
                    print("💡 32文字以上の複雑な文字列を入力してください")
                    new_jwt_secret = input("JWT Secret: ").strip()
                    if len(new_jwt_secret) >= 32:
                        security_config['jwtSecret'] = new_jwt_secret
                        print("✅ JWTシークレットを設定しました")
                        break
                    else:
                        print("❌ 32文字以上で入力してください")
                else:
                    print("❌ 1または2を入力してください")
        
        # Session Secret
        session_secret = security_config.get('sessionSecret', '')
        if session_secret.startswith('YOUR_'):
            print("\n🔐 セッションシークレット（セッション暗号化キー）の設定")
            print("💡 自動生成します（JWTシークレットとは異なる値）")
            
            new_session_secret = self.generate_secure_secret(64)
            security_config['sessionSecret'] = new_session_secret
            print("✅ セッションシークレットを自動生成しました")
    
    def _wizard_users(self, env_config: Dict[str, Any], env_name: str):
        """ユーザー設定ウィザード"""
        security_config = env_config.get('security', {})
        allowed_users = security_config.get('allowedUsers', [])
        
        print(f"\n👥 {env_name}環境の許可ユーザー設定")
        print("💡 このツールを使用できるユーザーのメールアドレスを設定します")
        print("🛡️ 設定されたユーザーのみがアクセスできます")
        
        # example.comユーザーの確認
        example_users = [user for user in allowed_users if '@example.com' in user]
        
        if example_users:
            print(f"\n📋 現在のテンプレートユーザー: {', '.join(example_users)}")
            print("💡 実際のユーザーのメールアドレスに変更してください")
            
            new_users = []
            for i, example_user in enumerate(example_users, 1):
                print(f"\n{i}. '{example_user}' を実際のメールアドレスに変更")
                while True:
                    new_email = input("新しいメールアドレス: ").strip()
                    if new_email:
                        if '@' in new_email and '.' in new_email:
                            new_users.append(new_email)
                            print(f"✅ {new_email} を追加しました")
                            break
                        else:
                            print("❌ 正しいメールアドレス形式で入力してください")
                    else:
                        print("❌ メールアドレスは必須です")
            
            # ユーザーリストを更新
            updated_users = [user for user in allowed_users if '@example.com' not in user]
            updated_users.extend(new_users)
            security_config['allowedUsers'] = updated_users
            
            print(f"✅ 許可ユーザーリストを更新しました: {', '.join(new_users)}")
        
        # 追加ユーザーの確認
        print(f"\n➕ 追加でユーザーを登録しますか？")
        print("💡 後からでも追加できます")
        
        while True:
            add_more = input("追加する場合は 'y'、完了する場合は Enter: ").strip().lower()
            if add_more == 'y':
                new_email = input("追加するメールアドレス: ").strip()
                if new_email and '@' in new_email and '.' in new_email:
                    current_users = security_config.get('allowedUsers', [])
                    if new_email not in current_users:
                        current_users.append(new_email)
                        security_config['allowedUsers'] = current_users
                        print(f"✅ {new_email} を追加しました")
                    else:
                        print("⚠️  そのユーザーは既に登録されています")
                else:
                    print("❌ 正しいメールアドレス形式で入力してください")
            else:
                break
    
    def run_verification_tests(self) -> bool:
        """設定完了後の検証テスト実行"""
        print("\n🧪 設定検証テストを実行中...")
        print("=" * 50)
        
        all_passed = True
        
        # 1. 設定ファイル存在確認
        print("1. 設定ファイル存在確認...")
        if self.config_path.exists():
            print("   ✅ 設定ファイルが存在します")
        else:
            print("   ❌ 設定ファイルが見つかりません")
            all_passed = False
        
        # 2. JSON形式確認
        print("2. JSON形式確認...")
        try:
            config_data = self.load_config()
            print("   ✅ JSON形式が正しいです")
        except Exception as e:
            print(f"   ❌ JSON形式エラー: {str(e)}")
            all_passed = False
            return all_passed
        
        # 3. プレースホルダー確認
        print("3. プレースホルダー確認...")
        total_placeholders = 0
        for env_name, env_config in config_data.get('environments', {}).items():
            placeholders = self.find_placeholders(env_config)
            if placeholders:
                total_placeholders += len(placeholders)
                print(f"   ⚠️  {env_name}環境: {len(placeholders)}個のプレースホルダーが残っています")
                for p in placeholders:
                    print(f"      - {p['path']}: {p['value']}")
        
        if total_placeholders == 0:
            print("   ✅ プレースホルダーは全て修正されています")
        else:
            print(f"   ⚠️  {total_placeholders}個のプレースホルダーが残っています")
        
        # 4. セキュリティ強度確認
        print("4. セキュリティ強度確認...")
        security_issues = 0
        for env_name, env_config in config_data.get('environments', {}).items():
            issues = self._check_security_strength(env_config, env_name)
            if issues:
                security_issues += len(issues)
                print(f"   ⚠️  {env_name}環境: {len(issues)}個のセキュリティ問題")
                for issue in issues:
                    print(f"      - {issue}")
        
        if security_issues == 0:
            print("   ✅ セキュリティ設定は適切です")
        else:
            print(f"   ⚠️  {security_issues}個のセキュリティ問題があります")
        
        # 5. 環境変数生成テスト
        print("5. 環境変数生成テスト...")
        try:
            for env_name in ['development', 'staging', 'production']:
                if env_name in config_data.get('environments', {}):
                    env_vars = self.generate_env_vars(env_name, 'json')
                    env_data = json.loads(env_vars)
                    if len(env_data) > 10:  # 最低限の環境変数数
                        print(f"   ✅ {env_name}環境: {len(env_data)}個の環境変数を生成")
                    else:
                        print(f"   ⚠️  {env_name}環境: 環境変数が不足している可能性があります")
        except Exception as e:
            print(f"   ❌ 環境変数生成エラー: {str(e)}")
            all_passed = False
        
        # 6. 全体検証
        print("6. 全体検証...")
        errors = self.validate_config(config_data)
        if errors:
            print(f"   ⚠️  {len(errors)}個の検証エラー:")
            for error in errors:
                print(f"      - {error}")
        else:
            print("   ✅ 全体検証に合格しました")
        
        # 結果サマリー
        print("\n" + "=" * 50)
        if all_passed and total_placeholders == 0 and security_issues == 0 and not errors:
            print("🎉 全ての検証テストに合格しました！")
            print("✅ 設定は完璧です。デプロイメントを開始できます。")
            return True
        else:
            print("⚠️  一部の検証テストで問題が見つかりました")
            print("💡 上記の問題を修正してから再度テストを実行してください")
            return False


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
    
    # auto-fix コマンド
    autofix_parser = subparsers.add_parser('auto-fix', help='プレースホルダーの自動修正')
    autofix_parser.add_argument('--config', default='setup-config.json', help='設定ファイルのパス')
    autofix_parser.add_argument('--non-interactive', action='store_true', help='非対話モード')
    
    # wizard コマンド
    wizard_parser = subparsers.add_parser('wizard', help='初心者向け対話式セットアップウィザード')
    wizard_parser.add_argument('--config', default='setup-config.json', help='設定ファイルのパス')
    
    # verify コマンド
    verify_parser = subparsers.add_parser('verify', help='設定完了後の検証テスト実行')
    verify_parser.add_argument('--config', default='setup-config.json', help='設定ファイルのパス')
    
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
        
        elif args.command == 'auto-fix':
            interactive = not args.non_interactive
            config_manager.auto_fix_placeholders(interactive)
        
        elif args.command == 'wizard':
            config_manager.interactive_setup_wizard()
        
        elif args.command == 'verify':
            success = config_manager.run_verification_tests()
            if not success:
                sys.exit(1)
    
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()