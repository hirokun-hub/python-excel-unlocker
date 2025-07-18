---
created: "[[2025-07-21]]"
aliases: "AWS SAM CLI インストールガイド"
tags:
  - "AWS"
  - "SAM CLI"
  - "手順書"
  - "環境構築"
  - "macOS"
  - "Windows"
---

# 【出力】手順書_AWS SAM CLIのインストールガイド (macOS & Windows対応)

このドキュメントは、AWSサーバーレスアプリケーションのデプロイに不可欠なツール「AWS SAM CLI」を、macOSまたはWindowsのPCにインストールするための詳細な手順を解説するものです。

以前のインストールで発生した「`brew`コマンドが無い」「時間がかかる処理で不安になる」といった点を解消し、誰でもスムーズに作業を完了できることを目指します。

---

## 1. macOSでのインストール手順

macOSでは、パッケージ管理ツール「Homebrew」を利用したインストールが最も簡単で確実です。

### Step 1-1: Homebrewがインストール済みか確認する

まず、ターミナルを開き、以下のコマンドを実行します。

```bash
brew --version
```

-   **`Homebrew 4.x.x`のようにバージョンが表示された場合**:
    -   Homebrewは既にインストールされています。**Step 1-4**に進んでください。
-   **`zsh: command not found: brew`と表示された場合**:
    -   Homebrewがインストールされていません。次の**Step 1-2**に進んでください。

### Step 1-2: Homebrewをインストールする

`brew`コマンドがなかった場合は、以下のコマンドをターミナルにコピー＆ペーストして実行し、Homebrewをインストールします。

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**【非常に重要な注意点】**
-   このコマンドを実行すると、途中でPCのパスワードの入力を求められることがあります。
-   インストールの一部として「Xcode Command Line Tools」のダウンロードとインストールが自動的に開始されます。
-   **このXcodeのインストールは、お使いのネットワーク環境によっては5分〜15分以上、画面に何も進捗が表示されないまま時間がかかることがあります。**
-   処理が止まっているように見えても、バックグラウンドではインストールが進行しています。**途中で中断せず、気長に完了するまで待ってください。**

### Step 1-3: Homebrewのパスを設定する

Homebrewのインストールが完了すると、ターミナルの最後に「Next steps:」として、実行すべきコマンドが表示されます。これは、`brew`コマンドをどこからでも呼び出せるようにするための設定です。

表示された2つのコマンドを、1行ずつ順番に実行してください。

```bash
# このコマンドはmacOSのバージョン等によって表示が若干異なる場合があります。
# 必ず、ご自身のターミナルに表示されたコマンドをコピーして実行してください。
(echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### Step 1-4: AWS SAM CLIをインストールする

Homebrewの準備が整ったら、いよいよSAM CLIをインストールします。以下の2つのコマンドを順番に実行してください。

1.  **AWSの公式リポジトリを追加します。**
    ```bash
    brew tap aws/tap
    ```

2.  **SAM CLIをインストールします。**
    ```bash
    brew install aws-sam-cli
    ```

### Step 1-5: インストールを確認する

最後に、以下のコマンドを実行して、SAM CLIのバージョンが表示されれば、macOSでのインストールはすべて完了です。

```bash
sam --version
```
> SAM CLI, version 1.142.1  (このように表示されれば成功です)

---

## 2. Windowsでのインストール手順

Windowsでは、公式サイトからインストーラー（.msiファイル）をダウンロードして実行するのが最も簡単です。

### Step 2-1: インストーラーをダウンロードする

以下のリンクをクリックして、64bit版のAWS SAM CLIインストーラーをダウンロードします。

-   [AWS SAM CLI for Windows (64-bit) ダウンロードリンク](https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-msi-x86_64.msi)

### Step 2-2: インストールを実行する

ダウンロードした `.msi` ファイルをダブルクリックして実行し、画面の指示に従ってインストールを進めてください。基本的には「Next」をクリックしていけば問題ありません。

### Step 2-3: インストールを確認する

インストールが完了したら、**一度すべてのコマンドプロンプトやPowerShellを閉じ、新しく開き直して**から、以下のコマンドを実行します。

```bash
sam --version
```
> SAM CLI, version 1.142.1  (このように表示されれば成功です)

以上で、Windowsでのインストールは完了です。 