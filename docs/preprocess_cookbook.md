# 前処理クックブック

## 前処理：外れ値処理 (Outlier Handling)

財務データには、極端に大きな値（異常値）が含まれることがよくあります。
本リポジトリでは、財務データ分析で広く用いられる以下の手法を例示します。 

1. **Trimming (除外):** 指定した範囲を超えるデータを行ごと削除する手法。異常値を「エラー」とみなす場合に適しています。
2. **Winsorizing (畳み込み):** 指定した範囲を超えるデータを、その境界値に置き換える手法。サンプル数を減らしたくない場合に適しています。

いずれの手法も、**「年度 × 業種」ごとに適用する** ことが可能です。

外れ値処理の方法およびカット割合は、研究分野や目的によって異なります。本リポジトリでは代表的な設定例を示しますが、分析設計に応じて適切に調整してください。

---

### レシピ 1: Trimming (データをカットする)

**概要:**
業種（`CLUSTER`）ごとに、指定した指標の上下 1%（`PROBS`）を外れ値とみなし、その行を抽出（または除外）します。

- ※ 欠損値 (`NA`) は外れ値ではないため、そのまま保持します。
- ※ カット割合は研究目的に応じて調整してください

**R (tidyverse)**

```r
library(tidyverse)

# 例: 業種ごとに ROA の上下 1% を残す (範囲外を除外)
df_trimmed <- df %>%
    group_by(年度, 日経業種中分類名) %>%
    filter(
        # NAは保持 | 下限より大きい & 上限より小さい
        is.na(ROA) | 
        (ROA > quantile(ROA, 0.01, na.rm = TRUE) & 
        ROA < quantile(ROA, 0.99, na.rm = TRUE))
    ) %>%
    ungroup()

```

**Python (pandas)**

```python
import numpy as np

def get_trim_mask(df, col, group_cols, limits=[0.01, 0.01]):
    """
    業種ごとの分位点を計算し、範囲内(True)のマスクを返す関数
    limits=[0.01, 0.01] のように指定。0 は「カットなし」として扱います。
    """
    # 1. 下限の閾値を計算 (0 なら -inf で制限なし)
    lower_limit = (
        df.groupby(group_cols)[col].transform(lambda x: x.quantile(limits[0]))
        if limits[0] > 0 else -np.inf
    )

    # 2. 上限の閾値を計算 (0 なら inf で制限なし)
    upper_limit = (
        df.groupby(group_cols)[col].transform(lambda x: x.quantile(1 - limits[1]))
        if limits[1] > 0 else np.inf
    )

    # 3. 判定 (範囲内 または NA なら True)
    # 不等号は厳密 (>) なので、境界値自体は除外されます (0 を「カットなし」として扱うための設定)
    return ((df[col] > lower_limit) & (df[col] < upper_limit)) | df[col].isna()

# --- 実行例 ---

# 複数の変数に対して個別の条件でマスクを作成
mask_roa = get_trim_mask(df, "ROA", group_cols=["年度", "日経業種中分類名"], limits=[0.01, 0.01])
mask_sales = get_trim_mask(df, "売上高", group_cols=["年度", "日経業種中分類名"], limits=[0, 0.01])

# すべての条件を満たす行のみを抽出 (Trim)
df_trimmed = df[mask_roa & mask_sales]

```

---

### レシピ 2: Winsorizing (値を畳み込む)

**概要:**
上下 1% を超える値を、それぞれの境界値（1%点・99%点）に置き換えます。データ数は減りません。

**R (tidyverse)**

Python の `scipy.stats.mstats.winsorize` と同じ挙動（端から % で指定）にするためのヘルパー関数を定義して使います。

```r
# ヘルパー関数: Python (scipy) 互換の Winsorize
winsorize_scipy <- function(x, limits = c(0.01, 0.01), na.rm = TRUE) {
    lower_prob <- limits[1]
    upper_prob <- 1 - limits[2]
    qs <- quantile(x, probs = c(lower_prob, upper_prob), na.rm = na.rm, type = 7)
    pmin(pmax(x, qs[1]), qs[2])
}

# 実行例
df_winsorized <- df %>%
    group_by(年度, 日経業種中分類名) %>%
    mutate(
        # 上下 1% を畳み込み
        ROA = winsorize_scipy(ROA, limits = c(0.01, 0.01))
    ) %>%
    ungroup()

```

**Python (pandas + scipy)**

```python
from scipy.stats.mstats import winsorize

# transform でグループごとに適用する
df["ROA_win"] = (
    df
    .groupby(["年度", "日経業種中分類名"])["ROA"]
    .transform(lambda x: winsorize(x, limits=[0.01, 0.01]))
)

```
