# standard.db チートシート（SQL / tidyverse / pandas）

## 0. スキーマ前提

* **企業マスタ**: `Companies`（PK: `NCODE`） 
* **財務データ**: `Standard`（PK: `std_id`、FK: `NCODE`、`年度`/`決算期`/`決算月数` など） 
* **財務指標**: `Ratios`（PK/FK: `std_id`、`ROA`/`ROE`/…） 
* **分析用ビュー**: `view_primary`（`Standard × Companies × Ratios` を結合し、**`決算月数=12` のみ**、既に `ORDER BY NCODE, 決算期`） 

> **実務ルール**：まず `view_primary` を使い、詳細科目が必要なら `std_id` で `Standard` を追加 join。 

---

## 1. 操作対応表（SQL / tidyverse / pandas）

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
    view_primary_df
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
    view_primary_df
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
    view_primary_df
    .melt(
        id_vars=["NCODE","年度","企業名","決算期"],
        value_vars=rat_cols,
        var_name="指標",
        value_name="値"
    )
)
```
