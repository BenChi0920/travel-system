from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT,
        birthday TEXT,
        stay TEXT,
        note TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/api/all")
def get_all():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM users ORDER BY name")
    rows = c.fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])

@app.route("/api/<id>")
def get_one(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE id=?", (id,))
    r = c.fetchone()
    conn.close()

    return jsonify(dict(r)) if r else jsonify({})

@app.route("/api/save", methods=["POST"])
def save():
    data = request.get_json()

    if not data:
        return "資料錯誤", 400

    id = data.get("id", "").strip()
    name = data.get("name", "").strip()
    birthday = data.get("birthday", "").strip()
    stay = data.get("stay", "")
    note = data.get("note", "")

    # 🔥 台胞證驗證
    if not id.isdigit() or len(id) not in [8,10]:
        return "台胞證格式錯誤", 400

    if not name or not birthday:
        return "姓名 / 生日必填", 400

    # 🔥 日期統一（只允許 YYYY-MM-DD）
    try:
        birthday = datetime.strptime(birthday, "%Y-%m-%d").strftime("%Y-%m-%d")
    except:
        return "生日格式錯誤（需 YYYY-MM-DD）", 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE id=?", (id,))
    r = c.fetchone()

    if r:
        if r[2] != birthday:
            conn.close()
            return "驗證失敗：生日不正確", 400

        c.execute("""
        UPDATE users
        SET name=?, birthday=?, stay=?, note=?
        WHERE id=?
        """, (name, birthday, stay, note, id))
    else:
        c.execute("""
        INSERT INTO users VALUES (?, ?, ?, ?, ?)
        """, (id, name, birthday, stay, note))

    conn.commit()
    conn.close()

    return "success"

@app.route("/api/delete/<id>", methods=["DELETE"])
def delete(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return "deleted"

if __name__ == "__main__":
    app.run(debug=True)

