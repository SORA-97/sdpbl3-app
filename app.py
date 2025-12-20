from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)
app.secret_key = "secret_key"  # 本番では変更

def get_db():
    return sqlite3.connect("app.db")

# 初回DB作成
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

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["username"]
        pw = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=?", (name,)
        ).fetchone()

        if user and check_password_hash(user[2], pw):
            session["user_id"] = user[0]
            return redirect("/dashboard")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["username"]
        pw = generate_password_hash(request.form["password"])

        try:
            db = get_db()
            db.execute(
                "INSERT INTO users (username, password) VALUES (?,?)",
                (name, pw)
            )
            db.commit()
            return redirect("/")
        except:
            pass

    return render_template("register.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        minutes = request.form["minutes"]
        today = date.today().isoformat()

        db = get_db()
        db.execute(
            "INSERT INTO records (user_id, date, minutes) VALUES (?,?,?)",
            (session["user_id"], today, minutes)
        )
        db.commit()

    db = get_db()
    records = db.execute(
        "SELECT date, minutes FROM records WHERE user_id=? ORDER BY date",
        (session["user_id"],)
    ).fetchall()

    return render_template("dashboard.html", records=records)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
