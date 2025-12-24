from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta

app = Flask(__name__)
app.secret_key = "secret_key"

# ===== DB設定 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ===== DB初期化 =====
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

# ===== ポイント計算 =====
def calc_points(minutes):
    hours = minutes // 60
    if hours >= 10:
        return 0
    else:
        return 10 - hours

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

        if user and check_password_hash(user["password"], pw):
            session["user_id"] = user["id"]
            return redirect("/dashboard")
        else:
            error = "ユーザー名またはパスワードが違います"

    return render_template("login.html", error=error)

# ===== 新規登録（自動ログイン） =====
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        name = request.form["username"]
        pw_hash = generate_password_hash(request.form["password"])

        try:
            db = get_db()
            cursor = db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (name, pw_hash)
            )
            db.commit()

            session["user_id"] = cursor.lastrowid
            return redirect("/dashboard")

        except sqlite3.IntegrityError:
            error = "その名前はすでに使われています"

    return render_template("register.html", error=error)

# ===== ダッシュボード =====
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]
    db = get_db()

    # ユーザー名取得
    user = db.execute(
        "SELECT username FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    username = user["username"]

    if request.method == "POST":
        input_date = request.form["date"]
        hours = int(request.form.get("hours", 0))
        minutes = int(request.form.get("minutes", 0))
        total_minutes = hours * 60 + minutes

        existing = db.execute(
            "SELECT id FROM records WHERE user_id = ? AND date = ?",
            (user_id, input_date)
        ).fetchone()

        if existing:
            db.execute(
                "UPDATE records SET minutes = ? WHERE id = ?",
                (total_minutes, existing["id"])
            )
        else:
            db.execute(
                "INSERT INTO records (user_id, date, minutes) VALUES (?, ?, ?)",
                (user_id, input_date, total_minutes)
            )
        db.commit()

    raw_records = db.execute(
        "SELECT date, minutes FROM records WHERE user_id = ? ORDER BY date DESC",
        (user_id,)
    ).fetchall()

    records = []
    total_points = 0

    for r in raw_records:
        points = calc_points(r["minutes"])
        total_points += points
        records.append({
            "date": r["date"],
            "minutes": r["minutes"],
            "points": points
        })

    yesterday = (date.today() - timedelta(days=1)).isoformat()

    return render_template(
        "dashboard.html",
        username=username,
        total_points=total_points,
        records=records,
        default_date=yesterday
    )

# ===== ログアウト =====
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/favicon.ico")
def favicon():
    return "", 204

if __name__ == "__main__":
    app.run(debug=True)
