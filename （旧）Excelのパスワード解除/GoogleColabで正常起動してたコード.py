# ライブラリのインストールとインポート
!pip install msoffcrypto-tool
from google.colab import drive
from google.colab import files
import msoffcrypto
from getpass import getpass
import os

# Googleドライブのマウント
drive.mount('/content/drive')

# 保存先のフォルダパスを設定
output_folder = '/content/drive/MyDrive/パスワード解除済みファイル'

# 保存先のフォルダが存在しない場合は作成
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"📁 フォルダを作成しました： {output_folder}")

# 共通パスワードの入力（入力内容は非表示）
password = getpass("パスワードを入力してください（共通パスワードがある場合）： ")

# ファイルのアップロード（複数ファイル選択可）
uploaded = files.upload()

# アップロードされたファイルのパスを取得
uploaded_files = list(uploaded.keys())

# 解除できなかったファイルのリスト
failed_files = []

# 最初にすべてのファイルに対して共通パスワードを試す
for input_filename in uploaded_files:
    try:
        # 入力ファイルのパス
        input_file = input_filename

        # 入力ファイルの名前と拡張子を取得
        input_name, input_ext = os.path.splitext(input_filename)

        # 出力ファイルのパスを作成（元のファイル名に「_解除」を追加）
        output_filename = f"{input_name}_解除{input_ext}"
        output_file = os.path.join(output_folder, output_filename)

        with open(input_file, "rb") as file_in:
            office_file = msoffcrypto.OfficeFile(file_in)

            # ファイルが暗号化されているか確認
            if not office_file.is_encrypted():
                print(f"🔓 ファイルはパスワード保護されていません： {input_filename}。そのまま保存します。")
                # ファイルを保存先フォルダにコピー
                file_in.seek(0)
                with open(output_file, "wb") as file_out:
                    file_out.write(file_in.read())
                print(f"✅ ファイルを保存しました： {output_file}")
                continue

            # 共通パスワードを試す
            try:
                office_file.load_key(password=password)
                with open(output_file, "wb") as file_out:
                    office_file.decrypt(file_out)
                print(f"✅ パスワード解除に成功しました。ファイルを保存しました： {output_file}")
            except Exception as e:
                # 共通パスワードで解除できなかったファイルをリストに追加
                failed_files.append(input_filename)
    except Exception as e:
        print(f"❌ エラーが発生しました。ファイルを処理できませんでした： {input_filename}")
        failed_files.append(input_filename)

# 共通パスワードで解除できなかったファイルに対して個別にパスワードを入力
for input_filename in failed_files[:]:
    try:
        input_file = input_filename
        input_name, input_ext = os.path.splitext(input_filename)
        output_filename = f"{input_name}_解除{input_ext}"
        output_file = os.path.join(output_folder, output_filename)

        with open(input_file, "rb") as file_in:
            office_file = msoffcrypto.OfficeFile(file_in)

            # パスワードを再入力
            new_password = getpass(f"パスワードを入力してください： {input_filename}： ")
            try:
                office_file.load_key(password=new_password)
                with open(output_file, "wb") as file_out:
                    office_file.decrypt(file_out)
                print(f"✅ パスワード解除に成功しました。ファイルを保存しました： {output_file}")
                failed_files.remove(input_filename)
            except Exception as e:
                print(f"❌ パスワードが正しくありません： {input_filename}")
    except Exception as e:
        print(f"❌ エラーが発生しました。ファイルを処理できませんでした： {input_filename}")

# 解除できなかったファイルの一覧を表示
if failed_files:
    print("\nパスワードを解除できなかったファイル：")
    for file in failed_files:
        print(f"- {file}")
else:
    print("\nすべてのファイルのパスワード解除に成功しました。")
