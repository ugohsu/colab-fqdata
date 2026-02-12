# 財務データ可視化チートシート (Visualization Cookbook)

`colab-fqdata` のデータを R (ggplot2) と Python (matplotlib / seaborn) で可視化するための、シンプルで実践的なレシピ集です。

---

## 1. 基本文法

### 1.1 R: ggplot2

`ggplot()` でキャンバスを作り、`geom_xxx()` でグラフを重ねていくスタイルです。

```r
library(tidyverse)

# 基本形: データと軸を指定して、箱ひげ図を重ねる
ggplot(data = df, mapping = aes(x = 年度, y = ROA)) +
  geom_boxplot()

```

### 1.2 Python: matplotlib + seaborn

`plt.subplots()` で枠（ax）を作り、そこに `sns.xxx(..., ax=ax)` で描画し、最後に `plt.show()` で表示するスタイルです。

```python
import matplotlib.pyplot as plt
import seaborn as sns

# 基本形: 枠を作って、箱ひげ図を描く
fig, ax = plt.subplots()
sns.boxplot(data=df, x="年度", y="ROA", ax=ax)
plt.show()

```

---

## 2. 実践レシピ

### 2.1 時系列推移の比較（折れ線グラフ）

特定業種の ROA（中央値）の推移を比較する、基本的な折れ線グラフの例です。

**R (tidyverse)**

```r
# 1. データ準備
target_inds <- c("食品", "医薬品", "小売業")

df_trend <- df %>%
    filter(
        日経業種中分類名 %in% target_inds,
        年度 >= 2020, 年度 <= 2024
    ) %>%
    group_by(年度, 日経業種中分類名) %>%
    summarise(ROA_median = median(ROA, na.rm = TRUE), .groups = "drop")

# 2. 描画
ggplot(df_trend, aes(x = 年度, y = ROA_median, color = 日経業種中分類名)) +
    geom_line() +
    scale_x_continuous(breaks = 2020:2024)

```

**Python (matplotlib + seaborn)**

```python
# 1. データ準備
target_inds = ["食品", "医薬品", "小売業"]

df_trend = (
    df
    .loc[lambda x:
        (x["日経業種中分類名"].isin(target_inds)) &
        (x["年度"] >= 2020) & (x["年度"] <= 2024)
    ]
    .groupby(["年度", "日経業種中分類名"], as_index=False)
    .agg(ROA_median=("ROA", "median"))
)

# 2. 描画
fig, ax = plt.subplots(figsize=(8, 5))

sns.lineplot(
    data=df_trend, 
    x="年度", y="ROA_median", 
    hue="日経業種中分類名", 
    ax=ax
)

ax.set_xticks(range(2020, 2025))
plt.show()

```


### 2.2 分布と特定企業の強調

「業界全体の分布」を箱ひげ図で示し、その中に「自社」がどこに位置するかを赤点で重ねて表示します。

**R (tidyverse)**

```r
# 1. まず「業界」に絞る
df_industry <- df %>% 
    filter(日経業種小分類名 == "電設工事")

# 2. その中から「自社」を取り出す
target <- df_industry %>% 
    filter(企業名 == "株式会社サクラ")

df_industry %>%
    ggplot(aes(x = factor(年度), y = 流動比率)) +
    # A. 全体分布 (箱ひげ + 点)
    # outlier.shape = NA: 箱ひげの外れ値を消す（下の jitter で描画されるため）
    geom_boxplot(outlier.shape = NA) +
    geom_jitter(width = 0.2, color = "gray", alpha = 0.5) +
    # B. 強調 (赤点)
    geom_point(data = target, color = "red", size = 3)

```

**Python (matplotlib + seaborn)**

```python
# 1. まず「業界」に絞る
df_industry = df.loc[lambda x: x["日経業種小分類名"] == "電設工事"]

# 2. その中から「自社」を取り出す
target = df_industry.loc[lambda x: x['企業名'] == '株式会社サクラ']

fig, ax = plt.subplots(figsize=(8, 5))

# A. 全体分布 (箱ひげ + 点)
# showfliers=False: 箱ひげの外れ値を消す（点で描画されるため）
sns.boxplot(data=df_industry, x='年度', y='流動比率', showfliers=False, color='white', ax=ax)
sns.stripplot(data=df_industry, x='年度', y='流動比率', color='gray', alpha=0.5, ax=ax)

# B. 強調 (赤点)
# zorder=10 で最前面に表示
sns.stripplot(data=target, x='年度', y='流動比率', color='red', size=10, zorder=10, ax=ax)

plt.show()

```
