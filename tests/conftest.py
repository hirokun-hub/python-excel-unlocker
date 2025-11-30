"""
テスト共通設定

テストデータの定数とフィクスチャを定義します。
"""

import os
import pytest
from pathlib import Path

# テストデータディレクトリ
TEST_DATA_DIR = Path("data")

# テスト用パスワード
TEST_PASSWORD = "test1234"

# テスト用 Excel ファイル（パスワード保護済み）
TEST_FILES = [
    "sample_protected.xlsx",
    "sample_protected.xlsx",
    "sample_protected.xlsx",
]


@pytest.fixture
def test_data_dir() -> Path:
    """テストデータディレクトリのパスを返す"""
    return TEST_DATA_DIR


@pytest.fixture
def test_password() -> str:
    """テスト用パスワードを返す"""
    return TEST_PASSWORD


@pytest.fixture
def test_excel_file() -> Path:
    """テスト用 Excel ファイルのパスを返す（最初のファイル）"""
    return TEST_DATA_DIR / TEST_FILES[0]


@pytest.fixture
def all_test_excel_files() -> list[Path]:
    """全テスト用 Excel ファイルのパスリストを返す"""
    return [TEST_DATA_DIR / f for f in TEST_FILES]


@pytest.fixture
def wrong_password() -> str:
    """不正なパスワードを返す"""
    return "wrong_password_123"
