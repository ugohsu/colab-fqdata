import sqlite3
import pandas as pd
import re
import os
import logging
from typing import Union, Iterable, Any

# --- 警告抑制を追加 ---
logging.getLogger('google_auth_httplib2').setLevel(logging.ERROR)

# Google Colab専用のライブラリ（認証・Drive操作用）
try:
    from google.colab import auth
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    IN_COLAB = True
except ImportError:
    IN_COLAB = False

class FqLoader:
    def __init__(self, db_source, force_download=False):
        """
        Args:
            db_source (str): Google Driveの共有URL、またはローカルのファイルパス
            force_download (bool): すでにファイルがあっても再ダウンロードするか
        """
        self.conn = None
        self.db_path = self._resolve_db_path(db_source, force_download)
        
        # 読み取り専用で接続
        self.conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)

    def _resolve_db_path(self, db_source, force_download):
        """URLならダウンロードし、ローカルパスならそのまま返す"""
        
        # 1. URLからファイルIDを抽出（ご提示のロジック）
        file_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', db_source)
        
        # URLではない（ローカルパス）場合
        if not file_id_match:
            if not os.path.exists(db_source):
                raise FileNotFoundError(f"指定されたファイルが見つかりません: {db_source}")
            return db_source

        # --- 以下、URLの場合のダウンロード処理 ---
        file_id = file_id_match.group(1)
        output_name = "standard_cache.db" # 一時保存名
        
        # キャッシュがあり、強制DLでないならそれを返す
        if os.path.exists(output_name) and not force_download:
            print(f"キャッシュされたDBファイルを使用します: {output_name}")
            return output_name

        # ダウンロード実行
        print(f"Google Driveからダウンロードを開始します... (ID: {file_id})")
        
        if IN_COLAB:
            self._download_securely(file_id, output_name)
        else:
            # ローカル環境等の場合はgdown（ただし公開設定が必要な場合が多い）
            # 今回の要件（権限管理）ではColab利用前提とします
            import gdown
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, output_name, quiet=False)
            
        print(f"準備完了: {output_name}")
        return output_name

    def _download_securely(self, file_id, output_path):
        """
        【重要】Colabの認証を使って、権限のあるユーザーのみダウンロードする
        """
        # 1. ユーザー認証（初回のみポップアップが出ます）
        auth.authenticate_user()
        
        # 2. Drive APIクライアント構築
        drive_service = build('drive', 'v3')
        
        # 3. ダウンロードリクエスト
        request = drive_service.files().get_media(fileId=file_id)
        
        # 4. 書き込み実行
        with open(output_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                # print(f"Download {int(status.progress() * 100)}%.")

    def read_sql(self, sql: str, filter_list: Union[Iterable[Any], None] = None, key_col: str = "証券コード"):
        """
        任意のSQLクエリを実行し、DataFrameを返す。
        filter_list が指定された場合、一時テーブルを作成して key_col で絞り込む。
        
        Args:
            sql (str): 実行したいSELECT文（年度絞り込みなどはここに書く）
            filter_list (list, optional): 絞り込みたい証券コード等のリスト
            key_col (str): 絞り込みに使うカラム名（デフォルト: '証券コード'）
        """
        # クエリの末尾のセミコロンを除去（サブクエリ化でエラーになるため）
        clean_sql = sql.strip().rstrip(';')
        
        if filter_list is None:
            # リストがない場合はそのまま実行
            return pd.read_sql(clean_sql, self.conn)
        
        # --- リスト絞り込みモード ---
        
        # 1. 前処理: 文字列型に統一
        clean_codes = [str(c).strip() for c in filter_list if pd.notna(c)]
        
        if not clean_codes:
            # リストが空の場合は空のDFを返す（あるいはエラーにする）
            return pd.DataFrame()

        try:
            with self.conn:
                # 2. 一時テーブル作成
                self.conn.execute("CREATE TEMP TABLE IF NOT EXISTS _temp_filter_keys (code TEXT PRIMARY KEY)")
                self.conn.execute("DELETE FROM _temp_filter_keys")
                
                # 3. 高速流し込み
                self.conn.executemany(
                    "INSERT OR IGNORE INTO _temp_filter_keys (code) VALUES (?)", 
                    [(c,) for c in clean_codes]
                )
                
                # 4. ユーザーSQLをラップして結合
                #    ユーザーのSQL結果(UserQuery) と 一時テーブル(Filter) を JOIN
                wrapper_query = f"""
                    SELECT UserQuery.*
                    FROM ({clean_sql}) AS UserQuery
                    INNER JOIN _temp_filter_keys AS Filter
                    ON UserQuery.{key_col} = Filter.code
                """
                
                return pd.read_sql(wrapper_query, self.conn)
                
        finally:
            # クリーンアップ（必須ではないがメモリ節約のため）
            self.conn.execute("DROP TABLE IF EXISTS _temp_filter_keys")

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """with構文の開始時に呼ばれる"""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """with構文を抜ける時に呼ばれる（自動close）"""
        self.close()

    def __del__(self):
        """変数が上書き/削除された時に呼ばれる（保険）"""
        try:
            self.close()
        except Exception:
            pass
