from io import BytesIO
import logging
import zipfile
from typing import List, Tuple

from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

class ZipService:
    def __init__(self, storage_service: StorageService):
        self.storage_service = storage_service

    def create_zip(
        self,
        file_ids: List[str]
    ) -> Tuple[BytesIO, List[str], List[str]]:
        """
        複数ファイルからZIPを生成

        Args:
            file_ids: ファイルIDのリスト

        Returns:
            (zip_buffer, successful_ids, missing_ids)
        """
        # 重複除去
        unique_ids = list(set(file_ids))
        successful_ids = []
        missing_ids = []

        # メモリ上にZIPを作成
        zip_buffer = BytesIO()

        try:
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_id in unique_ids:
                    # StorageServiceからファイルパスを取得
                    file_path = self.storage_service.get_path(file_id)
                    original_filename = self.storage_service.get_filename(file_id)

                    if not file_path or not original_filename:
                        logger.warning(f"File not found for zip: {file_id}")
                        missing_ids.append(file_id)
                        continue

                    try:
                        # ZIPに追加
                        # 重複ファイル名対策: 単純に追加するとZIP内パスが重複するが、
                        # Windows等の解凍ソフトは(1)などを付けるか上書きするか挙動が分かれる。
                        # ここではシンプルにそのまま追加する。
                        zf.write(file_path, arcname=original_filename)
                        successful_ids.append(file_id)
                    except Exception as e:
                        logger.error(f"Failed to add file to zip: {file_id}, {e}")
                        missing_ids.append(file_id)

        except Exception as e:
            logger.error(f"Failed to create zip: {e}")
            raise

        # バッファを先頭に戻す
        zip_buffer.seek(0)

        return zip_buffer, successful_ids, missing_ids

    def save_temp_zip(
        self,
        zip_buffer: BytesIO,
        filename: str
    ) -> Tuple[str, str]:
        """
        一時ZIPファイルを保存

        Returns:
            (zip_id, zip_path)
        """
        return self.storage_service.save(zip_buffer, filename)
