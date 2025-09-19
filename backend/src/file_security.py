"""
ファイル安全性チェック機能（無料実装）

基本的なマルウェア対策として以下の機能を提供：
- マクロ付きファイル（.xlsm）の検出・拒否
- ファイルサイズ制限の厳格化
- マジックバイト検証の実装
- 拡張子・MIMEタイプの厳格チェック
- 疑わしいファイルの隔離機能

要件: 基本的なマルウェア対策（無料）
"""
import logging
import os
import mimetypes
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# セキュリティ設定（定数）
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
MIN_FILE_SIZE = 100  # 100バイト（空ファイル対策）

# 許可されたファイル拡張子（厳格チェック）
ALLOWED_EXTENSIONS = frozenset(['.xlsx', '.xls'])

# 許可されたMIMEタイプ（厳格チェック）
ALLOWED_MIME_TYPES = frozenset([
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
    'application/vnd.ms-excel',  # .xls
    'application/octet-stream'  # 一部のブラウザで送信される場合がある
])

# 危険なファイル拡張子（拒否リスト）
DANGEROUS_EXTENSIONS = frozenset([
    '.xlsm',  # マクロ付きExcel
    '.xlsb',  # バイナリExcel（マクロ可能）
    '.xltm',  # マクロ付きテンプレート
    '.xla',   # Excel アドイン
    '.xlam',  # マクロ付きアドイン
    '.exe',   # 実行ファイル
    '.bat',   # バッチファイル
    '.cmd',   # コマンドファイル
    '.scr',   # スクリーンセーバー
    '.com',   # 実行ファイル
    '.pif',   # プログラム情報ファイル
    '.vbs',   # VBScript
    '.js',    # JavaScript
    '.jar',   # Java Archive
    '.zip',   # ZIP（偽装の可能性）
    '.rar',   # RAR（偽装の可能性）
])

# Excelファイルの有効なマジックバイト
VALID_MAGIC_BYTES = [
    b'PK\x03\x04',  # ZIP形式（.xlsx）の開始
    b'PK\x05\x06',  # ZIP形式（空の.xlsx）
    b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',  # OLE2形式（.xls）
]

# 危険なマジックバイト（実行ファイル等）
DANGEROUS_MAGIC_BYTES = [
    b'MZ',  # Windows実行ファイル
    b'\x7fELF',  # Linux実行ファイル
    b'\xca\xfe\xba\xbe',  # Java class file
    b'Rar!',  # RAR archive
    b'\x1f\x8b',  # GZIP
]

class SecurityCheckResult:
    """セキュリティチェック結果クラス"""
    
    def __init__(self, safe: bool, reason: str, risk_level: str = 'low', 
                 quarantine: bool = False, details: Optional[Dict[str, Any]] = None):
        self.safe = safe
        self.reason = reason
        self.risk_level = risk_level  # 'low', 'medium', 'high', 'critical'
        self.quarantine = quarantine  # 隔離が必要かどうか
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'safe': self.safe,
            'reason': self.reason,
            'risk_level': self.risk_level,
            'quarantine': self.quarantine,
            'details': self.details
        }

def check_file_extension(file_path: str) -> SecurityCheckResult:
    """
    ファイル拡張子の厳格チェック
    
    Args:
        file_path: チェック対象ファイルのパス
    
    Returns:
        SecurityCheckResult: チェック結果
    """
    file_ext = Path(file_path).suffix.lower()
    
    # 危険な拡張子のチェック（最優先）
    if file_ext in DANGEROUS_EXTENSIONS:
        if file_ext == '.xlsm':
            return SecurityCheckResult(
                safe=False,
                reason='マクロ付きExcelファイル（.xlsm）は処理できません。セキュリティ上の理由により拒否されました。',
                risk_level='high',
                quarantine=True,
                details={'detected_extension': file_ext, 'threat_type': 'macro_enabled'}
            )
        else:
            return SecurityCheckResult(
                safe=False,
                reason=f'危険なファイル形式（{file_ext}）が検出されました。このファイル形式は処理できません。',
                risk_level='critical',
                quarantine=True,
                details={'detected_extension': file_ext, 'threat_type': 'dangerous_executable'}
            )
    
    # 許可された拡張子のチェック
    if file_ext not in ALLOWED_EXTENSIONS:
        return SecurityCheckResult(
            safe=False,
            reason=f'サポートされていないファイル形式です（{file_ext}）。.xlsx または .xls ファイルのみ処理可能です。',
            risk_level='medium',
            quarantine=False,
            details={'detected_extension': file_ext, 'allowed_extensions': list(ALLOWED_EXTENSIONS)}
        )
    
    return SecurityCheckResult(
        safe=True,
        reason='ファイル拡張子チェック通過',
        risk_level='low',
        details={'detected_extension': file_ext}
    )

