# 財務データ操作クックブック (Query Cookbook)

このドキュメントは、`colab-fqdata` のデータを SQL、Python (pandas)、R (tidyverse) で操作する際の対応表と実践例です。

## 前提: 結合キー早見表

JOIN する際のキーカラムを確認するためのメモです。詳細は `standard_schema.md` を参照してください。

| テーブル | 主キー (PK) | 外部キー (FK) | 備考 |
| --- | --- | --- | --- |
| **Companies** | `NCODE` | - | 企業属性 |
| **Standard** | `std_id` | `NCODE` | 財務数値 |
| **Ratios** | `std_id` | - | Standard と 1:1 で結合 |

---

## 1. 操作対応表（SQL / tidyverse / pandas）

前提: 以下のライブラリの読み込みが必要です

R tidyverse 

```r
library(tidyverse)
```

Python pandas 

```python
import pandas as pd
import numpy as np
```

| SQL                                | tidyverse                         | pandas                                               | Python（pandas）実務メモ                           |
| ---------------------------------- | --------------------------------- | ---------------------------------------------------- | -------------------------------------------- |
| `WHERE 年度 >= 2020 AND ROA > 0`     | `filter(年度 >= 2020, ROA > 0)`     | `.loc[lambda x: (x["年度"] >= 2020) & (x["ROA"] > 0)]` | `&` / `\|` を使う（and/or不可）。各条件は必ず括弧。           |
| `SELECT NCODE, 年度, ROA`            | `select(NCODE, 年度, ROA)`          | `.loc[:, ["NCODE","年度","ROA"]]`                      | 1列でも `["列"]` とリストで指定すると後工程が安定。               |
| `SELECT *, LOG(ROA) AS logROA`     | `mutate(logROA = log(ROA))`       | `.assign(logROA=lambda x: np.log(x["ROA"]))`         | 既存列を参照するなら `lambda x:` を使う。                  |
| `ORDER BY 年度 ASC, ROA DESC`        | `arrange(年度, desc(ROA))`          | `.sort_values(["年度","ROA"], ascending=[True,False])` | `ascending` は列数と同じ長さのリスト。                    |
| `GROUP BY 年度`                      | `group_by(年度)`                    | `.groupby("年度", as_index=False)`                     | `as_index=False` を付けると tidyverse 的（キーが列に残る）。 |
| `SELECT 年度, AVG(ROA)`              | `summarise(mean_ROA = mean(ROA))` | `.agg(mean_ROA=("ROA","mean"))`                      | 書式は `新列=("対象列","関数")` が最も安定。                 |
| `AVG(ROA) OVER (PARTITION BY 年度)`  | `group_by(年度) %>% mutate(...)`    | `.groupby("年度")["ROA"].transform("mean")`            | `transform` は行数維持、`agg` は行数減少。               |
| `LEFT JOIN ... ON s.NCODE=c.NCODE` | `left_join(..., by="NCODE")`      | `.merge(..., on="NCODE", how="left")`                | キー同名なら `on=`。異名なら `left_on=` / `right_on=`。  |
| **UNPIVOT 相当**：`UNION ALL` で列を縦積み             | `pivot_longer()` | `.melt()`  | `id_vars` を明示すると安全。                     |
| **PIVOT 相当**：`GROUP BY` + `MAX(CASE WHEN...)` | `pivot_wider()`  | `.pivot()` | 重複があると失敗 → `.pivot_table(aggfunc=...)`。 |


---

## 2. `view_primary` を用いる例示

### 2.1 `年度 >= 2020 & ROA > 0` の抽出（filter + select + arrange）

**SQL（view_primary）**

```sql
SELECT NCODE, 年度, 企業名, ROA, 総資産, 売上高, 営業利益, 当期純利益, 決算期
FROM view_primary
WHERE 年度 >= 2020
  AND ROA > 0
ORDER BY 年度 ASC, ROA DESC;
```

**tidyverse**

```r
result <- df %>% # df は view_primary を読み込んだもの
    filter(
        年度 >= 2020, 
        ROA > 0
    ) %>%
    select(
        NCODE, 年度, 企業名, ROA, 総資産, 
        売上高, 営業利益, 当期純利益, 決算期
    ) %>%
    arrange(年度, desc(ROA))
```

**pandas**

```python
result = (
    df
    .loc[lambda x: 
        (x["年度"] >= 2020) &
        (x["ROA"] > 0)
    ]
    .loc[:, ["NCODE","年度","企業名","ROA","総資産","売上高","営業利益","当期純利益","決算期"]]
    .sort_values(["年度","ROA"], ascending=[True, False])
)
```

---

### 2.2 年度ごとの「平均との差ROA」（window / transform）

**SQL**

```sql
SELECT
  NCODE, 年度, 企業名, ROA,
  ROA - AVG(ROA) OVER (PARTITION BY 年度) AS 年度平均との差ROA
FROM view_primary;
```

**tidyverse**

```r
result <- df %>%
  group_by(年度) %>%
  mutate(年度平均との差ROA = ROA - mean(ROA, na.rm = TRUE)) %>%
  ungroup()
```

**pandas**

```python
result = (
    df
    .assign(年度平均との差ROA=lambda x: 
        x["ROA"] - x.groupby("年度")["ROA"].transform("mean")
    )
)
```

---

## 3. join 実例（キーが違うケースも含む）

### 3.1 標準：Standard と Companies（`NCODE` 同名）

**SQL**

