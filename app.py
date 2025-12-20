from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)
app.secret_key = "secret_key"  # 本番では変更

# ===== DBの場所を固定（超重要）=====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # ← カラム名でアクセスできる
    return conn

# ===== 初回DB作成 =====
with get_db() as conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        minutes INTEGER
    )
    """)
    conn.commit()

# ===== ログイン =====
@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        name = request.form["username"]
        pw = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (name,)
        ).fetchone()

        # デバッグ用（Render Logsで見える）
        print("LOGIN TRY:", name, user)

        if user and check_password_hash(user["password"], pw):
            session["user_id"] = user["id"]
            return redirect("/dashboard")
        else:
            error = "ユーザー名またはパスワードが違います"

    return render_template("login.html", error=error)

# ===== 新規登録 =====
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        name = request.form["username"]
        pw_hash = generate_password_hash(request.form["password"])

        try:
            db = get_db()
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (name, pw_hash)
            )
            db.commit()
            return redirect("/")
        except sqlite3.IntegrityError:
            error = "その名前はすでに使われています"

    return render_template("register.html", error=error)

# ===== ダッシュボード =====
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    if request.method == "POST":
        minutes = request.form["minutes"]
        today = date.today().isoformat()

        db = get_db()
        db.execute(
            "INSERT INTO records (user_id, date, minutes) VALUES (?, ?, ?)",
            (user_id, today, minutes)
        )
        db.commit()

    db = get_db()
    records = db.execute(
        "SELECT date, minutes FROM records WHERE user_id = ? ORDER BY date",
        (user_id,)
    ).fetchall()

    return render_template("dashboard.html", records=records)

# ===== ログアウト =====
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ===== デバッグ用：ユーザー一覧 =====
@app.route("/debug/users")
def debug_users():
    db = get_db()
    users = db.execute(
        "SELECT id, username FROM users"
    ).fetchall()
    return "<br>".join([f"{u['id']} : {u['username']}" for u in users])

# ===== favicon対策 =====
@app.route("/favicon.ico")
def favicon():
    return "", 204