def check_file_size(file_path: str) -> SecurityCheckResult:
    """
    ファイルサイズの厳格チェック
    
    Args:
        file_path: チェック対象ファイルのパス
    
    Returns:
        SecurityCheckResult: チェック結果
    """
    try:
        file_size = os.path.getsize(file_path)
    except OSError as e:
        return SecurityCheckResult(
            safe=False,
            reason=f'ファイルサイズの取得に失敗しました: {str(e)}',
            risk_level='medium',
            quarantine=False
        )
    
    # 最大サイズチェック
    if file_size > MAX_FILE_SIZE:
        return SecurityCheckResult(
            safe=False,
            reason=f'ファイルサイズ（{file_size:,} bytes）が上限（{MAX_FILE_SIZE:,} bytes）を超えています。',
            risk_level='medium',
            quarantine=False,
            details={'file_size': file_size, 'max_size': MAX_FILE_SIZE}
        )
    
    # 最小サイズチェック（空ファイル・破損ファイル対策）
    if file_size < MIN_FILE_SIZE:
        return SecurityCheckResult(
            safe=False,
            reason=f'ファイルサイズ（{file_size} bytes）が小さすぎます。破損している可能性があります。',
            risk_level='medium',
            quarantine=True,
            details={'file_size': file_size, 'min_size': MIN_FILE_SIZE}
        )
    
    return SecurityCheckResult(
        safe=True,
        reason='ファイルサイズチェック通過',
        risk_level='low',
        details={'file_size': file_size}
    )

def check_magic_bytes(file_path: str) -> SecurityCheckResult:
    """
    マジックバイト検証の実装
    
    Args:
        file_path: チェック対象ファイルのパス
    
    Returns:
        SecurityCheckResult: チェック結果
    """
    try:
        with open(file_path, 'rb') as f:
            # 最初の16バイトを読み取り（多くのマジックバイトをカバー）
            magic_bytes = f.read(16)
    except OSError as e:
        return SecurityCheckResult(
            safe=False,
            reason=f'ファイルの読み取りに失敗しました: {str(e)}',
            risk_level='medium',
            quarantine=False
        )
    
    if len(magic_bytes) < 4:
        return SecurityCheckResult(
            safe=False,
            reason='ファイルが短すぎます。破損している可能性があります。',
            risk_level='medium',
            quarantine=True,
            details={'magic_bytes_length': len(magic_bytes)}
        )
    
    # 危険なマジックバイトのチェック（最優先）
    for dangerous_magic in DANGEROUS_MAGIC_BYTES:
        if magic_bytes.startswith(dangerous_magic):
            return SecurityCheckResult(
                safe=False,
                reason='実行ファイルまたは危険なファイル形式が検出されました。処理を拒否します。',
                risk_level='critical',
                quarantine=True,
                details={
                    'detected_magic': dangerous_magic.hex(),
                    'threat_type': 'executable_or_archive'
                }
            )
    
    # 有効なExcelマジックバイトのチェック
    is_valid_excel = False
    detected_format = None
    
    for valid_magic in VALID_MAGIC_BYTES:
        if magic_bytes.startswith(valid_magic):
            is_valid_excel = True
            if valid_magic.startswith(b'PK'):
                detected_format = 'xlsx_zip'
            elif valid_magic.startswith(b'\xd0\xcf'):
                detected_format = 'xls_ole2'
            break
    
    if not is_valid_excel:
        return SecurityCheckResult(
            safe=False,
            reason='Excelファイルの形式が認識できません。ファイルが破損しているか、偽装されている可能性があります。',
            risk_level='high',
            quarantine=True,
            details={
                'detected_magic': magic_bytes[:8].hex(),
                'expected_formats': ['xlsx_zip', 'xls_ole2']
            }
        )
    
    return SecurityCheckResult(
        safe=True,
        reason='マジックバイトチェック通過',
        risk_level='low',
        details={'detected_format': detected_format}
    )