```sql
SELECT s.NCODE, s.年度, c.企業名, s.売上高
FROM Standard s
LEFT JOIN Companies c ON s.NCODE = c.NCODE
WHERE s.決算月数 = 12;
```

**tidyverse**

```r
result <- standard_df %>%
  filter(決算月数 == 12) %>%
  left_join(companies_df, by = "NCODE") %>%
  select(NCODE, 年度, 企業名, 売上高)
```

**pandas**

```python
result = (
    standard_df
    .loc[lambda x: x["決算月数"] == 12]
    .merge(companies_df, on="NCODE", how="left")
    .loc[:, ["NCODE","年度","企業名","売上高"]]
)
```

> キーが複数の場合は以下のように指定します。
> * tidyverse: `left_join(..., by=c("key1", "key2"))`
> * pandas: `.merge(..., on=["key1", "key2"])`


### 3.2 異名キー：`Companies.NCODE` と、手元の表が `company_id` のとき

**tidyverse**

```r
result <- your_df %>%
  left_join(companies_df, by = c("company_id" = "NCODE"))
```

**pandas**

```python
result = your_df.merge(companies_df, left_on="company_id", right_on="NCODE", how="left")
```

> キーが複数の場合は以下のように指定します。
> * tidyverse: `left_join(..., by=c("leftkey1" = "rightkey1", "leftkey2" = "rightkey2"))`
> * pandas: `.merge(..., left_on=["leftkey1", "leftkey2"], right_on=["rightkey1", "rightkey2"])`

---

## 4. pivot（Ratios の列を “long化” したい場合）

`view_primary` は `ROA, ROE, ATO, PM, ...` が「列」で入っています。 
これを tidy データ（指標名/値）にする例です。

**tidyverse（pivot_longer）**

```r
long_rat <- df %>%
    pivot_longer(
        cols = c(ROA, ROE, ATO, PM),
        names_to = "指標",
        values_to = "値"
    )
```

**pandas（melt）**

```python
rat_cols = ["ROA","ROE","ATO","PM"]
long_rat = (
    df
    .melt(
        id_vars=["NCODE","年度","企業名","決算期"],
        value_vars=rat_cols,
        var_name="指標",
        value_name="値"
    )
)
```

## 5. pivot（縦持ちデータを “wide化” したい場合）

Section 4 で作ったような tidy データ（指標列・値列）を、元の表形式に戻す例です。

**tidyverse（pivot_wider）**

```r
wide_df <- long_rat %>%
    pivot_wider(
        names_from = "指標",
        values_from = "値"
    )

```

**pandas（pivot / pivot_table）**

```python
# インデックスを一意に特定できる場合（単純な変形）
wide_df = (
    long_rat
    .pivot(
        index=["NCODE", "年度", "企業名", "決算期"],
        columns="指標",
        values="値"
    )
    .reset_index() # index を列に戻す
)

# 重複がある場合や集計が必要な場合（クロス集計など）
wide_df = (
    long_rat
    .pivot_table(
        index=["NCODE"],
        columns="指標",
        values="値",
        aggfunc="mean" # 平均をとるなど
    )
    .reset_index()
)

```

## 6. 要約統計量（describe / summary）

データの分布（平均、標準偏差、四分位数など）を確認します。

### 6.1 基本（全体・年度別）

単純に分布を見るだけなら、デフォルトの関数が便利です。

**tidyverse**

```r
# 全体
df %>% select(ROA, ROE) %>% summary()

# 年度別（リスト形式で出力）
df %>% split(.$年度) %>% map(~ summary(select(., ROA, ROE)))

```

**pandas**

```python
# 全体
df[["ROA", "ROE"]].describe()

# 年度別
df.groupby("年度")[["ROA", "ROE"]].describe()

```

### 6.2 発展：多変量・多重グループの縦持ち集計 (Tidy format)

「年度×業種」などで集計し、結果を扱いやすい「縦持ち（Long）」形式で取得するテクニックです。
結果がきれいなテーブルになるため、そのままグラフ描画やファイル保存に使えます。

**tidyverse**

R では「集計したい変数を先に縦持ちにする」のがコツです。

```r
summary_long <- df %>%
    select(年度, 日経業種中分類名, ROA, ROE) %>%
    # 1. まず集計したい指標を縦に積む
    pivot_longer(cols = c(ROA, ROE), names_to = "指標", values_to = "val") %>%
    # 2. グループ化して集計
    group_by(年度, 日経業種中分類名, 指標) %>%
    summarise(
        mean = mean(val, na.rm = TRUE),
        sd   = sd(val, na.rm = TRUE),
        count = n(),
        .groups = "drop" # ここでグループ化を完全解除
    ) %>%
    # 3. 統計項目も縦に積む（pandasのstack相当）
    pivot_longer(cols = c(mean, sd, count), names_to = "統計項目", values_to = "値")

```

**pandas**

Pandas では `groupby().describe()` で生成される MultiIndex カラムを `stack` で処理します。

```python
# 1. 集計 (カラムが [指標, 統計項目] のMultiIndexになる)
target_cols = ["ROA", "ROE", "自己資本比率", "売上高営業利益率"]
stats = df.groupby(["日経業種中分類名", "年度"])[target_cols].describe()

# 2. stack で列ラベルを行インデックスに移動（縦持ち化）
long_df = stats.stack(level=[0, 1]).reset_index()

# 3. カラム名を整備
long_df.columns = ["日経業種中分類名", "年度", "指標", "統計項目", "値"]

```
