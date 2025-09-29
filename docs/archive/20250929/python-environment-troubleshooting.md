# Python環境管理問題の解決ガイド

## 🚨 問題の概要

macOS環境でPython依存関係のインストール時に以下のエラーが発生する場合があります：

```
error: externally-managed-environment
× This environment is externally managed
```

これは、macOSのシステムPython環境が外部管理されているため、直接パッケージをインストールできないことを意味します。

## 🛡️ 安心してください

- ✅ この問題は一般的で、解決可能です
- ✅ あなたのシステムは安全です
- ✅ 以下の方法で確実に解決できます
- ✅ 何も壊れる心配はありません

## 🔧 解決方法

### 方法1: 仮想環境（venv）の使用（推奨）

```bash
# 1. プロジェクトディレクトリに移動
cd /path/to/excel-unlocker

# 2. 仮想環境を作成
python3 -m venv venv

# 3. 仮想環境をアクティベート
source venv/bin/activate

# 4. 依存関係をインストール
pip install -r scripts/requirements.txt

# 5. セットアップスクリプトを実行
./scripts/setup-integrated-deployment.sh
```

### 方法2: pipxの使用

```bash
# 1. Homebrewでpipxをインストール
brew install pipx

# 2. pipxのパスを設定
pipx ensurepath

# 3. 必要なパッケージをpipxでインストール
pipx install jsonschema
pipx install cryptography
pipx install PyYAML

# 4. セットアップスクリプトを実行（pipxモードで自動実行）
./scripts/setup-integrated-deployment.sh
```

### 方法3: Homebrewが未インストールの場合

```bash
# 1. Homebrewをインストール
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. pipxをインストール
brew install pipx

# 3. 方法2の手順を続行
```

## 🔍 問題の診断

### 現在のPython環境を確認

```bash
# Pythonのバージョンと場所を確認
python3 --version
which python3

# pip環境を確認
pip3 --version
which pip3

# 仮想環境の状態を確認
echo $VIRTUAL_ENV
```

### エラーメッセージの確認

```bash
# 詳細なエラーメッセージを確認
pip3 install jsonschema 2>&1 | head -20
```

## 🎯 自動解決機能

セットアップスクリプトには自動解決機能が組み込まれています：

1. **仮想環境の自動作成**: venvディレクトリが存在しない場合、自動で作成
2. **pipxフォールバック**: 仮想環境が失敗した場合、pipxを使用
3. **基本的な環境変数生成**: Python依存関係が利用できない場合のフォールバック

## 📋 トラブルシューティング

### よくある問題と解決方法

#### 問題: `python3: command not found`

```bash
# Homebrewでpython3をインストール
brew install python3

# または、公式サイトからダウンロード
# https://www.python.org/downloads/
```

#### 問題: `brew: command not found`

```bash
# Homebrewをインストール
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# パスを設定（M1/M2 Macの場合）
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
source ~/.zshrc
```

#### 問題: 仮想環境のアクティベートに失敗

```bash
# 仮想環境を削除して再作成
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

#### 問題: 権限エラー

```bash
# ディレクトリの権限を確認
ls -la
chmod 755 scripts/setup-integrated-deployment.sh

# 必要に応じてsudoを使用（推奨しません）
# sudo pip3 install -r scripts/requirements.txt
```

## 🚀 成功の確認

以下のコマンドで正常にインストールされたことを確認できます：

```bash
# 仮想環境内で確認
source venv/bin/activate
python3 -c "import jsonschema, cryptography; print('✅ 依存関係が正常にインストールされました')"

# pipxで確認
pipx list
```

## 💡 予防策

今後同様の問題を避けるために：

1. **常に仮想環境を使用**: プロジェクトごとに独立した環境を作成
2. **pipxの活用**: グローバルツールはpipxでインストール
3. **定期的な更新**: Python、pip、Homebrewを定期的に更新

## 📞 サポート

問題が解決しない場合：

1. **ログファイルを確認**: `setup-integrated-deployment.log`
2. **詳細なエラーメッセージを収集**: 上記の診断コマンドを実行
3. **環境情報を収集**: OS、Python、Homebrewのバージョン
4. **サポートに連絡**: 収集した情報と共にサポートチームに連絡

## 🔗 関連リンク

- [Python公式サイト](https://www.python.org/)
- [Homebrew公式サイト](https://brew.sh/)
- [pipx公式ドキュメント](https://pypa.github.io/pipx/)
- [Python仮想環境ガイド](https://docs.python.org/3/tutorial/venv.html)