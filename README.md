# Colab FQ Data Loader

このリポジトリは、**Google Colaboratory 上で、『日経 NEEDS-FinancialQUEST』(日本経済新聞社) から取得したデータを効率的に読み込み、分析するための関数・解説ドキュメント**をまとめた教材用リポジトリです。

構築済みの財務データベース（SQLite形式）から、必要な企業・年度のデータを抽出したり、Google スプレッドシートへ書き出したりする一連の処理をサポートします。

---

## クイックスタート（Python を書かずに利用する場合）

「とりあえずデータを抽出したい」「Python のコードはあまり書きたくない」という場合は、用意されている**テンプレートノートブック**をご利用ください。

### 手順

1. **Google Colab を開く**
    * ブラウザで [Google Colab](https://colab.research.google.com/) にアクセスします。


2. **ノートブックを開く**
    * メニューから **[ファイル]** > **[ノートブックを開く]** を選択します。
    * ポップアップ画面で **[GitHub]** タブを選択します。
    * 検索ボックスにリポジトリの URL（または `ugohsu/colab-fqdata`）を入力して検索します。


3. **テンプレートを選択**
    * 表示されたファイル一覧から、以下のファイルを選択して開きます。
    * `templates/fq_loader_template.ipynb`


このノートブックには、ライブラリのインストールからデータの抽出、Google スプレッドシートへの保存までの手順があらかじめ記述されています。画面の指示に従って設定項目（DBのURLなど）を入力し、セルを上から順に実行するだけでデータ抽出が可能です。

---

## ライブラリインポートの手順（Python コードで利用する場合）

ご自身の分析用ノートブックで、本リポジトリの関数をライブラリとして使用するための手順は次のとおりです。

### 1. リポジトリを clone

本ライブラリは `colab-common`（共通機能）に依存しているため、両方を clone します。

```python
## colab-common (依存ライブラリ)
!git clone https://github.com/ugohsu/colab-common.git

## colab-fqdata (本ライブラリ)
!git clone https://github.com/ugohsu/colab-fqdata.git

```

### 2. import 用のパスを追加

```python
import sys
sys.path.append("/content/colab-common")
sys.path.append("/content/colab-fqdata")

```

### 3. クラスを import (例)

```python
from colab_fqdata import FqLoader

```

---

### 注意（Google Colab での git clone）

同一ノートブック内で同一リポジトリに対する `git clone` を **2 回以上実行しないでください**。

```
fatal: destination path 'colab-fqdata' already exists

```

というエラーが発生し、そのセルでは、当該行以降のコードが実行されなくなります。

---

## 機能一覧（import して使う）

| 分類 | クラス・関数名 | 内容 | 実装ファイル |
| --- | --- | --- | --- |
| **I/O** | `FqLoader` | 財務DBへの接続・SQL実行・データフレーム化を行うメインクラス。接続時に取得時点・件数などのビルド情報（`Meta`テーブル）を自動で1行表示します | [`colab_fqdata/fq_loader.py`](colab_fqdata/fq_loader.py) |
| **I/O** | `FqLoader.read_sql` | SQLを実行してDataFrameを取得（証券コードリストによるフィルタリング機能付き） | [`colab_fqdata/fq_loader.py`](colab_fqdata/fq_loader.py) |
| **I/O** | `FqLoader.info` | DBのビルド情報（取得時点・収録期間・企業数・観測数など）を表示・取得 | [`colab_fqdata/fq_loader.py`](colab_fqdata/fq_loader.py) |

---

## ドキュメント一覧

| 分類 | 内容 | ドキュメント |
| --- | --- | --- |
| **Schema** | データベース定義書（テーブル構造・カラム定義・ER図） | [`docs/standard_schema.md`](docs/standard_schema.md) |
| **Release notes** | `standard.db` の再構築履歴（スキーマ変更・既知の問題） | [`docs/db_release_notes.md`](docs/db_release_notes.md) |
| **Cookbook** | 財務データ操作クックブック（SQL / R / Python 対応表・レシピ集） | [`docs/query_cookbook.md`](docs/query_cookbook.md) |
| **Cookbook** | 財務データ可視化クックブック（ggplot2 / matplotlib / seaborn） | [`docs/visualization_cookbook.md`](docs/visualization_cookbook.md) |
| **Cookbook** | 前処理クックブック (R / Python) | [`docs/preprocess_cookbook.md`](docs/preprocess_cookbook.md) |

---

## このデータベース（`standard.db`）について

* **データ源**: 日経 NEEDS-FinancialQUEST（日本経済新聞社）。大学の契約に基づき利用しています。
* **対象企業ユニバース**: テーブルによって対象範囲が異なります。
    * `Companies`: 一般事業会社に加えて上場企業（銀行・証券・保険を含む）全社をマージした、広いユニバース。
    * `Standard` / `Ratios`: 一般事業会社（銀行・証券・保険等を除いた有価証券報告書提出会社）のみ。金融機関などは `Companies` に情報があっても、こちらには財務データが存在しません。
* **収録期間・件数**: このREADMEには具体的な数値は書きません。`standard.db` は年1回程度再構築される配布物のため、数値を書くと実体とズレてしまいます。**必ず配布されたDB自身から確認してください**（下記コード例参照）。
* **利用条件**: 🚧 本データは大学との契約に基づき提供されるものであり、教育・研究目的での利用に限ります。学外への再配布はできません。

### 取得時点・収録範囲・件数を確認する

`standard.db` には `Meta` テーブル（ビルド情報）が同梱されています。`FqLoader` で接続すると内容が自動で1行表示されますが、論文等に記載する際は `info()` で全項目を確認してください。

```python
from colab_fqdata import FqLoader
loader = FqLoader(DB_URL)
loader.info()  # 取得時点・収録期間・企業数・観測数などを表示
```

詳細なカラム定義は [`docs/standard_schema.md`](docs/standard_schema.md) を参照してください（3つの主要テーブル + `Meta` テーブルの全カラムを定義しています）。

### 主な利用フロー

1. **DB接続**: Google Drive 上（またはローカル）の SQLite データベースファイルを指定して `FqLoader` を初期化します。
2. **クエリ実行**: 必要なデータを抽出するための SQL クエリを作成します。
3. **フィルタリング（任意）**: 特定の銘柄群（証券コードリスト）のみを抽出対象とする場合、リストを渡すことで自動的にフィルタリングを行います。
4. **データ取得**: 結果は `pandas.DataFrame` として返されるため、そのまま Python 上で分析・可視化に使用したり、`colab-common` を使ってスプレッドシートへ出力したりできます。

---

## ライセンス・利用について

* 教育・研究目的での利用を想定しています
* 講義資料・演習ノートへの組み込みも自由です
