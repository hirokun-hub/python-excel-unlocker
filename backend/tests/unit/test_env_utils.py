"""
テスト環境変数設定ユーティリティ
テスト実行時の環境変数管理をサポート
"""
import os
from typing import Dict, Any, Optional
from contextlib import contextmanager


class TestEnvironment:
    """テスト環境変数管理クラス"""
    
    @staticmethod
    def get_test_env_vars() -> Dict[str, str]:
        """テスト用の標準環境変数を取得"""
        return {
            'S3_BUCKET_NAME': 'test-excel-unlock-bucket',
            'ALLOWED_USERS': 'test@example.com,admin@example.com',
            'GOOGLE_CLIENT_ID': 'test-client-id.apps.googleusercontent.com',
            'LOG_LEVEL': 'INFO',
            'AWS_DEFAULT_REGION': 'ap-northeast-1'
        }
    
    @staticmethod
    @contextmanager
    def temporary_env(**env_vars):
        """
        一時的に環境変数を設定するコンテキストマネージャー
        
        Args:
            **env_vars: 設定する環境変数
        """
        original_env = {}
        
        # 現在の環境変数を保存
        for key in env_vars:
            if key in os.environ:
                original_env[key] = os.environ[key]
        
        try:
            # 新しい環境変数を設定
            for key, value in env_vars.items():
                os.environ[key] = value
            
            yield
            
        finally:
            # 元の環境変数を復元
            for key in env_vars:
                if key in original_env:
                    os.environ[key] = original_env[key]
                elif key in os.environ:
                    del os.environ[key]
    
    @staticmethod
    def setup_test_env():
        """テスト用環境変数を設定"""
        test_env = TestEnvironment.get_test_env_vars()
        for key, value in test_env.items():
            os.environ[key] = value
    
    @staticmethod
    def clear_test_env():
        """テスト用環境変数をクリア"""
        test_env = TestEnvironment.get_test_env_vars()
        for key in test_env:
            if key in os.environ:
                del os.environ[key]


# 便利関数
def with_test_env(**extra_env):
    """テスト環境変数設定デコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            test_env = TestEnvironment.get_test_env_vars()
            test_env.update(extra_env)
            
            with TestEnvironment.temporary_env(**test_env):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def setup_minimal_test_env():
    """最小限のテスト環境変数を設定"""
    minimal_env = {
        'S3_BUCKET_NAME': 'test-bucket',
        'ALLOWED_USERS': 'test@example.com',
        'GOOGLE_CLIENT_ID': 'test-client-id'
    }
    
    for key, value in minimal_env.items():
        os.environ[key] = value