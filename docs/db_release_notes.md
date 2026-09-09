# standard.db リリースノート

`standard.db` は年に 1 回程度、最新の FQ (NEEDS-FinancialQUEST) データから再構築されて配布されます。このファイルには、各再構築時点でのスキーマ変更・既知の問題・対応内容を記録します。

**具体的な収録件数・収録期間はここには記載しません。** 配布されたDB内の `Meta` テーブル（または `FqLoader` 接続時の自動サマリ表示・`loader.info()`）を参照してください。詳細は [`standard_schema.md`](standard_schema.md#5-metaビルド情報) を参照。

---

## 2026-09 (fq2026)

* 決算期（`ACC`/`DATEM`）の書式が FQ 側の仕様変更（またはデータ取得時オプションの違い）により、これまでの `YYYYMM` の無クォート整数（例: `198410`）から `"YYYY/MM"` 形式のテキスト（例: `"1984/10"`）に変わった。
  * これに伴い、決算期をYYYYMM整数として演算する自作関数（`shift_term`・`adj.YEAR`）を経由する処理が、`as.numeric("1984/10")` が `NA` になることで動作しなくなった。
  * 対応: 共有関数（`shift_term.R`・`adjYEAR_ver02.R`）は変更せず、`standard.R` 側でDBから決算期を取得するSQL（BS/PL/CF/その他/株価の5箇所）に `CAST(REPLACE(ACC, '/', '') AS INTEGER)` を追加し、取得時点でYYYYMM整数に統一した。
* `Meta` テーブルを新規追加（このバージョンから収録。これより前のDBには存在しない）。取得時点・収録期間・件数を DB 自身に持たせることが目的。
* `FqLoader` が接続時に `Meta` の内容を自動で1行サマリ表示するようになった（`fq_loader.py`）。全項目を見るには `loader.info()`。