def check_mime_type(file_path: str, declared_mime_type: Optional[str] = None) -> SecurityCheckResult:
    """
    MIMEタイプの厳格チェック
    
    Args:
        file_path: チェック対象ファイルのパス
        declared_mime_type: クライアントが宣言したMIMEタイプ
    
    Returns:
        SecurityCheckResult: チェック結果
    """
    # ファイル拡張子からMIMEタイプを推測
    guessed_mime_type, _ = mimetypes.guess_type(file_path)
    
    details = {
        'declared_mime_type': declared_mime_type,
        'guessed_mime_type': guessed_mime_type,
        'allowed_mime_types': list(ALLOWED_MIME_TYPES)
    }
    
    # 宣言されたMIMEタイプのチェック
    if declared_mime_type:
        if declared_mime_type not in ALLOWED_MIME_TYPES:
            return SecurityCheckResult(
                safe=False,
                reason=f'許可されていないMIMEタイプです: {declared_mime_type}',
                risk_level='medium',
                quarantine=False,
                details=details
            )
    
    # 推測されたMIMEタイプのチェック（補助的）
    if guessed_mime_type and guessed_mime_type not in ALLOWED_MIME_TYPES:
        # 警告レベル（拒否はしない）
        logger.warning(f"Suspicious MIME type detected: {guessed_mime_type} for file {file_path}")
        details['warning'] = f'疑わしいMIMEタイプ: {guessed_mime_type}'
    
    return SecurityCheckResult(
        safe=True,
        reason='MIMEタイプチェック通過',
        risk_level='low',
        details=details
    )

def check_file_structure(file_path: str) -> SecurityCheckResult:
    """
    ファイル構造の基本チェック（ZIP/OLE2構造の検証）
    
    Args:
        file_path: チェック対象ファイルのパス
    
    Returns:
        SecurityCheckResult: チェック結果
    """
    try:
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.xlsx':
            # ZIP構造の検証
            import zipfile
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_file:
                    # 基本的なOffice文書構造をチェック
                    required_files = ['[Content_Types].xml', '_rels/.rels']
                    file_list = zip_file.namelist()
                    
                    missing_files = [f for f in required_files if f not in file_list]
                    if missing_files:
                        return SecurityCheckResult(
                            safe=False,
                            reason='Excelファイルの内部構造が正しくありません。破損または偽装の可能性があります。',
                            risk_level='high',
                            quarantine=True,
                            details={'missing_files': missing_files, 'structure_type': 'xlsx_zip'}
                        )
                    
                    # マクロファイルの検出
                    macro_files = [f for f in file_list if 'vbaProject' in f or f.endswith('.bin')]
                    if macro_files:
                        return SecurityCheckResult(
                            safe=False,
                            reason='マクロが含まれているファイルが検出されました。セキュリティ上の理由により処理を拒否します。',
                            risk_level='critical',
                            quarantine=True,
                            details={'macro_files': macro_files, 'threat_type': 'embedded_macros'}
                        )
                        
            except zipfile.BadZipFile:
                return SecurityCheckResult(
                    safe=False,
                    reason='ZIP形式として読み取れません。ファイルが破損しているか、偽装されている可能性があります。',
                    risk_level='high',
                    quarantine=True,
                    details={'structure_type': 'invalid_zip'}
                )
        
        elif file_ext == '.xls':
            # OLE2構造の基本チェック
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(512)  # OLE2ヘッダーサイズ
                    
                # OLE2シグネチャの詳細チェック
                if len(header) < 512:
                    return SecurityCheckResult(
                        safe=False,
                        reason='OLE2ヘッダーが不完全です。ファイルが破損している可能性があります。',
                        risk_level='medium',
                        quarantine=True,
                        details={'header_size': len(header), 'structure_type': 'incomplete_ole2'}
                    )
                
                # OLE2の基本構造チェック
                ole2_signature = header[:8]
                if ole2_signature != b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
                    return SecurityCheckResult(
                        safe=False,
                        reason='OLE2形式のシグネチャが正しくありません。',
                        risk_level='high',
                        quarantine=True,
                        details={'detected_signature': ole2_signature.hex(), 'structure_type': 'invalid_ole2'}
                    )
                    
            except OSError as e:
                return SecurityCheckResult(
                    safe=False,
                    reason=f'ファイル構造の検証中にエラーが発生しました: {str(e)}',
                    risk_level='medium',
                    quarantine=False
                )
        
        return SecurityCheckResult(
            safe=True,
            reason='ファイル構造チェック通過',
            risk_level='low',
            details={'structure_type': f'{file_ext[1:]}_valid'}
        )
        
    except Exception as e:
        logger.exception(f"File structure check failed: {e}")
        return SecurityCheckResult(
            safe=False,
            reason=f'ファイル構造の検証中に予期しないエラーが発生しました: {str(e)}',
            risk_level='medium',
            quarantine=False
        )

