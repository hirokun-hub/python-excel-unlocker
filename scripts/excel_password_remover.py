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
  1. 入力フォルダ内のExcelファイルを検索
  2. ファイルごとに暗号化状態を判定
     - 暗号化されていない場合: コピーして保存
     - 暗号化されている場合: パスワードを使用し解除
  3. 最大5回までパスワード試行
  4. 解除成功ファイルを出力フォルダに保存
  5. 解除失敗ファイルを一覧表示

使用方法:
  python excel_password_remover.py
"""

import msoffcrypto
from getpass import getpass
import os
import sys
import argparse  # コマンドライン引数解析用

def create_output_folder():
    """指定されたパスに出力フォルダを作成"""
    base_folder = os.path.join("/Users/hironomac2025/Library/Mobile Documents/com~apple~CloudDocs/Downloads", "Officeパスワード解除希望ファイル")
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
    try:
        input_name = os.path.basename(input_file)
        input_name, input_ext = os.path.splitext(input_name)
        output_filename = f"{input_name}_解除{input_ext}"
        output_file = os.path.join(output_folder, output_filename)

        # 出力ファイルが既に存在する場合はスキップ
        if os.path.exists(output_file):
            print(f"⏭️ ファイルは既に処理済みです： {input_name}")
            return True

        with open(input_file, "rb") as file_in:
            office_file = msoffcrypto.OfficeFile(file_in)

            if not office_file.is_encrypted():
                print(f"🔓 ファイルはパスワード保護されていません： {input_name}。そのまま保存します。")
                file_in.seek(0)
                with open(output_file, "wb") as file_out:
                    file_out.write(file_in.read())
                print(f"✅ ファイルを保存しました： {output_file}")
                try:
                    os.remove(input_file)
                    print(f"🗑️ 元ファイルを削除しました： {input_file}")
                except Exception as e:
                    print(f"⚠️ 元ファイルの削除に失敗しました： {input_file} ({e})")
                return True

            if password:
                try:
                    office_file.load_key(password=password)
                    with open(output_file, "wb") as file_out:
                        office_file.decrypt(file_out)
                    print(f"✅ パスワード解除に成功しました。ファイルを保存しました： {output_file}")
                    try:
                        os.remove(input_file)
                        print(f"🗑️ 元ファイルを削除しました： {input_file}")
                    except Exception as e:
                        print(f"⚠️ 元ファイルの削除に失敗しました： {input_file} ({e})")
                    return True
                except Exception as e:
                    return False
            else:
                return False

    except Exception as e:
        print(f"❌ エラーが発生しました。ファイルを処理できませんでした： {input_name}")
        return False

def get_excel_files():
    """指定されたフォルダからExcelファイルを取得"""
    base_folder = os.path.join("/Users/hironomac2025/Library/Mobile Documents/com~apple~CloudDocs/Downloads", "Officeパスワード解除希望ファイル")
    if not os.path.exists(base_folder):
        print(f"❌ フォルダが見つかりません： {base_folder}")
        return []

    excel_files = []
    for file in os.listdir(base_folder):
        if file.lower().endswith(('.xls', '.xlsx', '.xlsm')):
            excel_files.append(os.path.join(base_folder, file))

    return excel_files

def get_password(prompt):
    """パスワードを入力し、黒丸を表示"""
    print(prompt, end='', flush=True)
    password = input()
    return password

def main():
    """
    メイン処理関数。コマンドライン引数で --yes/-y を指定すると、
    確認入力なしで自動的に処理を開始します。
    """
    # argparseでコマンドライン引数を取得
    parser = argparse.ArgumentParser(description="Excelファイルのパスワード解除ツール")
    parser.add_argument("-y", "--yes", action="store_true", help="確認なしで自動実行する")
    args = parser.parse_args()
    # 出力フォルダの作成
    output_folder = create_output_folder()
    
    # Excelファイルの取得
    excel_files = get_excel_files()
    
    if not excel_files:
        print("処理対象のExcelファイルが見つかりません。")
        print("~/Downloads/Officeパスワード解除希望ファイル フォルダにExcelファイルを配置してください。")
        sys.exit(1)

    print("\n処理対象のファイル:")
    for file in excel_files:
        print(f"- {os.path.basename(file)}")

    # コマンドライン引数 --yes/-y が指定されていれば自動実行
    if args.yes:
        proceed = 'y'
    else:
        proceed = input("\n処理を開始しますか？ (y/n): ").lower()
    if proceed != 'y':
        sys.exit(0)

    # 共通パスワードの入力
    password = get_password("パスワードを入力してください（共通パスワードがある場合）： ")

    # 解除できなかったファイルのリスト
    failed_files = []

    # 最初にすべてのファイルに対して共通パスワードを試す
    for input_file in excel_files:
        if not process_file(input_file, output_folder, password):
            failed_files.append(input_file)

    # パスワード試行回数の制御
    max_attempts = 5
    attempt = 1

    while failed_files and attempt < max_attempts:
        print(f"\n{attempt + 1}回目のパスワード試行")
        print(f"解除できなかったファイル数: {len(failed_files)}")
        print("1: パスワードを入力して続行")
        print("2: 処理を終了")
        
        choice = input("選択してください (1/2): ")
        
        if choice == "2":
            break
            
        new_password = get_password(f"パスワードを入力してください（{attempt + 1}回目）： ")
        
        # 現在の失敗リストのコピーを作成
        current_failed = failed_files.copy()
        failed_files = []  # 失敗リストをリセット
        
        for input_file in current_failed:
            if not process_file(input_file, output_folder, new_password):
                failed_files.append(input_file)
        
        attempt += 1

    # 解除できなかったファイルの一覧を表示
    if failed_files:
        print("\nパスワードを解除できなかったファイル：")
        for file in failed_files:
            print(f"- {os.path.basename(file)}")
    else:
        print("\nすべてのファイルのパスワード解除に成功しました。")

if __name__ == "__main__":
    main() 