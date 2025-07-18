---
title: "Dockerのインストールと設定ガイド"
created: "[[2025-07-19]]"
tags:
  - "Docker"
  - "環境構築"
  - "AWS SAM"
  - "解説"
---

# Dockerのインストールと設定ガイド

AWS SAMを使ってローカルで開発を進める際に「Dockerが必要」というエラーが出た場合の対処法を解説します。

## なぜDockerが必要なの？

AWS SAMの `local` コマンド（`start-api`など）は、AWSのLambda関数をあなたのPC上で忠実に再現するために、**Dockerコンテナ**という技術を使います。

- **Dockerとは？**: アプリケーションを「コンテナ」という隔離された箱に入れて動かすための技術です。
- **なぜSAMで使う？**: この「箱」がAWSのクラウド環境とそっくりなため、開発中のコードがクラウド上でも同じように動くことを保証してくれます。

```mermaid
---
title: DockerとSAMの関係
---
graph TD
    subgraph "あなたのMac"
        A["sam local start-api コマンド実行"] --> B{Dockerは起動してる？};
        B -- Yes --> C["Dockerコンテナ（Lambdaのそっくりさん）を起動"];
        C --> D["コンテナ内でPythonコードを実行"];
        B -- No --> E[<font color=red>エラー！</font>];
    end

    subgraph "AWSクラウド"
        F["実際のLambda環境"]
    end

    C -.-> F;
    style C fill:#f9f,stroke:#333,stroke-width:2px
```

## インストール手順 (Mac)

1.  **Docker Desktopのダウンロード**
    以下の公式サイトから、あなたのMacに合ったDocker Desktopをダウンロードします。
    - [Docker公式サイト：Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
    - 通常は「Apple Chip」（M1, M2, M3など）か「Intel Chip」かを選択します。

2.  **インストール**
    ダウンロードした `.dmg` ファイルを開き、DockerアイコンをApplicationsフォルダにドラッグ＆ドロップしてインストールします。

3.  **Dockerの起動**
    アプリケーションフォルダから「Docker」を起動します。初回起動時は利用規約への同意などが求められる場合があります。

4.  **起動の確認**
    メニューバーにクジラのアイコンが表示され、クリックして「Docker Desktop is running」と表示されていれば起動成功です。

    ![Dockerメニューバーアイコン](https://docs.docker.com/desktop/images/whale-menu-running.png)

## インストール後の再挑戦

Docker Desktopが「running」状態になったことを確認したら、もう一度ターミナルに戻り、プロジェクトのルートディレクトリ (`Excel_Password`) で以下のコマンドを再実行してください。

```bash
sam local start-api
```

今度はDockerが起動しているため、SAMは正常にローカルサーバーを起動できるはずです。
