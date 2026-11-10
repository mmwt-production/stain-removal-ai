"""記録の保存先。

- 環境変数 SHEETS_WEBHOOK_URL があれば Google スプレッドシート(Apps Script経由)に保存
  (Streamlit Cloud では secrets に書いた値が環境変数になる)
- なければ、これまで通りローカルの SQLite(feedback.db)に保存
"""
import os
import sqlite3
import time
import uuid
from datetime import datetime

DB_PATH = "feedback.db"

# 直近の保存エラー(画面で警告を出すために使う)。成功すると None に戻る
last_error = None

_CACHE_SECONDS = 60
_cache = {"time": 0.0, "rows": []}


# ---------------------------------------------------------------- 共通
def _remote():
    url = os.environ.get("SHEETS_WEBHOOK_URL")
    if not url:
        return None
    return url, os.environ.get("SHEETS_TOKEN", "")


def using_sheets():
    return _remote() is not None


def _post(payload, timeout=25):
    import requests

    url, token = _remote()
    r = requests.post(url, json={**payload, "token": token}, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data


def init_db():
    if using_sheets():
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            image_path TEXT,
            detected_color TEXT,
            spread_answer TEXT,
            texture_answer TEXT,
            predicted_stain TEXT,
            is_correct INTEGER,
            actual_stain TEXT,
            actual_chemical TEXT,
            feedback_at TEXT
        )
    """)
    # 既存DBへの追加列(におい)。すでにあれば何もしない
    cols = [r[1] for r in c.execute("PRAGMA table_info(records)").fetchall()]
    if "smell_answer" not in cols:
        c.execute("ALTER TABLE records ADD COLUMN smell_answer TEXT")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------- 保存
def save_record(image_path, detected_color, spread_answer, texture_answer,
                predicted_stain, smell_answer=None):
    global last_error
    if using_sheets():
        record_id = "r-" + uuid.uuid4().hex[:12]  # 数値に誤変換されないよう接頭辞つき
        row = {
            "id": record_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "detected_color": detected_color,
            "spread_answer": spread_answer,
            "texture_answer": texture_answer,
            "smell_answer": smell_answer,
            "predicted_stain": predicted_stain,
        }
        try:
            _post({"action": "append", "row": row})
            last_error = None
        except Exception as e:  # 通信失敗でもアプリは止めない
            last_error = f"スプレッドシートへの保存に失敗しました: {e}"
        return record_id

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO records (created_at, image_path, detected_color, spread_answer, texture_answer, predicted_stain, smell_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), image_path, detected_color, spread_answer, texture_answer, predicted_stain, smell_answer))
    conn.commit()
    record_id = c.lastrowid
    conn.close()
    return record_id


def save_feedback(record_id, is_correct, actual_stain, actual_chemical):
    global last_error
    if using_sheets():
        fields = {
            "is_correct": 1 if is_correct else 0,
            "actual_stain": actual_stain,
            "actual_chemical": actual_chemical,
            "feedback_at": datetime.now().isoformat(timespec="seconds"),
        }
        try:
            _post({"action": "update", "id": record_id, "fields": fields})
            _cache["time"] = 0.0  # 次回は最新を読み直す
            last_error = None
        except Exception as e:
            last_error = f"スプレッドシートへの保存に失敗しました: {e}"
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE records
        SET is_correct = ?, actual_stain = ?, actual_chemical = ?, feedback_at = ?
        WHERE id = ?
    """, (1 if is_correct else 0, actual_stain, actual_chemical, datetime.now().isoformat(), record_id))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------- 読み出し
def get_feedback_rows():
    """フィードバック済みの記録を辞書のリストで返す"""
    global last_error
    if using_sheets():
        if time.time() - _cache["time"] < _CACHE_SECONDS:
            return _cache["rows"]
        try:
            rows = _post({"action": "list"}).get("rows", [])
            _cache.update(time=time.time(), rows=rows)
            return rows
        except Exception as e:
            last_error = f"スプレッドシートの読み込みに失敗しました(学習は今回使えません): {e}"
            return _cache["rows"]

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM records WHERE feedback_at IS NOT NULL").fetchall()
    conn.close()
    return [dict(r) for r in rows]
