app.run(host="127.0.0.1", port=8000, debug=False)
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=False)from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("CONNECT_SECRET_KEY")

if not app.secret_key:
    app.secret_key = os.urandom(32)

DB = os.path.join(os.path.dirname(__file__), "users.db")

def connect_db():
    return sqlite3.connect(DB)

with connect_db() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Connect Social</title>
<style>
body {
    margin: 0;
    background: #f0f2f5;
    font-family: Arial, sans-serif;
    color: #222;
}
header {
    background: #1877f2;
    color: white;
    text-align: center;
    padding: 20px;
    font-size: 28px;
    font-weight: bold;
}
.card {
    background: white;
    max-width: 380px;
    margin: 40px auto;
    padding: 24px;
    border-radius: 14px;
    box-shadow: 0 3px 12px #0002;
}
input {
    width: 100%;
    box-sizing: border-box;
    padding: 13px;
    margin: 9px 0;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 16px;
}
button, .button {
    display: inline-block;
    box-sizing: border-box;
    width: 100%;
    padding: 13px;
    margin-top: 10px;
    border: none;
    border-radius: 8px;
    background: #1877f2;
    color: white;
    text-align: center;
    text-decoration: none;
    font-size: 16px;
    cursor: pointer;
}
.secondary {
    background: #e7f0ff;
    color: #1877f2;
}
.error {
    background: #ffe5e5;
    color: #a00;
    padding: 10px;
    border-radius: 8px;
}
p { line-height: 1.5; }
</style>
</head>
<body>
<header>🌐 Connect</header>
<div class="card">
{% if user %}
    <h2>Welcome, {{ user }}! 👋</h2>
    <p>You are logged in to Connect.</p>
    <p>Your account is saved on this phone.</p>
    <a class="button" href="/logout">Log out</a>
{% else %}
    <h2>{{ title }}</h2>
    <p>{{ description }}</p>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="POST">
        <input name="username" placeholder="Username"
               minlength="3" maxlength="24"
               pattern="[A-Za-z0-9_]+"
               title="Use letters, numbers and underscores"
               required>
        <input name="password" type="password"
               placeholder="Password" minlength="8" required>
        <button type="submit">{{ button }}</button>
    </form>
    {% if mode == 'login' %}
        <a class="button secondary" href="/register">Create an account</a>
    {% else %}
        <a class="button secondary" href="/login">Already registered? Log in</a>
    {% endif %}
{% endif %}
</div>
</body>
</html>
"""

def show_page(title, description, button, mode, error=None):
    return render_template_string(
        PAGE, title=title, description=description,
        button=button, mode=mode, error=error,
        user=session.get("username")
    )

@app.route("/")
def home():
    if session.get("username"):
        return show_page("", "", "", "", None)
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not (3 <= len(username) <= 24):
            error = "Username must be 3–24 characters."
        elif not all(c.isalnum() or c == "_" for c in username):
            error = "Use only letters, numbers and underscores."
        elif len(password) < 8:
            error = "Password must contain at least 8 characters."
        else:
            try:
                with connect_db() as db:
                    db.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username, generate_password_hash(password))
                    )
                session.clear()
                session["username"] = username
                return redirect("/")
            except sqlite3.IntegrityError:
                error = "That username is already taken."

    return show_page(
        "Create your account",
        "Join Connect and start your journey.",
        "Register", "register", error
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with connect_db() as db:
            row = db.execute(
                "SELECT password_hash FROM users WHERE username = ?",
                (username,)
            ).fetchone()

        if row and check_password_hash(row[0], password):
            session.clear()
            session["username"] = username
            return redirect("/")
        error = "Incorrect username or password."

    return show_page(
        "Welcome back",
        "Log in to your Connect account.",
        "Log in", "login", error
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)
