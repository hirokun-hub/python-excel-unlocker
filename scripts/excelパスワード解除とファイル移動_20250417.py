"""
excel_password_remover.py

説明:
  指定フォルダ内のパスワードで保護されたExcelファイルを自動で解除し、
  非暗号化ファイルはそのままコピーして出力フォルダに保存するスクリプトです.

対象ファイル:
  入力フォルダ: ~/Downloads/Officeパスワード解除希望ファイル
  対象拡張子: .xls, .xlsx, .xlsm

出力先:
  出力フォルダ: ~/Downloads/Officeパスワード解除希望ファイル/パスワード解除済みファイル
  出力ファイル名: <元ファイル名>_解除.<拡張子>

主な機能:
  1. 入力フォルダ内のファイルを全て取得
  2. 拡張子判定
     - Excel以外：そのまま移動
     - Excel：暗号化判定および解除
  3. 暗号化されていないExcelはコピー保存
  4. 暗号化されたExcelはパスワード解除（最大5回試行）
  5. 処理済みファイルは入力フォルダから削除
  6. 解除失敗ファイルだけを残す

使用方法:
  python excel_password_remover.py
"""

import msoffcrypto
from getpass import getpass
import os
import sys
import shutil

CURRENT_INDEX = None
TOTAL_FILES = None

def create_output_folder():
    """指定されたパスに出力フォルダを作成"""
    base_folder = os.path.expanduser("~/Downloads/Officeパスワード解除希望ファイル")
    output_folder = os.path.join(base_folder, "パスワード解除済みファイル")
    
    # ベースフォルダが存在しない場合は作成
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)
        print(f"📁 フォルダを作成しました： {base_folder}")
    
    # 出力フォルダが存在しない場合は作成
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"📁 フォルダを作成しました： {output_folder}")
    
    return output_folder

def process_file(input_file, output_folder, password=None):
    """個別のファイルを処理"""
    global CURRENT_INDEX, TOTAL_FILES
    try:
        filename = os.path.basename(input_file)
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_解除{ext}"
        output_path = os.path.join(output_folder, output_filename)

        with open(input_file, "rb") as f:
            office_file = msoffcrypto.OfficeFile(f)

            # 暗号化されていない場合はコピー
            if not office_file.is_encrypted():
                print(f"🔓 保護なし： {filename}")
                if CURRENT_INDEX and TOTAL_FILES:
                    print(f"処理状況: 全{TOTAL_FILES}件中 {CURRENT_INDEX}件目")
                if os.path.exists(output_path):
                    print(f"⚠️ 出力先に既存ファイルあり： {output_path}")
                    choice = input("  1: 上書き保存  2: 既存ファイルを保持  (1/2): ")
                    if choice == '1':
                        f.seek(0)
                        with open(output_path, "wb") as out:
                            out.write(f.read())
                        print(f"✅ 上書き保存しました： {output_path}")
                    else:
                        print(f"⏭️ 既存ファイルを保持： {output_path}")
                else:
                    f.seek(0)
                    with open(output_path, "wb") as out:
                        out.write(f.read())
                    print(f"✅ 保存しました： {output_path}")
                os.remove(input_file)
                return True

            # 暗号化されている場合はパスワード解除を試みる
            if password:
                try:
                    office_file.load_key(password=password)
                    print(f"🔐 解除対象： {filename}")
                    if CURRENT_INDEX and TOTAL_FILES:
                        print(f"処理状況: 全{TOTAL_FILES}件中 {CURRENT_INDEX}件目")
                    if os.path.exists(output_path):
                        print(f"⚠️ 出力先に既存ファイルあり： {output_path}")
                        choice = input("  1: 上書き保存  2: 既存ファイルを保持  (1/2): ")
                        if choice == '1':
                            with open(output_path, "wb") as out:
                                office_file.decrypt(out)
                            print(f"✅ 上書き保存しました： {output_path}")
                        else:
                            print(f"⏭️ 既存ファイルを保持： {output_path}")
                    else:
                        with open(output_path, "wb") as out:
                            office_file.decrypt(out)
                        print(f"✅ 解除成功： {output_path}")
                    os.remove(input_file)
                    return True
                except Exception:
                    return False
            else:
                return False

    except Exception:
        print(f"❌ 処理失敗： {filename}")
        return False

def get_password(prompt):
    """パスワード入力用"""
    print(prompt, end='', flush=True)
    return input()

def main():
    output_folder = create_output_folder()
    base_folder = os.path.expanduser("~/Downloads/Officeパスワード解除希望ファイル")

    # 入力フォルダ内の全ファイルを取得
    all_files = [
        os.path.join(base_folder, f)
        for f in os.listdir(base_folder)
        if os.path.isfile(os.path.join(base_folder, f))
           and not f.startswith('.')
    ]

    if not all_files:
        print("処理対象のファイルが見つかりません。")
        sys.exit(1)

    print("\n処理対象のファイル:")
    for path in all_files:
        ext = os.path.splitext(path)[1].lower()
        name = os.path.basename(path)
        if ext in ('.xls', '.xlsx', '.xlsm'):
            print(f"【Excel】パスワード解除対象 → {name}")
        else:
            print(f"【その他】ファイル移動 → {name}")

    if input("\n処理を開始しますか？ (y/n): ").lower() != 'y':
        sys.exit(0)

    password = get_password("パスワードを入力してください（共通パスワードがある場合）： ")
    failed = []

    TOTAL_FILES = len(all_files)
    # 全ファイル処理
    for idx, path in enumerate(all_files, start=1):
        CURRENT_INDEX = idx
        ext = os.path.splitext(path)[1].lower()
        if ext not in ('.xls', '.xlsx', '.xlsm'):
            shutil.move(path, output_folder)
            print(f"📦 非Excelファイル移動： {os.path.basename(path)}")
        else:
            if not process_file(path, output_folder, password):
                failed.append(path)

    # パスワード再試行
    max_trials = 5
    attempt = 1
    while failed and attempt < max_trials:
        print(f"\n{attempt+1}回目の試行（失敗ファイル数: {len(failed)}）")
        choice = input("1: 続行  2: 終了  > ")
        if choice == '2':
            break
        password = get_password(f"パスワード（{attempt+1}回目）： ")
        current = failed.copy()
        failed.clear()
        for path in current:
            if not process_file(path, output_folder, password):
                failed.append(path)
        attempt += 1

    # 結果表示
    if failed:
        print("\n解除できなかったファイル：")
        for path in failed:
            print(f"- {os.path.basename(path)}")
    else:
        print("\n入力フォルダには失敗ファイルのみが残っています。")

if __name__ == "__main__":
    main()