def quarantine_file(file_path: str, reason: str) -> bool:
    """
    疑わしいファイルの隔離機能
    
    Args:
        file_path: 隔離対象ファイルのパス
        reason: 隔離理由
    
    Returns:
        bool: 隔離成功時True
    """
    try:
        # 隔離ディレクトリの作成
        quarantine_dir = '/tmp/quarantine'
        os.makedirs(quarantine_dir, exist_ok=True)
        
        # 隔離ファイル名の生成（タイムスタンプ付き）
        import time
        timestamp = int(time.time())
        original_name = Path(file_path).name
        quarantine_name = f"{timestamp}_{original_name}.quarantined"
        quarantine_path = os.path.join(quarantine_dir, quarantine_name)
        
        # ファイルを隔離ディレクトリに移動
        import shutil
        shutil.move(file_path, quarantine_path)
        
        # 隔離ログの記録
        logger.warning(f"File quarantined: {original_name} -> {quarantine_path}, Reason: {reason}")
        
        # 隔離情報ファイルの作成
        info_path = f"{quarantine_path}.info"
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(f"Original file: {original_name}\n")
            f.write(f"Quarantined at: {time.ctime()}\n")
            f.write(f"Reason: {reason}\n")
        
        return True
        
    except Exception as e:
        logger.exception(f"Failed to quarantine file {file_path}: {e}")
        return False

def comprehensive_security_check(file_path: str, declared_mime_type: Optional[str] = None) -> Dict[str, Any]:
    """
    包括的なファイル安全性チェック
    
    Args:
        file_path: チェック対象ファイルのパス
        declared_mime_type: クライアントが宣言したMIMEタイプ
    
    Returns:
        Dict[str, Any]: 包括的なチェック結果
    """
    logger.info(f"Starting comprehensive security check for file: {Path(file_path).name}")
    
    # 各チェック項目の実行
    checks = {
        'extension_check': check_file_extension(file_path),
        'size_check': check_file_size(file_path),
        'magic_bytes_check': check_magic_bytes(file_path),
        'mime_type_check': check_mime_type(file_path, declared_mime_type),
        'structure_check': check_file_structure(file_path)
    }
    
    # 全体的な安全性評価
    overall_safe = all(check.safe for check in checks.values())
    highest_risk = 'low'
    quarantine_needed = False
    failed_checks = []
    
    for check_name, result in checks.items():
        if not result.safe:
            failed_checks.append({
                'check': check_name,
                'reason': result.reason,
                'risk_level': result.risk_level
            })
            
            # 最高リスクレベルの更新
            risk_levels = ['low', 'medium', 'high', 'critical']
            if risk_levels.index(result.risk_level) > risk_levels.index(highest_risk):
                highest_risk = result.risk_level
            
            # 隔離が必要かチェック
            if result.quarantine:
                quarantine_needed = True
    
    # 隔離処理の実行
    if quarantine_needed and os.path.exists(file_path):
        quarantine_reasons = [check['reason'] for check in failed_checks if 'quarantine' in str(checks)]
        quarantine_success = quarantine_file(file_path, '; '.join(quarantine_reasons))
        if not quarantine_success:
            logger.error(f"Failed to quarantine suspicious file: {file_path}")
    
    # 結果の集約
    result = {
        'safe': overall_safe,
        'risk_level': highest_risk,
        'quarantine_applied': quarantine_needed,
        'failed_checks': failed_checks,
        'check_details': {name: check.to_dict() for name, check in checks.items()},
        'summary': _generate_security_summary(overall_safe, failed_checks, highest_risk)
    }
    
    logger.info(f"Security check completed: safe={overall_safe}, risk_level={highest_risk}, quarantine={quarantine_needed}")
    return result

def _generate_security_summary(overall_safe: bool, failed_checks: List[Dict[str, Any]], highest_risk: str) -> str:
    """
    セキュリティチェック結果のサマリーを生成
    
    Args:
        overall_safe: 全体的な安全性
        failed_checks: 失敗したチェック項目
        highest_risk: 最高リスクレベル
    
    Returns:
        str: サマリーメッセージ
    """
    if overall_safe:
        return 'ファイルは全てのセキュリティチェックに合格しました。'
    
    if highest_risk == 'critical':
        return 'クリティカルなセキュリティリスクが検出されました。このファイルは処理できません。'
    elif highest_risk == 'high':
        return '高リスクのセキュリティ問題が検出されました。ファイルが隔離されました。'
    elif highest_risk == 'medium':
        return 'セキュリティ上の問題が検出されました。ファイルを確認してください。'
    else:
        return '軽微なセキュリティ問題が検出されました。'